"""Probes a YouTube URL to see whether it resolves to a playlist before the
main download starts, so the GUI can ask "download the whole playlist?"
instead of silently grabbing one or grabbing everything."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class PlaylistProbeThread(QThread):
    finished_probe = Signal(bool, int, str, bool, str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            import yt_dlp
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": "in_playlist",
                "noplaylist": False,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            entries = info.get("entries") if isinstance(info, dict) else None
            is_playlist = bool(entries) or (isinstance(info, dict) and info.get("_type") == "playlist")
            count = len(entries) if hasattr(entries, "__len__") else 0
            title = (info.get("title") or "YouTube Playlist") if isinstance(info, dict) else "YouTube Playlist"
            playlist_only = isinstance(info, dict) and info.get("_type") == "playlist"
            self.finished_probe.emit(is_playlist, count, title, playlist_only, "")
        except Exception as exc:
            self.finished_probe.emit(False, 0, "", False, str(exc)[:220])
