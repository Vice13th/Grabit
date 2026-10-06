"""Session download history.

Populated by :class:`~grabit.gui.main_window.GrabItApp` each time a
download started from either the Grab or Batch page finishes — this page
itself has no knowledge of ``DownloadThread``, keeping the "who owns the
thread" rule from the original architecture intact.
"""
from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from grabit.gui.theme import GREEN, RED


class DownloadsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        title = QLabel("Downloads")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("Everything grabbed this session, newest first.")
        sub.setObjectName("DimLabel")
        outer.addWidget(sub)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Title / URL", "Platform", "Save Folder", "Result"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        outer.addWidget(self.table, 1)

        self.empty_lbl = QLabel("Nothing downloaded yet this session.")
        self.empty_lbl.setObjectName("DimLabel")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.empty_lbl)
        self._sync_empty()

    def add_entry(self, urls: list[str], platform: str, save_dir: str, success: bool):
        self.table.insertRow(0)
        label = urls[0] if len(urls) == 1 else f"{len(urls)} URLs (batch)"
        if len(label) > 70:
            label = label[:67] + "..."
        vals = [time.strftime("%H:%M:%S"), label, platform, save_dir, "✓ Success" if success else "✗ Failed"]
        for c, val in enumerate(vals):
            item = QTableWidgetItem(val)
            if c == 4:
                item.setForeground(Qt.green if success else Qt.red)
            self.table.setItem(0, c, item)
        self._sync_empty()

    def _sync_empty(self):
        self.empty_lbl.setVisible(self.table.rowCount() == 0)
        self.table.setVisible(self.table.rowCount() > 0)
