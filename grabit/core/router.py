"""SmartRouter: decides which engine handles a given URL.

Behavior-preserving port of the original ``SmartRouter`` with one bug fix
(see ``_classify_direct_extension`` below) and one architectural change:
optional-dependency availability (is streamlink/aria2c installed?) is
now passed in explicitly instead of read from a module-level global, so the
router can be unit-tested with any availability combination and doesn't
depend on import order.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

from grabit.core.models import RouteDecision

# ----------------------------------------------------------------------
# Pattern tables
# ----------------------------------------------------------------------
GALLERY_DL_PATTERNS = [
    r"pixiv\.net", r"deviantart\.com", r"artstation\.com",
    r"danbooru\.donmai\.us", r"gelbooru\.com", r"e621\.net",
    r"konachan\.com", r"yande\.re", r"mangadex\.org",
    r"webtoons\.com", r"flickr\.com", r"tumblr\.com",
    r"imgur\.com", r"patreon\.com", r"fanbox\.cc",
    r"gumroad\.com", r"behance\.net", r"dribbble\.com",
    r"500px\.com", r"smugmug\.com", r"mastodon",
    r"bsky\.app", r"pillowfort\.social", r"tapas\.io",
    r"dynasty-scans\.com", r"civitai\.com",
    r"bunkr", r"erome\.com", r"coomer\.party",
    r"kemono\.party", r"4chan\.org", r"archive\.org/details",
    r"are\.na", r"bluesky\.app", r"booth\.pm", r"cohost\.org",
    r"fanbox\.cc", r"fantia\.jp", r"newgrounds\.com", r"inkbunny\.net",
    r"itaku\.ee", r"iwara\.tv", r"mangadex\.org", r"webtoons\.com",
    r"kemono\.su", r"gelbooru\.com", r"danbooru\.donmai\.us",
    r"e926\.net", r"aibooru\.online", r"furaffinity\.net",
]
PINTEREST_PATTERNS = [r"pinterest\.\w+", r"pin\.it"]
INSTAGRAM_PATTERNS = [r"instagram\.com"]
GDRIVE_PATTERNS = [r"drive\.google\.com", r"docs\.google\.com"]
DROPBOX_PATTERNS = [r"dropbox\.com"]
MEGA_PATTERNS = [r"mega\.nz", r"mega\.co\.nz"]
BILIBILI_PATTERNS = [r"bilibili\.com"]
TWITCH_PATTERNS = [r"twitch\.tv"]
SOUNDCLOUD_PATTERNS = [r"soundcloud\.com"]
REDDIT_PATTERNS = [r"reddit\.com", r"redd\.it"]
TIKTOK_PATTERNS = [r"tiktok\.com"]
CIVITAI_PATTERNS = [r"civitai\.com"]
STREAMLINK_PATTERNS = [
    r"twitch\.tv", r"kick\.com", r"rumble\.com", r"abema\.tv",
    r"afreecatv\.com", r"17live\.com",
]
ARIA2_PROTOCOL_PATTERNS = [r"^magnet:", r"\.torrent(?:$|[?#])", r"\.metalink(?:$|[?#])"]
RCLONE_PATTERN = r"^rclone://"
STREAM_EXTENSIONS = [".m3u8", ".m3u", ".mpd"]
YTDLP_PATTERNS = [
    r"youtube\.com", r"youtu\.be", r"twitter\.com", r"x\.com",
    r"facebook\.com", r"fb\.watch", r"vimeo\.com",
    r"dailymotion\.com", r"dai\.ly", r"linkedin\.com",
    r"youku\.com", r"douyin\.com", r"rutube\.ru",
    r"vk\.com/video", r"aparat\.com", r"bandcamp\.com",
    r"mixcloud\.com", r"audiomack\.com", r"ted\.com",
    r"bbc\.co\.uk", r"aljazeera\.com", r"cnn\.com",
    r"9gag\.com", r"rumble\.com", r"odysee\.com", r"kick\.com",
    r"17live\.com", r"23video\.com", r"24tv\.ua", r"3sat\.de",
    r"7plus\.com\.au", r"9news\.com\.au", r"9now\.com\.au",
    r"abc\.net\.au", r"abematv\.akamaized\.net", r"abema\.tv",
    r"afreecatv\.com", r"archive\.org/details", r"arte\.tv",
    r"art19\.com", r"audiodraft\.com", r"audius\.co",
    r"bandlab\.com", r"buzzsprout\.com", r"cbc\.ca", r"cbs\.com",
    r"c-span\.org", r"cctv\.com", r"dw\.com", r"euronews\.com",
    r"fox\.com", r"france\.tv", r"imdb\.com", r"khanacademy\.org",
    r"loom\.com", r"mediathekviewweb\.de", r"nebula\.tv",
    r"niconico\.jp", r"nos\.nl", r"peertube\.[^/]+", r"pluto\.tv",
    r"podbean\.com", r"podcasts\.apple\.com", r"ted\.com",
    r"triller\.co", r"u-next\.com", r"veoh\.com", r"vlive\.tv",
    r"watchever\.de", r"weverse\.io", r"wistia\.com", r"wistia\.net",
]

# Extension -> media kind, expressed directly instead of via list-slicing.
#
# BUG FIX vs. the original script: the previous implementation classified
# kind with ``DIRECT_EXTENSIONS[:13]`` / ``[13:26]`` / ``[26:34]`` slices.
# Those boundaries didn't line up with where the video/audio/image groups
# actually started in the list, so most audio extensions were reported as
# "image" and several image extensions (plus ``.zip``) were reported as
# "audio". It had no visible effect only because nothing downstream read
# `kind` yet (the settings panel keyed off the *engine* name instead); now
# that the settings panel is wired up and can use `kind`, it needs to be
# correct.
_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv",
    ".m4v", ".3gp", ".mpg", ".mpeg", ".ts", ".m2ts",
}
_AUDIO_EXTENSIONS = {
    ".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac", ".wma",
}
_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg",
    ".tiff", ".tif", ".ico", ".heic", ".avif",
}
_OTHER_FILE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".iso", ".dmg", ".tgz", ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".epub", ".mobi",
    ".odt", ".ods", ".odp", ".rtf", ".exe", ".msi",
    ".apk", ".deb", ".rpm", ".appimage", ".jar", ".bin",
    ".img", ".json", ".xml", ".csv", ".sql", ".db", ".sqlite",
}
DIRECT_EXTENSIONS = (
    _VIDEO_EXTENSIONS | _AUDIO_EXTENSIONS | _IMAGE_EXTENSIONS | _OTHER_FILE_EXTENSIONS
)


def _classify_direct_extension(ext: str) -> str:
    if ext in _VIDEO_EXTENSIONS:
        return "video"
    if ext in _AUDIO_EXTENSIONS:
        return "audio"
    if ext in _IMAGE_EXTENSIONS:
        return "image"
    return "file"


class SmartRouter:
    """Stateless URL -> engine classifier.

    ``route()`` is a classmethod (no instance state) so it can be called as
    ``SmartRouter.route(url, optional_status)`` from anywhere — the GUI's
    live "detected engine" badge, the batch importer, and the worker thread
    all share the exact same decision logic.
    """

    @classmethod
    def route(cls, url: str, optional_status: Optional[Dict[str, bool]] = None) -> RouteDecision:
        status = optional_status if optional_status is not None else _fallback_optional_status()
        url_lower = (url or "").strip().lower()

        if re.match(RCLONE_PATTERN, url_lower):
            return RouteDecision("rclone", "file", "Cloud Remote", "#2F80ED", "☁")

        # Cloud storage
        for pat in GDRIVE_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("gdrive", "file", "Google Drive", "#4285F4", "📁")
        for pat in DROPBOX_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("dropbox", "file", "Dropbox", "#0061FF", "📦")
        for pat in MEGA_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("mega", "file", "Mega.nz", "#D9272E", "M")

        # Specialized social/media
        for pat in PINTEREST_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("pinterest", "image", "Pinterest", "#E60023", "📌")
        for pat in INSTAGRAM_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("instaloader", "image", "Instagram", "#E1306C", "📷")
        for pat in BILIBILI_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("bilibili", "video", "Bilibili", "#00A1D6", "B")
        for pat in TWITCH_PATTERNS:
            if re.search(pat, url_lower):
                if "/videos/" in url_lower or not status.get("streamlink", False):
                    engine = "twitch"
                else:
                    engine = "streamlink"
                return RouteDecision(engine, "video", "Twitch", "#9146FF", "🎮")
        for pat in SOUNDCLOUD_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("soundcloud", "audio", "SoundCloud", "#FF5500", "🎵")
        for pat in REDDIT_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("reddit", "video", "Reddit", "#FF4500", "👽")
        for pat in TIKTOK_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("tiktok", "video", "TikTok", "#69C9D0", "🎵")
        for pat in CIVITAI_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("civitai", "file", "CivitAI", "#9C27B0", "🎨")

        # Live streams / protocol manifests
        if any(re.search(pat, url_lower) for pat in STREAMLINK_PATTERNS):
            if status.get("streamlink", False):
                return RouteDecision("streamlink", "video", "Live Stream", "#8E44AD", "◉")
        path = url_lower.split("?")[0].split("#")[0].rstrip("/")
        if any(path.endswith(ext) for ext in STREAM_EXTENSIONS):
            if status.get("streamlink", False):
                return RouteDecision("streamlink", "video", "Stream Manifest", "#8E44AD", "◉")
            return RouteDecision("yt-dlp", "video", "Stream Manifest", "#FF0000", "▶")

        # BitTorrent / Metalink
        if any(re.search(pat, url_lower) for pat in ARIA2_PROTOCOL_PATTERNS):
            if status.get("aria2c", False):
                return RouteDecision("aria2", "file", "P2P / Multi-source", "#F39C12", "⚡")

        # Direct file link; aria2 is used only when available.
        for ext in DIRECT_EXTENSIONS:
            if path.endswith(ext):
                kind = _classify_direct_extension(ext)
                engine = "aria2" if status.get("aria2c", False) else "direct"
                return RouteDecision(engine, kind, "Direct Link", "#00BCD4", "🔗")

        # gallery-dl
        for pat in GALLERY_DL_PATTERNS:
            if re.search(pat, url_lower):
                return RouteDecision("gallery-dl", "image", cls._extract_platform_name(pat), "#9C27B0", "🖼️")

        # yt-dlp
        for pat in YTDLP_PATTERNS:
            if re.search(pat, url_lower):
                kind = "audio" if any(
                    x in url_lower for x in ("music.", "podcast", "audiomack", "audius", "bandcamp", "soundcloud")
                ) else "video"
                return RouteDecision("yt-dlp", kind, cls._extract_platform_name(pat), "#FF0000", "▶")

        # Generic HTTP(S) fallback: yt-dlp may still support embeds/generic extractors.
        if re.match(r"https?://", url_lower):
            return RouteDecision("yt-dlp", "video", "Generic Web", "#FF0000", "▶")

        if re.search(r"\.[a-z0-9]{2,5}$", path):
            return RouteDecision("direct", "file", "Direct Link", "#00BCD4", "🔗")

        return RouteDecision(None, None, "Unknown", "#9a9a9a", "❓")

    @staticmethod
    def _extract_platform_name(pattern: str) -> str:
        name = pattern.replace(r"\.", ".").replace(r"\w+", "x")
        name = name.replace("^", "").replace("$", "")
        name = name.replace(r"(", "").replace(r")", "")
        name = name.replace("|", "/").split("/")[0]
        return name.strip().title() if name else "Unknown"


def _fallback_optional_status() -> Dict[str, bool]:
    """Used only when a caller doesn't pass ``optional_status`` explicitly
    (e.g. quick scripts/tests). Production code paths always pass the
    dependency snapshot computed once at startup instead of calling this,
    since it performs real imports and is too slow to call per keystroke."""
    from grabit.dependencies.manager import detect_optional_dependencies
    return detect_optional_dependencies()
