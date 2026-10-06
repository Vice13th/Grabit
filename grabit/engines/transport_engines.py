"""Engines that shell out to an external CLI tool rather than a Python library."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse

from grabit.core.proc import no_window_kwargs
from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.engines import register_engine
from grabit.engines.base import BaseEngine


@register_engine("aria2")
class Aria2Engine(BaseEngine):
    """High-performance multi-protocol engine backed by aria2c."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        exe = shutil.which("aria2c")
        if not exe:
            return DownloadResult.fail("aria2c not installed")
        status_cb("⚡ Starting accelerated download...", "#9a9a9a")
        progress_cb(0.05)
        cmd = [exe, "--dir", save_dir, "--allow-overwrite=false",
               "--auto-file-renaming=true", "--summary-interval=1",
               "--console-log-level=warn", "--file-allocation=none", url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200, check=False, **no_window_kwargs())
            if result.returncode == 0:
                progress_cb(1.0)
                return DownloadResult.ok("Accelerated download complete")
            return DownloadResult.fail((result.stderr or result.stdout or "aria2 download failed")[-220:])
        except Exception as e:
            return DownloadResult.fail(str(e)[:180])


@register_engine("streamlink")
class StreamlinkEngine(BaseEngine):
    """Live/VOD stream capture using Streamlink + FFmpeg."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        optional_status = options.get("optional_status", {}) or {}
        exe = shutil.which("streamlink")
        cmd_prefix = [exe] if exe else (
            [sys.executable, "-m", "streamlink"] if optional_status.get("streamlink", False) else None
        )
        if not cmd_prefix:
            return DownloadResult.fail("Streamlink not installed")
        host = urlparse(url).netloc.replace(".", "_") or "stream"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output = os.path.join(save_dir, f"{host}_{timestamp}.ts")
        status_cb("◉ Capturing stream...", "#9a9a9a")
        progress_cb(0.05)
        cmd = cmd_prefix + ["--stdout", url, "best"]
        try:
            with open(output, "wb") as f:
                proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE, **no_window_kwargs())
                while proc.poll() is None:
                    options.checkpoint()
                    time.sleep(0.25)
                    if os.path.exists(output):
                        size = os.path.getsize(output)
                        status_cb(f"◉ Recording... {size / 1024 / 1024:.1f} MB", "#9a9a9a")
                stderr = proc.stderr.read() if proc.stderr else b""
                rc = proc.returncode
            if rc == 0 and os.path.exists(output) and os.path.getsize(output) > 0:
                progress_cb(1.0)
                return DownloadResult.ok(f"Saved: {os.path.basename(output)}")
            return DownloadResult.fail((stderr.decode(errors="ignore") or "Stream capture failed")[-220:])
        except Exception as e:
            return DownloadResult.fail(str(e)[:180])


@register_engine("rclone")
class RcloneEngine(BaseEngine):
    """Optional cloud-remote downloader using an existing rclone remote."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        exe = shutil.which("rclone")
        if not exe:
            return DownloadResult.fail("rclone not installed")
        remote = url[len("rclone://"):].strip()
        if not remote or ":" not in remote:
            return DownloadResult.fail("Use rclone://remote/path syntax")
        status_cb("☁ Downloading from configured cloud remote...", "#9a9a9a")
        progress_cb(0.05)
        cmd = [exe, "copy", remote, save_dir, "--transfers", "4", "--checkers", "8", "--stats", "0"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200, check=False, **no_window_kwargs())
            if result.returncode == 0:
                progress_cb(1.0)
                return DownloadResult.ok("Cloud remote download complete")
            return DownloadResult.fail((result.stderr or result.stdout or "rclone failed")[-220:])
        except Exception as e:
            return DownloadResult.fail(str(e)[:180])
