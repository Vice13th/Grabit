"""The v6.0 engine family: newer, more specialized single-purpose backends.

Grouped together because they were introduced together in the original
script and share a common shape (try to import a small, focused library;
report a clear "not installed" message if it's missing).
"""
from __future__ import annotations

import os
import subprocess
import sys

from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.core.url_utils import sanitize_filename
from grabit.core.proc import no_window_kwargs
from grabit.engines import register_engine
from grabit.engines.base import BaseEngine


@register_engine("bilibili")
class BilibiliEngine(BaseEngine):
    """Bilibili engine using bilix (async, high-concurrency)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from bilix.sites.bilibili import DownloaderBilibili
        except ImportError:
            # bilix depends on danmakuC, which as of this writing ships no
            # Python 3.12 wheel on any platform — pip falls back to
            # building from source, which fails without a Rust/C toolchain
            # (this is exactly the failure users hit on a fresh Python 3.12
            # install). yt-dlp has a native, dependency-free Bilibili
            # extractor, so fall back to it instead of just failing —
            # you lose bilix's danmaku/bullet-comment export, but the video
            # itself still downloads.
            status_cb("⬇ bilix unavailable — using yt-dlp for Bilibili instead...", "#9a9a9a")
            from grabit.engines.ytdlp_engine import YtDlpEngine
            return YtDlpEngine.download(url, save_dir, options, progress_cb, status_cb)
        import asyncio

        status_cb("⬇ Downloading from Bilibili (async)...", "#9a9a9a")
        progress_cb(0.1)

        async def _download():
            async with DownloaderBilibili() as d:
                await d.get_video(url)

        try:
            asyncio.run(_download())
            progress_cb(1.0)
            return DownloadResult.ok(f"Bilibili video downloaded to: {save_dir}")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])


@register_engine("twitch")
class TwitchEngine(BaseEngine):
    """Twitch engine using twitch-archiver (streams, VODs, chat logs)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            import twitch_archiver  # noqa: F401 — presence check; used via CLI below
        except ImportError:
            return DownloadResult.fail("twitch-archiver not installed")
        status_cb("⬇ Downloading from Twitch...", "#9a9a9a")
        progress_cb(0.1)
        # twitch-archiver is primarily a CLI tool; drive it via subprocess.
        result = subprocess.run(
            [sys.executable, "-m", "twitch_archiver", "-u", url, "-o", save_dir],
            capture_output=True, text=True, timeout=3600, **no_window_kwargs(),
        )
        if result.returncode == 0:
            progress_cb(1.0)
            return DownloadResult.ok(f"Twitch content downloaded to: {save_dir}")
        return DownloadResult.fail((result.stderr or "")[:150])


@register_engine("soundcloud")
class SoundCloudEngine(BaseEngine):
    """SoundCloud engine using soundcloud-lib (no API key required)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from sclib import SoundcloudAPI, Track, Playlist
        except ImportError:
            status_cb("⬇ soundcloud-lib unavailable — using yt-dlp for SoundCloud instead...", "#9a9a9a")
            from grabit.engines.ytdlp_engine import YtDlpEngine
            return YtDlpEngine.download(url, save_dir, options, progress_cb, status_cb)
        status_cb("⬇ Downloading from SoundCloud...", "#9a9a9a")
        progress_cb(0.1)
        try:
            api = SoundcloudAPI()
            track = api.resolve(url)
            if isinstance(track, Track):
                filename = os.path.join(save_dir, sanitize_filename(f"{track.artist} - {track.title}.mp3"))
                with open(filename, "wb+") as f:
                    track.write_mp3_to(f)
                progress_cb(1.0)
                return DownloadResult.ok(f"Saved: {track.artist} - {track.title}.mp3")
            if isinstance(track, Playlist):
                count = 0
                for t in track.tracks:
                    options.checkpoint()
                    filename = os.path.join(save_dir, sanitize_filename(f"{t.artist} - {t.title}.mp3"))
                    with open(filename, "wb+") as f:
                        t.write_mp3_to(f)
                    count += 1
                progress_cb(1.0)
                return DownloadResult.ok(f"Downloaded {count} track(s) from playlist")
            return DownloadResult.fail("Unsupported SoundCloud URL")
        except Exception as e:
            # sclib works by scraping SoundCloud's site for a usable
            # client_id and repeatedly breaks (401/403/404) whenever
            # SoundCloud changes their page — a long-standing, recurring
            # upstream fragility (github.com/3jackdaws/soundcloud-lib,
            # issues #1, #2, #29, all the same root cause). yt-dlp ships an
            # actively-maintained native SoundCloud extractor that doesn't
            # depend on that scraping trick, so fall back to it instead of
            # just failing — same pattern as the Bilibili/bilix fallback.
            status_cb(f"⬇ soundcloud-lib failed ({str(e)[:60]}) — trying yt-dlp instead...", "#9a9a9a")
            from grabit.engines.ytdlp_engine import YtDlpEngine
            return YtDlpEngine.download(url, save_dir, options, progress_cb, status_cb)


@register_engine("reddit")
class RedditEngine(BaseEngine):
    """Reddit engine using RedDownloader (auth-less)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from RedDownloader import RedDownloader
        except ImportError:
            return DownloadResult.fail("RedDownloader not installed")
        status_cb("⬇ Downloading from Reddit...", "#9a9a9a")
        progress_cb(0.1)
        try:
            quality = options.video_quality
            if quality in (None, "best"):
                quality = "1080"
            RedDownloader.Download(
                url=url, output="reddit_media", destination=save_dir, quality=int(quality),
            )
            progress_cb(1.0)
            return DownloadResult.ok(f"Reddit media downloaded to: {save_dir}")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])


@register_engine("tiktok")
class TikTokEngine(BaseEngine):
    """TikTok engine using tiktok-downloader-py (watermark-free)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from tiktok_downloader import download_video
        except ImportError:
            return DownloadResult.fail("tiktok-downloader-py not installed")
        status_cb("⬇ Downloading from TikTok (watermark-free)...", "#9a9a9a")
        progress_cb(0.1)
        try:
            output_path = download_video(url, output_dir=save_dir)
            progress_cb(1.0)
            if output_path:
                return DownloadResult.ok(f"Saved: {os.path.basename(output_path)}")
            return DownloadResult.fail("Download failed")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])


@register_engine("instacapture")
class InstagramCaptureEngine(BaseEngine):
    """Alternate Instagram engine using instacapture (stories, posts, reels, IGTV).

    Not currently wired into ``SmartRouter`` — Instagram URLs route to
    :class:`grabit.engines.gallery_engines.InstaloaderEngine` by default.
    Kept registered (rather than silently unreachable, as it was in the
    original script under the name ``InstagramEngine``) so it can be
    selected explicitly or promoted to a fallback later without being
    rewritten from scratch.
    """

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from instacapture import InstaStory, InstaPost
        except ImportError:
            return DownloadResult.fail("instacapture not installed")
        status_cb("⬇ Downloading from Instagram...", "#9a9a9a")
        progress_cb(0.1)
        try:
            if "/stories/" in url:
                story_obj = InstaStory()
                story_obj.username = url.split("/stories/")[-1].split("/")[0]
                story_obj.story_download()
            else:
                post_obj = InstaPost()
                post_obj.reel_id = url
                post_obj.media_download()
            progress_cb(1.0)
            return DownloadResult.ok(f"Instagram content downloaded to: {save_dir}")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])


@register_engine("civitai")
class CivitAIEngine(BaseEngine):
    """CivitAI engine using civitai-downloader (models & images)."""

    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from civitai_downloader import download_file, get_token
        except ImportError:
            return DownloadResult.fail("civitai-downloader not installed")
        status_cb("⬇ Downloading from CivitAI...", "#9a9a9a")
        progress_cb(0.1)
        try:
            token = get_token()
            if not token:
                return DownloadResult.fail("CivitAI API token not configured")
            download_file(url, save_dir, token)
            progress_cb(1.0)
            return DownloadResult.ok(f"CivitAI content downloaded to: {save_dir}")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])
