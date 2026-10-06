"""Logs page: shows the real on-disk log file
(``<data_dir>/logs/grabit.log``, see :mod:`grabit.logging_setup`) and keeps
streaming new lines live via :mod:`grabit.gui.log_bridge`, instead of being
a second, disconnected "engine log"-style widget.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)

from grabit.gui.log_bridge import install as install_log_bridge


class LogsPage(QWidget):
    def __init__(self, log_file: Path, parent=None):
        super().__init__(parent)
        self.log_file = log_file
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("Logs")
        title.setObjectName("PageTitle")
        head.addWidget(title)
        head.addStretch()
        self.path_lbl = QLabel(str(log_file))
        self.path_lbl.setObjectName("FaintLabel")
        head.addWidget(self.path_lbl)
        outer.addLayout(head)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        outer.addWidget(self.view, 1)

        btn_row = QHBoxLayout()
        reload_btn = QPushButton("↺  Reload from disk")
        export_btn = QPushButton("⤓  Export as...")
        clear_btn = QPushButton("🗑  Clear view")
        for b in (reload_btn, export_btn, clear_btn):
            b.setObjectName("SmallBtn")
        reload_btn.clicked.connect(self._reload)
        export_btn.clicked.connect(self._export)
        clear_btn.clicked.connect(lambda: self.view.clear())
        btn_row.addWidget(reload_btn)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        outer.addLayout(btn_row)

        self._reload()
        bridge = install_log_bridge()
        bridge.line_emitted.connect(lambda level, line: self.view.appendPlainText(line))

    def _reload(self):
        try:
            text = self.log_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = "(no log file yet)"
        self.view.setPlainText(text)
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export log", "grabit-log.txt", "Text files (*.txt)")
        if path:
            try:
                Path(path).write_text(self.view.toPlainText(), encoding="utf-8")
            except OSError:
                pass
