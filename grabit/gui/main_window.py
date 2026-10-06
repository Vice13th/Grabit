"""Main window: sidebar navigation over stacked pages, still the single
place that owns the shared download thread.

v8 redesign note: this replaces the old ``QTabWidget`` layout with a
sidebar (:class:`~grabit.gui.anim_widgets.Sidebar`) + ``QStackedWidget``,
and adds Downloads/Media Studio/Engines/Logs/Settings pages that didn't
exist before. The thread-ownership architecture described in the original
docstring is unchanged: pages only emit start/pause/resume/cancel signals
and expose ``set_status``/``set_progress``/``set_controls``/
``on_download_finished``; this class is still the only place that touches
``DownloadThread`` directly.
"""
from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from grabit.config import AppConfig
from grabit.core.models import DownloadOptions
from grabit.gui.about_tab import AboutTab
from grabit.gui.batch_tab import BatchDownloadTab
from grabit.gui.downloads_page import DownloadsPage
from grabit.gui.engines_page import EnginesPage
from grabit.gui.grab_page import GrabPage
from grabit.gui.anim_widgets import Sidebar
from grabit.gui.logs_page import LogsPage
from grabit.gui.media_studio_page import MediaStudioPage
from grabit.gui.search_page import SearchPage
from grabit.gui.settings_page import SettingsPage
from grabit.gui.update_dialog import UpdateDialog
from grabit.workers.download_thread import DownloadThread

logger = logging.getLogger(__name__)


class GrabItApp(QMainWindow):
    def __init__(self, config: AppConfig, optional_status: dict):
        super().__init__()
        self.config = config
        self.optional_status = optional_status
        self.setWindowTitle("GrabIt — Universal Media Downloader")
        self.setMinimumSize(1180, 760)
        self.resize(1360, 860)

        self.thread: Optional[DownloadThread] = None
        self._active_tab = None
        self._active_urls: list[str] = []
        self._active_save_dir: str = ""
        self._active_platform: str = ""

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        from grabit import __version__
        self.sidebar = Sidebar(f"v{__version__}  ·  Modular")
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        default_save_dir = str(self.config.default_save_dir)
        self.grab_page = GrabPage(default_save_dir, self.optional_status)
        self.search_page = SearchPage(default_save_dir)
        self.batch_tab = BatchDownloadTab(default_save_dir, self.optional_status, self.config)
        self.downloads_page = DownloadsPage()
        self.studio_page = MediaStudioPage(default_save_dir)
        self.engines_page = EnginesPage(self.optional_status)
        self.settings_page = SettingsPage(self.config)
        self.update_dialog = UpdateDialog(self.config)
        self.logs_page = LogsPage(self.config.data_dir / "logs" / "grabit.log")
        self.about_tab = AboutTab()

        self._pages = {
            "grab": self.grab_page,
            "search": self.search_page,
            "batch": self.batch_tab,
            "downloads": self.downloads_page,
            "studio": self.studio_page,
            "engines": self.engines_page,
            "settings": self.settings_page,
            "updates": self.update_dialog,
            "logs": self.logs_page,
            "about": self.about_tab,
        }
        for key in ("grab", "search", "batch", "downloads", "studio", "engines", "settings", "updates", "logs", "about"):
            self.stack.addWidget(self._pages[key])

        self.sidebar.page_changed.connect(self._on_page_changed)

        # Honor the (previously dead) auto-paste-from-clipboard setting.
        self.grab_page.url_entry.enable_auto_paste(self.config.auto_paste_from_clipboard)

        self.grab_page.start_requested.connect(
            lambda url, save_dir, options: self._start(self.grab_page, [url], save_dir, options, 1)
        )
        self.grab_page.pause_requested.connect(self._on_pause)
        self.grab_page.resume_requested.connect(self._on_resume)
        self.grab_page.cancel_requested.connect(self._on_cancel)

        self.search_page.start_requested.connect(
            lambda url, save_dir, options: self._start(self.search_page, [url], save_dir, options, 1)
        )

        self.batch_tab.start_requested.connect(
            lambda urls, save_dir, options, concurrency: self._start(self.batch_tab, urls, save_dir, options, concurrency)
        )
        self.batch_tab.pause_requested.connect(self._on_pause)
        self.batch_tab.resume_requested.connect(self._on_resume)
        self.batch_tab.cancel_requested.connect(self._on_cancel)

    def _on_page_changed(self, key: str):
        page = self._pages.get(key)
        if page is not None:
            if key == "studio":
                self.studio_page.set_dir(self.grab_page.path_entry.text().strip() or str(self.config.default_save_dir))
            self.stack.setCurrentWidget(page)

    # -- shared thread lifecycle --------------------------------------------
    def _start(self, tab, urls: list, save_dir: str, options: DownloadOptions, max_concurrency: int):
        if self.thread is not None and self.thread.isRunning():
            tab.set_status("⚠ A download is already running in another tab", "#FF9800")
            tab.on_download_finished(False)
            return

        self._active_tab = tab
        self._active_urls = list(urls)
        self._active_save_dir = save_dir
        decision = getattr(self.grab_page, "current_decision", None) if tab is self.grab_page else None
        self._active_platform = decision.platform if decision else (
            "Batch" if tab is self.batch_tab else "Search" if tab is self.search_page else "Unknown"
        )
        self.thread = DownloadThread(
            urls, save_dir, options, self.optional_status,
            parent=self, max_concurrency=max_concurrency,
        )
        self.thread.status_changed.connect(self._forward_status)
        self.thread.progress_changed.connect(self._forward_progress)
        self.thread.finished_with_status.connect(self._on_finished)
        self.thread.finished.connect(self._on_thread_finished)
        self.thread.start()

    def _forward_status(self, text: str, color: str):
        if self._active_tab is not None:
            self._active_tab.set_status(text, color)

    def _forward_progress(self, value: float):
        if self._active_tab is not None:
            self._active_tab.set_progress(value)

    def _on_finished(self, success: bool):
        if self._active_tab is not None:
            self._active_tab.on_download_finished(success)
        self.downloads_page.add_entry(self._active_urls, self._active_platform, self._active_save_dir, success)

    def _on_thread_finished(self):
        if self.thread is not None:
            self.thread.deleteLater()
        self.thread = None

    def _on_pause(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.pause()
            if self._active_tab is not None:
                self._active_tab.set_controls(running=True, paused=True)

    def _on_resume(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.resume_download()
            if self._active_tab is not None:
                self._active_tab.set_controls(running=True, paused=False)

    def _on_cancel(self):
        if self.thread is not None and self.thread.isRunning():
            self.thread.cancel()
            if self._active_tab is not None:
                self._active_tab.set_status("✕ Cancelling download...", "#FF9800")
                self._active_tab.set_controls(running=True, paused=False, cancelling=True)

    def closeEvent(self, event):
        if self.thread is not None and self.thread.isRunning():
            self.thread.cancel()
            self.thread.wait(3000)
        net_thread = getattr(self.grab_page, "_net_check_thread", None)
        if net_thread is not None:
            try:
                if net_thread.isRunning():
                    net_thread.wait(1500)
            except RuntimeError:
                pass  # already deleted via deleteLater() after finishing — nothing to wait for
        self.config.save()
        super().closeEvent(event)
