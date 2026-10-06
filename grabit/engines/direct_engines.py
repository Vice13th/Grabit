"""Direct-file-transfer engines: plain HTTP(S)/Dropbox, Google Drive, Mega.nz."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from urllib.parse import unquote, urlparse

import requests

from grabit.core.exceptions import DownloadCancelled
from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.core.retry import retry_on_exception
from grabit.core.proc import no_window_kwargs
from grabit.core.url_utils import sanitize_filename
from grabit.engines import register_engine
from grabit.engines.base import BaseEngine

_CONTENT_TYPE_EXTENSIONS = {
    "video/mp4": ".mp4", "video/webm": ".webm", "video/x-matroska": ".mkv",
    "video/quicktime": ".mov", "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
    "audio/ogg": ".ogg", "audio/wav": ".wav", "image/jpeg": ".jpg",
    "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp",
    "image/svg+xml": ".svg", "application/pdf": ".pdf",
    "application/zip": ".zip", "application/x-rar-compressed": ".rar",
    "application/x-7z-compressed": ".7z", "application/json": ".json",
    "application/xml": ".xml", "text/plain": ".txt", "text/html": ".html",
}
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@register_engine("direct", "dropbox")
class DirectHttpEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        if "dropbox.com" in url:
            if "dl=0" in url:
                url = url.replace("dl=0", "dl=1")
            elif "dl=1" not in url:
                url = url + ("&dl=1" if "?" in url else "?dl=1")

        status_cb("⬇ Connecting to server...", "#9a9a9a")
        progress_cb(0.02)
        try:
            session = requests.Session()
            response = DirectHttpEngine._open(session, url)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            filename = DirectHttpEngine._extract_filename(response.headers.get("Content-Disposition", ""))
            if not filename:
                filename = DirectHttpEngine._filename_from_url(response.url)
            if not filename or "." not in filename:
                ext = _CONTENT_TYPE_EXTENSIONS.get(content_type.lower().split(";")[0].strip(), "")
                if ext and not (filename or "").endswith(ext):
                    filename = (filename or "downloaded_file") + ext

            filepath = os.path.join(save_dir, sanitize_filename(filename))
            base, dot_ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(filepath):
                filepath = f"{base}_{counter}{dot_ext}"
                counter += 1

            total = int(response.headers.get("Content-Length", 0) or 0)
            downloaded = 0
            last_report = 0.0
            last_report_at = time.monotonic()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    options.checkpoint()
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.monotonic()
                    if total:
                        pct = downloaded / total
                        if pct - last_report >= 0.02 or now - last_report_at >= 0.25:
                            last_report = pct
                            last_report_at = now
                            progress_cb(min(pct, 0.99))
                            mb_done, mb_total = downloaded / 1024 / 1024, total / 1024 / 1024
                            status_cb(f"⬇ Downloading... {pct * 100:.0f}%  ({mb_done:.1f}/{mb_total:.1f} MB)", "#9a9a9a")
                    elif now - last_report_at >= 0.5:
                        last_report_at = now
                        status_cb(f"⬇ Downloading... {downloaded / 1024 / 1024:.1f} MB", "#9a9a9a")
            progress_cb(1.0)
            return DownloadResult.ok(f"Saved: {os.path.basename(filepath)}")
        except DownloadCancelled:
            raise
        except Exception as e:
            return DownloadResult.fail(str(e)[:180])

    @staticmethod
    @retry_on_exception((requests.exceptions.RequestException,), attempts=3, base_delay=1.5)
    def _open(session: requests.Session, url: str) -> requests.Response:
        """Establish the streaming connection, retrying transient network
        errors (DNS hiccups, connection resets) before the caller commits to
        writing a file. Mid-stream interruptions are not retried here, since
        resuming a partial write isn't implemented — a retry there would
        silently overwrite/duplicate bytes rather than correctly resume."""
        return session.get(url, stream=True, timeout=(15, 60), allow_redirects=True,
                            headers={"User-Agent": _USER_AGENT})

    @staticmethod
    def _extract_filename(content_disposition: str):
        if not content_disposition:
            return None
        if "filename*=" in content_disposition:
            try:
                part = content_disposition.split("filename*=", 1)[1].split(";", 1)[0].strip()
                if "''" in part:
                    part = part.split("''", 1)[1]
                return unquote(part).strip().strip('"').strip("'")
            except (IndexError, ValueError):
                pass
        if "filename=" in content_disposition:
            try:
                part = content_disposition.split("filename=", 1)[1].split(";", 1)[0].strip()
                return part.strip().strip('"').strip("'")
            except IndexError:
                pass
        return None

    @staticmethod
    def _filename_from_url(url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        name = unquote(path.split("/")[-1])
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        return name or "downloaded_file"


@register_engine("gdrive")
class GDriveEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        import gdown

        status_cb("⬇ Connecting to Google Drive...", "#9a9a9a")
        progress_cb(0.15)
        is_folder = "/folders/" in url or "drive/folders" in url
        if is_folder:
            status_cb("📁 Downloading folder...", "#9a9a9a")
            gdown.download_folder(url=url, output=save_dir, quiet=True, use_cookies=False)
            progress_cb(1.0)
            return DownloadResult.ok(f"Folder downloaded to: {save_dir}")

        status_cb("📄 Downloading file...", "#9a9a9a")
        output_path = gdown.download(url=url, output=os.path.join(save_dir, ""), quiet=True)
        progress_cb(1.0)
        if output_path:
            return DownloadResult.ok(f"Saved: {os.path.basename(output_path)}")
        return DownloadResult.fail("Download failed")


@register_engine("mega")
class MegaEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        if not shutil.which("megadl"):
            return DownloadResult.fail("megadl not found. Install megatools.")
        status_cb("⬇ Downloading from Mega.nz...", "#9a9a9a")
        progress_cb(0.2)
        result = subprocess.run(["megadl", "--path", save_dir, url],
                                 capture_output=True, text=True, timeout=3600, **no_window_kwargs())
        if result.returncode == 0:
            progress_cb(1.0)
            return DownloadResult.ok(f"Mega download complete in: {save_dir}")
        return DownloadResult.fail((result.stderr or "")[:150])
