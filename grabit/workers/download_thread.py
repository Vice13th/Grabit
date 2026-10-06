"""The QThread that drives the router + engine registry from the GUI.

Two execution modes:

* Sequential (``max_concurrency == 1``, the default — identical to the
  original script's behavior): one URL at a time, progress mapped onto its
  own ``[base, base+span]`` slice of the overall bar.
* Concurrent (``max_concurrency > 1``, opt-in from the batch tab): several
  URLs download at once via a thread pool; overall progress is the mean of
  each URL's own fraction. Pause/cancel remain cooperative and *shared*
  across every in-flight download, so pausing stops all of them at their
  next checkpoint rather than only the "current" one.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

from grabit.core.exceptions import DownloadCancelled
from grabit.core.models import DownloadOptions, DownloadResult
from grabit.core.router import SmartRouter
from grabit.engines import get_engine

logger = logging.getLogger(__name__)


class DownloadThread(QThread):
    status_changed = Signal(str, str)
    progress_changed = Signal(float)
    info_ready = Signal(str)
    url_started = Signal(str, int, int)
    finished_with_status = Signal(bool)

    def __init__(
        self,
        urls: List[str],
        save_dir: str,
        options: DownloadOptions,
        optional_status: Dict[str, bool],
        parent=None,
        max_concurrency: int = 1,
    ):
        super().__init__(parent)
        self.urls = urls if isinstance(urls, list) else [urls]
        self.save_dir = save_dir
        self.options = options
        self.optional_status = optional_status
        self.max_concurrency = max(1, int(max_concurrency))
        self._control = threading.Condition()
        self._pause_requested = False
        self._cancel_requested = False
        self._last_progress_emit = 0.0
        self._last_progress_emit_time = 0.0
        self._last_status_emit = 0.0
        self._archive_path = os.path.join(
            self.save_dir, f".grabit_session_{os.getpid()}_{id(self)}.archive"
        )

    # -- pause / resume / cancel: cooperative, shared by every worker -----
    def pause(self):
        with self._control:
            if not self._cancel_requested:
                self._pause_requested = True
        self._emit_status("⏸ Download paused", "#FF9800")

    def resume_download(self):
        with self._control:
            self._pause_requested = False
            self._control.notify_all()
        self._emit_status("▶ Resuming download...", "#9a9a9a")

    def cancel(self):
        with self._control:
            self._cancel_requested = True
            self._pause_requested = False
            self._control.notify_all()

    def _control_checkpoint(self):
        with self._control:
            while self._pause_requested and not self._cancel_requested:
                self._control.wait(timeout=0.5)
            if self._cancel_requested:
                raise DownloadCancelled("Download cancelled")

    def _is_cancelled(self) -> bool:
        with self._control:
            return self._cancel_requested

    # -- throttled signal emission -----------------------------------------
    def _emit_progress(self, value: float):
        now = time.monotonic()
        if value >= 0.999 or value - self._last_progress_emit >= 0.01 or now - self._last_progress_emit_time >= 0.10:
            self._last_progress_emit = value
            self._last_progress_emit_time = now
            self.progress_changed.emit(float(value))

    def _emit_status(self, text: str, color: str):
        now = time.monotonic()
        if now - self._last_status_emit >= 0.12 or text.startswith(("✓", "✗", "⚠", "⏸", "▶")):
            self._last_status_emit = now
            self.status_changed.emit(text, color)

    def _progress_callback(self, index: int, total: int):
        """A progress_cb confining ``index``'s updates to its own slice of
        the overall bar — used only in sequential mode, where exactly one
        URL is active at a time."""
        base = (index - 1) / total
        span = 1.0 / total

        def callback(value: float):
            self._control_checkpoint()
            self._emit_progress(base + max(0.0, min(1.0, value)) * span)

        return callback

    @staticmethod
    def _prefix(idx: int, total: int) -> str:
        return f"[{idx}/{total}] " if total > 1 else ""

    def _status_callback(self, prefix: str):
        def callback(text: str, color: str):
            self._control_checkpoint()
            self._emit_status(f"{prefix}{text}", color)

        return callback

    # -- single-URL unit of work, shared by both execution modes -----------
    def _download_one(self, url: str, idx: int, total: int, progress_cb) -> Optional[bool]:
        """Return True (success), False (failure), or None (stop — cancelled)."""
        self._control_checkpoint()
        self.url_started.emit(url, idx, total)
        prefix = self._prefix(idx, total)
        status_cb = self._status_callback(prefix)

        decision = SmartRouter.route(url, self.optional_status)
        if not decision.is_known:
            self._emit_status(f"⚠ {prefix}Unknown platform: {url[:50]}", "#FF9800")
            return False
        engine = get_engine(decision.engine)
        if engine is None:
            self._emit_status(f"✗ {prefix}Engine unavailable: {decision.engine}", "#F44336")
            return False
        self._emit_status(f"{prefix}🔀 {decision.engine}", "#9a9a9a")

        try:
            result: DownloadResult = engine.download(
                url=url, save_dir=self.save_dir, options=self.options,
                progress_cb=progress_cb, status_cb=status_cb,
            )
        except DownloadCancelled:
            self._emit_status(f"✗ {prefix}Download cancelled", "#FF9800")
            return None
        except Exception as exc:
            if self._is_cancelled():
                self._emit_status(f"✗ {prefix}Download cancelled", "#FF9800")
                return None
            logger.exception("Engine %s failed on %s", decision.engine, url)
            self._emit_status(f"✗ {prefix}Error: {str(exc)[:100]}", "#F44336")
            return False

        if result.cancelled or self._is_cancelled():
            self._emit_status(f"✗ {prefix}Download cancelled", "#FF9800")
            return None
        if result.success:
            self._emit_status(f"{prefix}✓ {result.message or 'Done!'}", "#4CAF50")
            return True
        self._emit_status(f"{prefix}✗ {result.message or 'Failed'}", "#F44336")
        return False

    # -- execution modes -----------------------------------------------------
    def _run_sequential(self, total: int) -> Tuple[int, int, bool]:
        success = fail = 0
        for idx, url in enumerate(self.urls, start=1):
            outcome = self._download_one(url, idx, total, self._progress_callback(idx, total))
            if outcome is None:
                return success, fail, True
            success += int(bool(outcome))
            fail += int(outcome is False)
        return success, fail, False

    def _run_concurrent(self, total: int) -> Tuple[int, int, bool]:
        success = fail = 0
        progress_map: Dict[int, float] = {i: 0.0 for i in range(1, total + 1)}
        lock = threading.Lock()

        def make_progress_cb(idx: int):
            def cb(value: float):
                self._control_checkpoint()
                with lock:
                    progress_map[idx] = max(0.0, min(1.0, value))
                    overall = sum(progress_map.values()) / total
                self._emit_progress(overall)
            return cb

        cancelled = False
        with ThreadPoolExecutor(max_workers=self.max_concurrency) as pool:
            futures = {
                pool.submit(self._download_one, url, idx, total, make_progress_cb(idx)): idx
                for idx, url in enumerate(self.urls, start=1)
            }
            for future in as_completed(futures):
                outcome = future.result()
                if outcome is None:
                    cancelled = True
                elif outcome:
                    success += 1
                else:
                    fail += 1
        return success, fail, cancelled

    def run(self):
        total = len(self.urls)
        self._last_progress_emit_time = time.monotonic()
        self.options.download_archive = self._archive_path
        self.options.control_checkpoint = self._control_checkpoint
        self.options.cancel_requested = self._is_cancelled
        self.options.extra["optional_status"] = self.optional_status

        try:
            if self.max_concurrency > 1 and total > 1:
                success_count, fail_count, cancelled = self._run_concurrent(total)
            else:
                success_count, fail_count, cancelled = self._run_sequential(total)
        finally:
            try:
                if os.path.exists(self._archive_path):
                    os.remove(self._archive_path)
            except OSError:
                pass

        if cancelled:
            self.status_changed.emit("✗ Download cancelled", "#FF9800")
            self.finished_with_status.emit(success_count > 0)
            return

        self.progress_changed.emit(1.0)
        if total > 1:
            summary = f"✓ Batch complete: {success_count} success, {fail_count} failed (of {total})"
            color = "#4CAF50" if fail_count == 0 else "#FF9800"
        else:
            summary = "✓ Done!" if success_count == 1 else "✗ Download failed"
            color = "#4CAF50" if success_count == 1 else "#F44336"
        self.status_changed.emit(summary, color)
        self.info_ready.emit(summary)
        self.finished_with_status.emit(success_count > 0)
