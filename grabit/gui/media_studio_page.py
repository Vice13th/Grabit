"""Media Studio: a lightweight browser over the files GrabIt has actually
saved to disk, in the configured save folder.

This is intentionally *not* a media editor / transcoder — that would be a
new, separate engine and out of scope for a UI redesign task. What it does
do: list what's there, show size/modified time, and let you open or reveal
a file, since the original app had no way to see your downloads without
leaving it.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

_KIND_ICON = {
    ".mp4": "🎬", ".mkv": "🎬", ".webm": "🎬", ".mov": "🎬", ".avi": "🎬",
    ".mp3": "🎵", ".m4a": "🎵", ".flac": "🎵", ".wav": "🎵", ".opus": "🎵",
    ".jpg": "🖼", ".jpeg": "🖼", ".png": "🖼", ".gif": "🖼", ".webp": "🖼",
}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


class MediaStudioPage(QWidget):
    def __init__(self, default_dir: str, parent=None):
        super().__init__(parent)
        self.current_dir = default_dir
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        title = QLabel("Media Studio")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("Browse what's already been grabbed into your save folder.")
        sub.setObjectName("DimLabel")
        outer.addWidget(sub)

        folder_row = QHBoxLayout()
        self.dir_edit = QLineEdit(default_dir)
        folder_row.addWidget(self.dir_edit, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("BrowseBtn")
        browse_btn.clicked.connect(self._browse)
        folder_row.addWidget(browse_btn)
        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.setObjectName("SmallBtn")
        refresh_btn.clicked.connect(self.refresh)
        folder_row.addWidget(refresh_btn)
        outer.addLayout(folder_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "Name", "Size", "Modified"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnWidth(0, 30)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._open_selected)
        outer.addWidget(self.table, 1)

        self.empty_lbl = QLabel("No files here yet.")
        self.empty_lbl.setObjectName("DimLabel")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.empty_lbl)

        open_row = QHBoxLayout()
        open_folder_btn = QPushButton("📂 Open Folder in File Manager")
        open_folder_btn.setObjectName("SmallBtn")
        open_folder_btn.clicked.connect(self._open_folder)
        open_row.addWidget(open_folder_btn)
        open_row.addStretch()
        outer.addLayout(open_row)

        self.refresh()

    def set_dir(self, path: str):
        self.dir_edit.setText(path)
        self.current_dir = path
        self.refresh()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder", self.dir_edit.text())
        if folder:
            self.dir_edit.setText(folder)
            self.refresh()

    def refresh(self):
        self.current_dir = self.dir_edit.text().strip()
        self.table.setRowCount(0)
        entries = []
        if self.current_dir and os.path.isdir(self.current_dir):
            try:
                for entry in os.scandir(self.current_dir):
                    if entry.is_file():
                        entries.append(entry)
            except OSError:
                pass
        entries.sort(key=lambda e: e.stat().st_mtime, reverse=True)
        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            ext = Path(entry.name).suffix.lower()
            icon = _KIND_ICON.get(ext, "📄")
            stat = entry.stat()
            self.table.setItem(row, 0, QTableWidgetItem(icon))
            self.table.setItem(row, 1, QTableWidgetItem(entry.name))
            self.table.setItem(row, 2, QTableWidgetItem(_human_size(stat.st_size)))
            import time as _time
            self.table.setItem(row, 3, QTableWidgetItem(_time.strftime("%Y-%m-%d %H:%M", _time.localtime(stat.st_mtime))))
        self.empty_lbl.setVisible(self.table.rowCount() == 0)
        self.table.setVisible(self.table.rowCount() > 0)

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name_item = self.table.item(row, 1)
        if not name_item:
            return
        path = os.path.join(self.current_dir, name_item.text())
        if os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _open_folder(self):
        if os.path.isdir(self.current_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_dir))
