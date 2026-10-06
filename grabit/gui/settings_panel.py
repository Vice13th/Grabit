"""Per-engine settings panel.

In the original script this class was fully built but never instantiated —
the single-download tab used a separate, ad-hoc "YouTube options" frame
instead, duplicating logic this panel already had. It's wired into the
single-download tab now (see :mod:`grabit.gui.single_tab`), so the
duplication is gone and adding a new options page for a future engine means
touching one place.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QStackedWidget,
    QVBoxLayout, QWidget,
)

from grabit.core.models import DownloadOptions


class SettingsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPanel")
        self._engine = None
        self._kind = None

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(16, 12, 16, 12)
        self.root.setSpacing(10)
        self.engine_label = QLabel("ENGINE: —")
        self.engine_label.setObjectName("SectionTitle")
        self.root.addWidget(self.engine_label)

        self.stack = QStackedWidget()
        self.root.addWidget(self.stack)
        self.empty_page = self._build_empty_page()
        self.video_page = self._build_video_page()
        self.image_page = self._build_image_page()
        self.file_page = self._build_file_page()
        self.audio_page = self._build_audio_page()
        for page in (self.empty_page, self.video_page, self.image_page, self.file_page, self.audio_page):
            self.stack.addWidget(page)
        self.set_engine(None, None)

    # -- page builders --------------------------------------------------
    def _build_empty_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("No settings available.")
        lbl.setStyleSheet("color: #7a7a7a; font-size: 12px;")
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _build_video_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        row1 = QHBoxLayout()
        lbl1 = QLabel("Format:")
        lbl1.setFixedWidth(80)
        lbl1.setStyleSheet("color: #b0b0b0;")
        row1.addWidget(lbl1)
        self.video_mode_combo = QComboBox()
        self.video_mode_combo.addItems(["🎬 Video (MP4)", "🎵 Audio only"])
        self.video_mode_combo.currentIndexChanged.connect(self._on_video_mode_changed)
        row1.addWidget(self.video_mode_combo, 1)
        lay.addLayout(row1)

        self.video_quality_row = QWidget()
        vq = QHBoxLayout(self.video_quality_row)
        vq.setContentsMargins(0, 0, 0, 0)
        lbl2 = QLabel("Quality:")
        lbl2.setFixedWidth(80)
        lbl2.setStyleSheet("color: #b0b0b0;")
        vq.addWidget(lbl2)
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(
            ["Best available", "4K (2160p)", "2K (1440p)", "Full HD (1080p)", "HD (720p)", "SD (480p)", "Low (360p)"]
        )
        self.video_quality_combo.setCurrentIndex(3)
        vq.addWidget(self.video_quality_combo, 1)
        lay.addWidget(self.video_quality_row)

        self.audio_quality_row = QWidget()
        aq = QHBoxLayout(self.audio_quality_row)
        aq.setContentsMargins(0, 0, 0, 0)
        lbl3 = QLabel("Bitrate:")
        lbl3.setFixedWidth(80)
        lbl3.setStyleSheet("color: #b0b0b0;")
        aq.addWidget(lbl3)
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["320 kbps (best)", "256 kbps", "192 kbps (default)", "128 kbps"])
        self.audio_quality_combo.setCurrentIndex(2)
        aq.addWidget(self.audio_quality_combo, 1)
        self.audio_quality_row.setVisible(False)
        lay.addWidget(self.audio_quality_row)

        self.audio_format_row = QWidget()
        af = QHBoxLayout(self.audio_format_row)
        af.setContentsMargins(0, 0, 0, 0)
        lbl4 = QLabel("Audio type:")
        lbl4.setFixedWidth(80)
        lbl4.setStyleSheet("color: #b0b0b0;")
        af.addWidget(lbl4)
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["MP3", "M4A", "OPUS", "FLAC", "WAV"])
        af.addWidget(self.audio_format_combo, 1)
        self.audio_format_row.setVisible(False)
        lay.addWidget(self.audio_format_row)

        lay.addStretch()
        return w

    def _build_image_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        info = QLabel("✓ Full-size / original resolution is downloaded automatically — pictures and videos both included where the source has them.")
        info.setStyleSheet("color: #3ddc84; font-size: 12px;")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.cb_min_res = QCheckBox("Skip low-resolution images (min 500px)")
        self.cb_min_res.setChecked(True)
        lay.addWidget(self.cb_min_res)
        lay.addStretch()
        return w

    def _build_file_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("✓ Original file will be downloaded without modification.\nFilename and extension are detected automatically.")
        lbl.setStyleSheet("color: #7a7a7a; font-size: 12px;")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _build_audio_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        info = QLabel("✓ Audio will be downloaded as MP3 (original quality).")
        info.setStyleSheet("color: #4CAF50; font-size: 12px;")
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addStretch()
        return w

    def _on_video_mode_changed(self, idx: int):
        is_audio = idx == 1
        self.video_quality_row.setVisible(not is_audio)
        self.audio_quality_row.setVisible(is_audio)
        self.audio_format_row.setVisible(is_audio)

    # -- public API -------------------------------------------------------
    def set_engine(self, engine: str | None, kind: str | None):
        self._engine = engine
        self._kind = kind
        self.engine_label.setText(f"ENGINE: {engine.upper() if engine else '—'}")
        if engine == "yt-dlp":
            self.stack.setCurrentWidget(self.video_page)
        elif engine in ("gallery-dl", "instaloader", "pinterest", "instacapture"):
            self.stack.setCurrentWidget(self.image_page)
        elif engine in ("gdrive", "dropbox", "mega", "direct", "civitai"):
            self.stack.setCurrentWidget(self.file_page)
        elif engine in ("soundcloud",):
            self.stack.setCurrentWidget(self.audio_page)
        elif engine in ("bilibili", "twitch", "reddit", "tiktok"):
            self.stack.setCurrentWidget(self.video_page)
        else:
            self.stack.setCurrentWidget(self.empty_page)

    def get_options(self) -> DownloadOptions:
        opts = DownloadOptions()
        if self._engine in ("yt-dlp", "bilibili", "twitch", "reddit", "tiktok"):
            is_audio = self.video_mode_combo.currentIndex() == 1
            opts.output_mode = "audio" if is_audio else "video"
            quality_map = {0: "best", 1: "2160", 2: "1440", 3: "1080", 4: "720", 5: "480", 6: "360"}
            opts.video_quality = quality_map.get(self.video_quality_combo.currentIndex(), "1080")
            bitrate_map = {0: "320", 1: "256", 2: "192", 3: "128"}
            opts.audio_quality = bitrate_map.get(self.audio_quality_combo.currentIndex(), "192")
            fmt_map = {0: "mp3", 1: "m4a", 2: "opus", 3: "flac", 4: "wav"}
            opts.audio_format = fmt_map.get(self.audio_format_combo.currentIndex(), "mp3")
        elif self._engine in ("gallery-dl", "instaloader", "pinterest", "instacapture"):
            opts.gallery_min_size = 500 if self.cb_min_res.isChecked() else 0
            # ig_download_pictures / ig_download_videos: no UI toggle — both
            # default True on DownloadOptions, matching the removed
            # checkboxes' always-checked default, so Instagram behavior is
            # unchanged (all engines, not just Instagram's, used this page).
        return opts
