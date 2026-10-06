"""Batch (multi-URL) download tab.

New vs. the original script: a "Parallel downloads" spinbox lets the user
opt into concurrent downloads (see
:meth:`grabit.workers.download_thread.DownloadThread._run_concurrent`).
Defaults to 1 (fully sequential, byte-for-byte the old behavior) unless the
user has changed ``AppConfig.concurrent_batch_downloads``.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from grabit.config import AppConfig
from grabit.core.models import DownloadOptions
from grabit.core.url_utils import extract_urls_regex, is_valid_url, parse_urls_from_file


class BatchDownloadTab(QWidget):
    start_requested = Signal(list, str, object, int)  # urls, save_dir, DownloadOptions, max_concurrency
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, default_save_dir: str, optional_status: dict, config: AppConfig, parent=None):
        super().__init__(parent)
        self.optional_status = optional_status
        self.config = config
        self.last_save_dir = ""
        self._busy = False
        self._build_ui(default_save_dir)

    def _build_ui(self, default_save_dir: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Batch Download")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel("Paste URLs or load from a file — supports TXT, CSV, JSON, XML, YAML, Markdown, HTML")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        url_header = QHBoxLayout()
        url_label = QLabel("URL list:")
        url_label.setObjectName("FieldLabel")
        url_header.addWidget(url_label)
        url_header.addStretch()
        self.batch_count_label = QLabel("0 URLs")
        self.batch_count_label.setObjectName("PlatformBadge")
        url_header.addWidget(self.batch_count_label)
        layout.addLayout(url_header)
        layout.addSpacing(4)

        self.batch_input = QPlainTextEdit()
        self.batch_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=...\n"
            "https://www.instagram.com/p/...\n"
            "https://pin.it/...\n"
            "https://example.com/video.mp4       ← direct link\n"
            "https://example.com/archive.zip     ← direct link\n"
            "https://drive.google.com/file/d/...\n"
            "..."
        )
        self.batch_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.batch_input, 1)

        io_row = QHBoxLayout()
        io_row.setSpacing(10)
        load_btn = QPushButton("📁 Load from file")
        load_btn.setObjectName("SmallBtn")
        load_btn.clicked.connect(self._load_from_file)
        io_row.addWidget(load_btn)
        save_btn = QPushButton("💾 Save list")
        save_btn.setObjectName("SmallBtn")
        save_btn.clicked.connect(self._save_to_file)
        io_row.addWidget(save_btn)
        paste_btn = QPushButton("📋 Paste from clipboard")
        paste_btn.setObjectName("SmallBtn")
        paste_btn.clicked.connect(self._paste_from_clipboard)
        io_row.addWidget(paste_btn)
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setObjectName("SmallBtn")
        clear_btn.clicked.connect(lambda: self.batch_input.clear())
        io_row.addWidget(clear_btn)
        io_row.addStretch()
        layout.addLayout(io_row)

        batch_hint = QLabel(
            "ℹ Supported list formats:\n"
            "  • TXT — one URL per line\n"
            "  • CSV — URLs in any cell (auto-detect)\n"
            "  • JSON — recursive URL extraction\n"
            "  • YAML / XML / RSS / HTML — auto URL extraction\n"
            "  • Markdown — [text](url) links + raw URLs\n"
            "  • Any text — regex fallback finds all http(s) URLs"
        )
        batch_hint.setStyleSheet("color: #9a9a9a; font-size: 11px; padding: 8px 12px; background-color: #232323; border-radius: 8px;")
        batch_hint.setWordWrap(True)
        layout.addWidget(batch_hint)

        path_label = QLabel("Save to:")
        path_label.setObjectName("FieldLabel")
        layout.addWidget(path_label)
        layout.addSpacing(4)
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_entry = QLineEdit()
        self.path_entry.setText(default_save_dir)
        self.path_entry.setFixedHeight(42)
        path_row.addWidget(self.path_entry, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("BrowseBtn")
        browse_btn.setFixedHeight(42)
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        concurrency_row = QHBoxLayout()
        concurrency_row.setSpacing(10)
        concurrency_label = QLabel("Parallel downloads:")
        concurrency_label.setObjectName("FieldLabel")
        concurrency_row.addWidget(concurrency_label)
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 8)
        self.concurrency_spin.setValue(max(1, self.config.concurrent_batch_downloads))
        self.concurrency_spin.setFixedWidth(70)
        self.concurrency_spin.setToolTip(
            "1 = one URL at a time (safest, matches the original behavior).\n"
            "Higher values download several URLs at once — faster for large\n"
            "batches, but uses more bandwidth/CPU/disk at once."
        )
        concurrency_row.addWidget(self.concurrency_spin)
        concurrency_row.addStretch()
        layout.addLayout(concurrency_row)

        layout.addSpacing(10)
        self.download_btn = QPushButton("🚀  Start Batch Download")
        self.download_btn.setObjectName("DownloadBtn")
        self.download_btn.setFixedHeight(48)
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)

        control_row = QHBoxLayout()
        control_row.setSpacing(8)
        self.pause_btn = QPushButton("⏸ Pause")
        self.resume_btn = QPushButton("▶ Resume")
        self.cancel_btn = QPushButton("✕ Cancel")
        for btn in (self.pause_btn, self.resume_btn, self.cancel_btn):
            btn.setObjectName("SmallBtn")
            btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_requested.emit)
        self.resume_btn.clicked.connect(self.resume_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        control_row.addWidget(self.pause_btn)
        control_row.addWidget(self.resume_btn)
        control_row.addWidget(self.cancel_btn)
        layout.addLayout(control_row)
        layout.addSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(8)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    # -- URL list management -------------------------------------------------
    def _current_urls(self) -> list[str]:
        text = self.batch_input.toPlainText()
        urls = [u.strip() for u in text.splitlines() if u.strip() and is_valid_url(u.strip())]
        if not urls and text.strip():
            urls = extract_urls_regex(text)
        seen, unique = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique

    def _on_text_changed(self):
        count = len(self._current_urls())
        self.batch_count_label.setText(f"{count} URL{'s' if count != 1 else ''}")

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load URL list",
            "", "All supported (*.txt *.csv *.tsv *.json *.yaml *.yml *.xml *.html *.htm *.md);;All files (*.*)",
        )
        if not path:
            return
        urls = parse_urls_from_file(path)
        if not urls:
            QMessageBox.information(self, "No URLs found", "Could not find any URLs in that file.")
            return
        existing = self.batch_input.toPlainText().strip()
        self.batch_input.setPlainText((existing + "\n" if existing else "") + "\n".join(urls))

    def _save_to_file(self):
        urls = self._current_urls()
        if not urls:
            QMessageBox.information(self, "Nothing to save", "The URL list is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save URL list", "urls.txt", "Text files (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(urls))
        except OSError as e:
            QMessageBox.warning(self, "Could not save", str(e))

    def _paste_from_clipboard(self):
        from PySide6.QtWidgets import QApplication
        text = (QApplication.clipboard().text() or "").strip()
        if not text:
            return
        existing = self.batch_input.toPlainText().strip()
        self.batch_input.setPlainText((existing + "\n" if existing else "") + text)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.path_entry.text())
        if folder:
            self.path_entry.setText(folder)

    # -- download lifecycle ---------------------------------------------------
    def _start_download(self):
        if self._busy:
            return
        urls = self._current_urls()
        if not urls:
            self.set_status("⚠ Add at least one valid URL", "#FF9800")
            return
        save_dir = self.path_entry.text().strip()
        if not save_dir:
            self.set_status("⚠ Please select a save folder", "#FF9800")
            return
        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            self.set_status(f"✗ Cannot create folder: {e}", "#F44336")
            return

        self._busy = True
        self.last_save_dir = save_dir
        self._set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.set_controls(running=True, paused=False)
        self.set_status(f"⏳ Starting batch of {len(urls)} URL(s)...", "#9a9a9a")

        options = DownloadOptions()  # batch uses one shared, generic configuration
        self.start_requested.emit(urls, save_dir, options, self.concurrency_spin.value())

    def _set_ui_enabled(self, enabled: bool):
        self.batch_input.setEnabled(enabled)
        self.path_entry.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
        self.concurrency_spin.setEnabled(enabled)

    # -- slots driven by the main window / worker thread ----------------------
    def set_status(self, text: str, color: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def set_progress(self, value: float):
        self.progress_bar.setValue(int(value * 100))

    def set_controls(self, running: bool = False, paused: bool = False, cancelling: bool = False):
        self.pause_btn.setEnabled(bool(running and not paused and not cancelling))
        self.resume_btn.setEnabled(bool(running and paused and not cancelling))
        self.cancel_btn.setEnabled(bool(running and not cancelling))

    def on_download_finished(self, success: bool):
        self._busy = False
        self._set_ui_enabled(True)
        self.set_controls(running=False)
