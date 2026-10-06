"""Small, presentation-only metadata about engines/platforms.

Deliberately separate from :mod:`grabit.core.router` — the router owns
*routing* decisions (URL -> engine/platform/color/icon) and is imported by
non-GUI code/tests; this module only adds a short human-readable feature
blurb per engine for the "Detected platform" panel and the Engines page, so
GUI-only concerns don't creep into the routing layer.
"""
from __future__ import annotations

ENGINE_FEATURES = {
    "yt-dlp": "Playlist, Subtitles, Chapters",
    "gallery-dl": "Albums, Full-resolution, Metadata",
    "instaloader": "Stories, Posts, Reels",
    "pinterest": "Boards, Pins, Original size",
    "bilibili": "Video, Danmaku, Multi-part",
    "twitch": "VOD, Clips",
    "streamlink": "Live stream capture",
    "soundcloud": "Tracks, Sets, Metadata",
    "reddit": "Video, Gallery, Crossposts",
    "tiktok": "Video, No-watermark",
    "civitai": "Model files, Preview images",
    "gdrive": "Single file / shared folder",
    "dropbox": "Direct file link",
    "mega": "Encrypted file link",
    "rclone": "Configured cloud remote",
    "aria2": "Multi-connection, Resume",
    "direct": "Resumable HTTP(S) download",
    "playwright": "JS-rendered page fallback",
}

ENGINE_DESCRIPTIONS = {
    "yt-dlp": "The core video/audio engine — covers YouTube and hundreds of generic sites.",
    "gallery-dl": "Image gallery & booru engine for art/photo sites (Pixiv, DeviantArt, Danbooru...).",
    "instaloader": "Instagram-specific engine for posts, stories and reels.",
    "pinterest": "Pinterest boards and pins at original resolution.",
    "bilibili": "Native Bilibili video engine (falls back to yt-dlp automatically if bilix/danmakuC can't install — e.g. no Python 3.12 wheel yet).",
    "twitch": "Twitch VODs and clips.",
    "streamlink": "Captures live streams (Twitch, Kick, Rumble...) as they air.",
    "soundcloud": "SoundCloud tracks and sets.",
    "reddit": "Reddit video/gallery posts.",
    "tiktok": "TikTok video downloads.",
    "civitai": "CivitAI model & image files.",
    "gdrive": "Public Google Drive files and folders.",
    "dropbox": "Public Dropbox share links.",
    "mega": "Mega.nz encrypted share links.",
    "rclone": "Any cloud remote configured in rclone.",
    "aria2": "Multi-connection accelerated downloader for direct links & torrents.",
    "direct": "Plain HTTP(S) direct file download.",
    "playwright": "Headless-browser fallback for JavaScript-heavy pages.",
}


def features_for(engine: str | None) -> str:
    if not engine:
        return "—"
    return ENGINE_FEATURES.get(engine, "Standard download")


def description_for(engine: str) -> str:
    return ENGINE_DESCRIPTIONS.get(engine, "")
