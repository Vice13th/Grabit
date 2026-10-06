"""Search-by-name page: find a track by artist + title (no URL needed),
pick a result, then download it through the exact same shared thread
lifecycle as the Grab/Batch pages (same ``start_requested`` contract).
"""
from __future__ import annotations

import os

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from grabit.core.models import DownloadOptions
from grabit.core.track_search import TrackResult, search_track
from grabit.gui.anim_widgets import Card, GlowProgressBar
from grabit.gui.settings_panel import SettingsPanel
from grabit.gui.theme import TEXT_DIM


class _SearchThread(QThread):
    finished_search = Signal(list, str)  # results, error

    def __init__(self, artist: str, title: str, parent=None):
        super().__init__(parent)
        self.artist = artist
        self.title = title

    def run(self):
        try:
            results = search_track(self.artist, self.title)
            self.finished_search.emit(results, "")
        except Exception as e:  # search_track shouldn't raise, but never crash the thread
            self.finished_search.emit([], str(e)[:200])


class SearchPage(QWidget):
    start_requested = Signal(str, str, object)  # url, save_dir, DownloadOptions
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, default_save_dir: str, parent=None):
        super().__init__(parent)
        self._results: list[TrackResult] = []
        self._search_thread: _SearchThread | None = None
        self._build_ui(default_save_dir)

    def _build_ui(self, default_save_dir: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)

        title = QLabel("Search")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("Find a track by artist and title — no URL needed.")
        sub.setObjectName("DimLabel")
        outer.addWidget(sub)

        search_card = Card("SEARCH")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.artist_entry = QLineEdit()
        self.artist_entry.setPlaceholderText("Artist (optional)")
        self.artist_entry.returnPressed.connect(self._run_search)
        row.addWidget(self.artist_entry, 1)
        self.title_entry = QLineEdit()
        self.title_entry.setPlaceholderText("Track title")
        self.title_entry.returnPressed.connect(self._run_search)
        row.addWidget(self.title_entry, 1)
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setObjectName("GrabBtn")
        self.search_btn.setFixedHeight(38)
        self.search_btn.clicked.connect(self._run_search)
        row.addWidget(self.search_btn)
        search_card.add(row)

        self.status_label = QLabel("Searches SoundCloud first, then YouTube as a fallback.")
        self.status_label.setObjectName("StatusLabel")
        search_card.add(self.status_label)

        self.results_list = QListWidget()
        self.results_list.setFixedHeight(220)
        self.results_list.itemSelectionChanged.connect(self._on_selection_changed)
        search_card.add(self.results_list)
        outer.addWidget(search_card)

        opts_card = Card("DOWNLOAD OPTIONS")
        self.settings_panel = SettingsPanel()
        opts_card.add(self.settings_panel)
        path_row = QHBoxLayout()
        self.path_entry = QLineEdit(default_save_dir)
        path_row.addWidget(self.path_entry, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("BrowseBtn")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        opts_card.add(path_row)

        bar_row = QHBoxLayout()
        self.progress_bar = GlowProgressBar()
        bar_row.addWidget(self.progress_bar, 1)
        opts_card.add(bar_row)
        self.dl_status_label = QLabel("")
        self.dl_status_label.setObjectName("StatusLabel")
        opts_card.add(self.dl_status_label)

        self.download_btn = QPushButton("⬇ Download Selected")
        self.download_btn.setObjectName("GrabBtn")
        self.download_btn.setFixedHeight(40)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._start_download)
        opts_card.add(self.download_btn)
        outer.addWidget(opts_card)
        outer.addStretch()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.path_entry.text())
        if folder:
            self.path_entry.setText(folder)

    def _run_search(self):
        artist = self.artist_entry.text().strip()
        title = self.title_entry.text().strip()
        if not artist and not title:
            self.status_label.setText("⚠ Enter at least a track title")
            return
        self.results_list.clear()
        self.download_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.status_label.setText("🔎 Searching...")
        self._search_thread = _SearchThread(artist, title, self)
        self._search_thread.finished_search.connect(self._on_search_finished)
        self._search_thread.start()

    def _on_search_finished(self, results: list, error: str):
        self.search_btn.setEnabled(True)
        self._results = results
        if error:
            self.status_label.setText(f"✗ Search error: {error}")
            return
        if not results:
            self.status_label.setText("No results found on SoundCloud or YouTube.")
            return
        for r in results:
            mins = f"{int(r.duration // 60)}:{int(r.duration % 60):02d}" if r.duration else "—"
            item = QListWidgetItem(f"{r.title}  —  {r.uploader}   [{r.source} · {mins}]")
            self.results_list.addItem(item)
        self.status_label.setText(f"✓ {len(results)} result(s)")

    def _on_selection_changed(self):
        self.download_btn.setEnabled(bool(self.results_list.selectedItems()))
        row = self.results_list.currentRow()
        if 0 <= row < len(self._results):
            r = self._results[row]
            engine = "soundcloud" if r.source == "soundcloud" else "yt-dlp"
            self.settings_panel.set_engine(engine, "audio")

    def _start_download(self):
        row = self.results_list.currentRow()
        if not (0 <= row < len(self._results)):
            return
        result = self._results[row]
        save_dir = self.path_entry.text().strip()
        if not save_dir:
            self.dl_status_label.setText("⚠ Please select a save folder")
            return
        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            self.dl_status_label.setText(f"✗ Cannot create folder: {e}")
            return
        options = self.settings_panel.get_options()
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.set_active(True)
        self.set_status(f"⏳ Starting download: {result.title}...", "#8a8a90")
        self.start_requested.emit(result.url, save_dir, options)

    # -- slots driven by main window / worker thread (same contract as GrabPage) --
    def set_status(self, text: str, color: str):
        self.dl_status_label.setText(text)
        self.dl_status_label.setStyleSheet(f"color: {color}; font-family: 'JetBrains Mono', monospace; font-size: 12px;")

    def set_progress(self, value: float):
        self.progress_bar.setValue(int(value * 100))

    def set_controls(self, running: bool = False, paused: bool = False, cancelling: bool = False):
        pass  # search-and-download is single-shot; no pause/resume UI here

    def on_download_finished(self, success: bool):
        self.progress_bar.set_active(False)
        self.download_btn.setEnabled(bool(self.results_list.selectedItems()))
