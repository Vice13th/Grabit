"""Read-only page listing every registered engine, its availability and a
short description. Pulls live from the engine registry
(:mod:`grabit.engines`) and dependency status, so it can't drift out of
sync with what the router can actually route to.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from grabit.gui.anim_widgets import Card, status_row
from grabit.gui.engine_meta import description_for


REQUIRED_ALWAYS = {"yt-dlp", "gallery-dl", "instaloader", "direct", "dropbox", "mega"}
OPTIONAL_KEY = {
    "pinterest": "pinterest-dl", "gdrive": "gdown", "bilibili": "bilix",
    "twitch": "twitch-archiver", "soundcloud": "soundcloud-lib", "reddit": "RedDownloader",
    "tiktok": "tiktok-downloader-py", "instacapture": "instacapture", "civitai": "civitai-downloader",
    "streamlink": "streamlink", "aria2": "aria2c", "rclone": "rclone",
    "playwright": "playwright",
}


class EnginesPage(QWidget):
    def __init__(self, optional_status: dict, parent=None):
        super().__init__(parent)
        from grabit.engines import available_engine_names

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(12)

        title = QLabel("Engines")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("Every backend GrabIt can route a URL to, and whether it's available right now.")
        sub.setObjectName("DimLabel")
        outer.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(12)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        names = available_engine_names()
        cols = 2
        for i, name in enumerate(names):
            available = True
            for opt_name, dep_key in OPTIONAL_KEY.items():
                if name == opt_name:
                    available = bool(optional_status.get(dep_key, False))
            card = Card(name.upper())
            row = status_row("ok" if available else "warn", "Available" if available else "Not installed", mono=False)
            card.add(row)
            desc = QLabel(description_for(name) or "Specialized backend engine.")
            desc.setWordWrap(True)
            desc.setObjectName("DimLabel")
            card.add(desc)
            grid.addWidget(card, i // cols, i % cols)
