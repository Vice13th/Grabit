"""Browser-based resolver for JS-heavy pages when yt-dlp's extractor fails.

Not registered in the engine registry / not directly reachable from
``SmartRouter`` — it's a secondary resolver that :class:`YtDlpEngine` reaches
for only when its own extraction raises and Playwright is installed, exactly
as in the original script.
"""
from __future__ import annotations

import os

from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.core.url_utils import sanitize_filename


class PlaywrightFallback:
    @staticmethod
    def resolve(
        url: str,
        save_dir: str,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return DownloadResult.fail("Playwright not installed")

        captured = {"download": None, "media": None}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(accept_downloads=True)

                def on_download(download):
                    captured["download"] = download

                def on_response(response):
                    if captured["media"]:
                        return
                    ctype = (response.headers.get("content-type") or "").lower()
                    if ctype.startswith(("video/", "audio/", "image/", "application/octet-stream")):
                        captured["media"] = response.url

                page.on("download", on_download)
                page.on("response", on_response)
                status_cb("🌐 Resolving through browser engine...", "#9a9a9a")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                if captured["download"] is not None:
                    download = captured["download"]
                    target = os.path.join(save_dir, sanitize_filename(download.suggested_filename, "download"))
                    download.save_as(target)
                    browser.close()
                    progress_cb(1.0)
                    return DownloadResult.ok(f"Saved: {os.path.basename(target)}")

                media_url = captured["media"]
                browser.close()

            if media_url:
                from grabit.engines.direct_engines import DirectHttpEngine
                return DirectHttpEngine.download(media_url, save_dir, DownloadOptions(), progress_cb, status_cb)
            return DownloadResult.fail("Browser could not resolve a downloadable media resource")
        except Exception as e:
            return DownloadResult.fail(str(e)[:180])
