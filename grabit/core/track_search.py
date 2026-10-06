"""Search for a track by artist + title, without a direct URL.

Three tiers, each only attempted if the previous one produced no results —
mirrors the "if a source can't do it, try the next one" pattern already
used by SoundCloudEngine/BilibiliEngine, but for *searching* rather than
*downloading a known URL*:

1. yt-dlp's ``scsearch:`` — SoundCloud search, kept as tier 1 to keep
   SoundCloud as the first-choice source (same platform priority the
   existing SoundCloud download engine has), but resolved through yt-dlp's
   maintained extractor rather than screen-scraping soundcloud.com's HTML.
   An earlier version of this module did exactly that HTML-scraping —
   soundcloud.com's search page is a JS-rendered SPA, so a plain
   ``requests.get()`` never saw real results; removed.
2. yt-dlp's ``ytmsearch:`` — YouTube Music search. Official, documented
   yt-dlp prefix (same syntax as ytsearch); tends to surface studio/official
   uploads before random covers or live versions.
3. yt-dlp's ``ytsearch:`` — general YouTube search, broadest catch-all.

IMPORTANT: tier 1 (``scsearch``) must NOT use yt-dlp's ``extract_flat``.
That combination is a confirmed upstream yt-dlp bug (github.com/yt-dlp/
yt-dlp issue #14443): in flat mode, SoundCloud search entries come back
with ``url`` pointing at an internal ``api.soundcloud.com/tracks/...``
endpoint that yt-dlp itself can't resolve later ("No suitable extractor
(Soundcloud) found for URL ..."), not a real, downloadable page URL. Tiers
2/3 (YouTube-backed) are unaffected by that bug and stay flat for speed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TrackResult:
    title: str
    uploader: str
    url: str
    duration: Optional[float]
    source: str  # "soundcloud", "youtube-music", or "youtube" — display only


def _entry_url(entry: dict) -> Optional[str]:
    url = entry.get("webpage_url") or entry.get("url")
    if url and url.startswith(("http://", "https://")):
        return url
    # Flat YouTube/YT-Music entries sometimes give just a bare video id.
    vid = entry.get("id")
    if vid and entry.get("ie_key", "").lower().startswith("youtube"):
        return f"https://www.youtube.com/watch?v={vid}"
    return None


def _search_ytdlp(query: str, prefix: str, source: str, max_results: int, flat: bool) -> List[TrackResult]:
    try:
        import yt_dlp
    except ImportError:
        return []
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    if flat:
        opts["extract_flat"] = "in_playlist"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"{prefix}{max_results}:{query}", download=False)
        entries = (info or {}).get("entries") or []
        results = []
        for e in entries:
            if not e:
                continue
            url = _entry_url(e)
            if not url:
                continue
            results.append(TrackResult(
                e.get("title") or "Unknown title",
                e.get("uploader") or e.get("channel") or e.get("artist") or "Unknown artist",
                url, e.get("duration"), source,
            ))
        return results
    except Exception:
        return []


def search_track(artist: str, title: str, max_results: int = 8) -> List[TrackResult]:
    """Search by artist + title (either may be blank). Returns an empty
    list only if every tier below found nothing — never raises."""
    query = " ".join(p for p in (artist.strip(), title.strip()) if p).strip()
    if not query:
        return []

    results = _search_ytdlp(query, "scsearch", "soundcloud", max_results, flat=False)
    if results:
        return results

    results = _search_ytdlp(query, "ytmsearch", "youtube-music", max_results, flat=True)
    if results:
        return results

    return _search_ytdlp(query, "ytsearch", "youtube", max_results, flat=True)
