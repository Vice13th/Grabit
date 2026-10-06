"""Small reusable widgets."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QLineEdit

from grabit.core.url_utils import is_valid_url


class ClipboardAwareLineEdit(QLineEdit):
    """A ``QLineEdit`` that auto-fills itself from the clipboard on first
    click/focus if it looks like a valid, safely-short URL and the field is
    currently empty."""

    url_pasted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_paste_enabled = True
        self.setToolTip("Click to auto-paste URL from clipboard")

    def _try_auto_paste(self) -> bool:
        if not self._auto_paste_enabled:
            return False
        if self.text().strip():
            return False
        try:
            clipboard = QApplication.clipboard()
            text = (clipboard.text() or "").strip()
        except Exception:
            return False
        if text and is_valid_url(text) and len(text) < 2048:
            self.setText(text)
            self.selectAll()
            self.url_pasted.emit(text)
            return True
        return False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._try_auto_paste():
            event.accept()
            return
        super().mousePressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._try_auto_paste()

    def enable_auto_paste(self, enabled: bool):
        self._auto_paste_enabled = bool(enabled)
