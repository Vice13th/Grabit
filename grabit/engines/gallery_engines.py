"""Image-gallery engines: gallery-dl (50+ boorus/art sites), Instaloader, Pinterest."""
from __future__ import annotations

import re

import requests

from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback
from grabit.engines import register_engine
from grabit.engines.base import BaseEngine


@register_engine("gallery-dl")
class GalleryDlEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        try:
            from gallery_dl import job as gallery_job
        except ImportError:
            return DownloadResult.fail("gallery-dl not installed")
        status_cb("⬇ Fetching gallery with gallery-dl...", "#9a9a9a")
        progress_cb(0.1)
        config = {
            "base-directory": save_dir,
            "directory": ["{category}", "{title|default=Gallery}"],
            "filename": "{filename}.{extension}",
            "sleep-request": 1.0, "retries": 3, "skip": True,
        }
        try:
            gallery_job.DownloadJob(url, config=config).run()
            progress_cb(1.0)
            return DownloadResult.ok(f"Gallery downloaded to: {save_dir}")
        except Exception as e:
            return DownloadResult.fail(str(e)[:150])


@register_engine("instaloader")
class InstaloaderEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        import instaloader
        import os

        match = re.search(r"instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url)
        if not match:
            return DownloadResult.fail("Unsupported Instagram URL format")
        shortcode = match.group(1)
        status_cb(f"⬇ Fetching Instagram post {shortcode}...", "#9a9a9a")
        progress_cb(0.3)
        loader = instaloader.Instaloader(
            dirname_pattern=save_dir,
            filename_pattern="{shortcode}",
            download_pictures=options.ig_download_pictures,
            download_videos=options.ig_download_videos,
            download_video_thumbnails=False,
            download_geotags=False, download_comments=False,
            save_metadata=False, quiet=True,
        )
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            ok = loader.download_post(post, target=save_dir)
            # instaloader's download_post() return value alone isn't fully
            # trustworthy across versions/login-wall states (it can return
            # True while actually only fetching metadata and skipping the
            # real media on a login-gated post) — GrabIt was previously
            # reporting success unconditionally without even checking this.
            # Verify a file matching the shortcode actually landed on disk
            # before claiming success.
            saved_files = [
                f for f in os.listdir(save_dir)
                if f.startswith(shortcode) and not f.endswith(".txt")
            ] if os.path.isdir(save_dir) else []
            if not ok or not saved_files:
                return DownloadResult.fail(
                    "Instagram did not return any media for this post — likely "
                    "login-gated or private. Anonymous Instagram scraping is "
                    "increasingly restricted by Instagram itself; this is not "
                    "something GrabIt can bypass."
                )
            progress_cb(1.0)
            return DownloadResult.ok(f"Instagram post {shortcode} downloaded!")
        except Exception as e:
            err = str(e).lower()
            if "login" in err or "401" in err or "403" in err:
                return DownloadResult.fail("Instagram requires login")
            return DownloadResult.fail(str(e)[:150])


@register_engine("pinterest")
class PinterestEngine(BaseEngine):
    @staticmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        from pinterest_dl import PinterestDL

        if "pin.it" in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10)
                url = resp.url
            except requests.RequestException:
                pass
        status_cb("⬇ Downloading Pinterest images...", "#9a9a9a")
        progress_cb(0.3)
        dl = PinterestDL.with_api()
        images = dl.scrape_and_download(url=url, output_dir=save_dir, num=1, download_streams=True)
        try:
            close_fn = getattr(dl, "close", None)
            if callable(close_fn):
                close_fn()
        except Exception:
            pass
        progress_cb(1.0)
        if images:
            return DownloadResult.ok(f"Saved {len(images)} image(s)", count=len(images))
        return DownloadResult.fail("No media found")
