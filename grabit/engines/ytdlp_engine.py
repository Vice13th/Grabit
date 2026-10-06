"""yt-dlp backed engine — the workhorse for YouTube and ~1000 other sites."""
from __future__ import annotations

import os

from grabit.core.block_detect import looks_like_block
from grabit.core.exceptions import DownloadCancelled
from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.engines import register_engine
from grabit.engines.base import BaseEngine

# yt-dlp has no literal "mirror" concept (there's no second youtube.com to
# fall back to) — but it DOES let you request a different internal API
# "client" (the same site, accessed the way a different YouTube app would),
# and switching client is yt-dlp's own documented way to route around a
# block/rate-limit tied to one client's fingerprint. This is the real
# equivalent for this engine: same idea as a PyPI mirror (try another path
# to the same content when the default one is blocked), different
# mechanism because the target is a single site, not a package index.
_CLIENT_FALLBACK_LADDER = ["android", "ios", "tv"]


@register_engine("yt-dlp")
class YtDlpEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        import yt_dlp

        last_pct = {"value": 0.0}

        def progress_hook(d):
            options.checkpoint()
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    pct = downloaded / total
                    progress_cb(min(pct, 0.99))
                    if pct - last_pct["value"] >= 0.05:
                        last_pct["value"] = pct
                        speed = d.get("speed") or 0
                        speed_txt = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "..."
                        status_cb(f"⬇ Downloading... {pct * 100:.0f}%  ({speed_txt})", "#9a9a9a")
            elif d.get("status") == "finished":
                progress_cb(0.99)
                mode = options.output_mode
                status_cb(
                    "🔧 Converting to audio..." if mode == "audio" else "🔧 Merging audio/video...",
                    "#9a9a9a",
                )
                options.checkpoint()

        ydl_opts = YtDlpEngine._build_opts(save_dir, options, progress_hook)
        try:
            info = YtDlpEngine._extract_with_client_fallback(yt_dlp, url, ydl_opts, status_cb)
        except DownloadCancelled:
            raise
        except Exception as exc:
            if options.is_cancelled():
                return DownloadResult.cancelled_result()
            optional_status = options.get("optional_status", {}) or {}
            if optional_status.get("playwright", False):
                from grabit.engines.playwright_fallback import PlaywrightFallback
                fallback = PlaywrightFallback.resolve(url, save_dir, progress_cb, status_cb)
                if fallback.success:
                    return fallback
            raise exc

        progress_cb(1.0)
        if not info:
            return DownloadResult.fail("No media found")
        entries = info.get("entries")
        if entries:
            count = sum(1 for _ in entries)
            title = info.get("title", "Playlist")
            return DownloadResult.ok(f"Downloaded {count} item(s): {title[:50]}", count=count)
        title = info.get("title", "media")
        ext = info.get("ext", "")
        if options.output_mode == "audio":
            ext = options.audio_format
        return DownloadResult.ok(f"Saved: {title[:60]}.{ext}", title=title)

    @staticmethod
    def _extract_with_client_fallback(yt_dlp, url: str, ydl_opts: dict, status_cb: StatusCallback):
        """Try the default client first; if the failure looks like a
        block/rate-limit (see grabit.core.block_detect), retry with each
        client in _CLIENT_FALLBACK_LADDER before giving up — the
        yt-dlp-side equivalent of a mirror fallback (see module docstring
        note above _CLIENT_FALLBACK_LADDER)."""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        except DownloadCancelled:
            raise
        except Exception as first_exc:
            if not looks_like_block(str(first_exc)):
                raise
            for client in _CLIENT_FALLBACK_LADDER:
                status_cb(f"⚠ Blocked/rate-limited — retrying via {client} client...", "#FF9800")
                retry_opts = dict(ydl_opts)
                retry_opts["extractor_args"] = {"youtube": {"player_client": [client]}}
                try:
                    with yt_dlp.YoutubeDL(retry_opts) as ydl:
                        return ydl.extract_info(url, download=True)
                except DownloadCancelled:
                    raise
                except Exception:
                    continue
            raise first_exc

    @staticmethod
    def _build_opts(save_dir: str, options: DownloadOptions, progress_hook) -> dict:
        opts = {
            "outtmpl": os.path.join(save_dir, "%(title).150B [%(id)s].%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True, "no_warnings": True, "noprogress": True,
            "ignoreerrors": False, "retries": 3, "fragment_retries": 3,
            "concurrent_fragment_downloads": 16,
            "buffersize": 1024 * 1024,
            "continuedl": True,
        }
        if options.download_archive:
            opts["download_archive"] = options.download_archive
        if options.playlist_mode == "yes":
            opts["noplaylist"] = False
        elif options.playlist_mode == "no":
            opts["noplaylist"] = True

        if options.output_mode == "audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": options.audio_format,
                "preferredquality": options.audio_quality,
            }]
            return opts

        quality = "best" if options.video_quality in (None, "best") else str(options.video_quality)
        if quality == "best":
            selector = "bv*+ba/b"
        else:
            selector = f"bv*[height<={quality}]+ba/b[height<={quality}]/b[height<={quality}]"

        video_format = options.video_format
        if video_format == "mp4":
            opts["format"] = f"{selector}[ext=mp4]/{selector}"
            opts["merge_output_format"] = "mp4"
        elif video_format == "mkv":
            opts["format"] = selector
            opts["merge_output_format"] = "mkv"
        elif video_format == "webm":
            opts["format"] = selector
            opts["merge_output_format"] = "webm"
        else:
            opts["format"] = selector
        return opts
