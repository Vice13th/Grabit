"""Animated building blocks used across the redesigned GUI.

Kept separate from ``widgets.py`` (which holds the original, behavior-only
``ClipboardAwareLineEdit``) so the purely decorative/animated pieces added
for the v8 redesign are easy to find and don't get mixed up with logic that
existing tabs depend on.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup,
    Qt, Signal,
)
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget,
)

from grabit.gui.theme import BORDER, GREEN, RED, RED_DIM, TEXT_DIM, YELLOW


# ---------------------------------------------------------------------------
# Status dot: a small circle that pulses (opacity breathing) when "live".
# ---------------------------------------------------------------------------
class StatusDot(QWidget):
    COLORS = {"idle": TEXT_DIM, "ok": GREEN, "warn": YELLOW, "error": RED, "active": RED}

    def __init__(self, state: str = "idle", diameter: int = 9, parent=None):
        super().__init__(parent)
        self._diameter = diameter
        self._opacity = 1.0
        self._color = QColor(self.COLORS.get(state, TEXT_DIM))
        self.setFixedSize(diameter, diameter)
        self._anim = QPropertyAnimation(self, b"opacity", self)
        self._anim.setDuration(900)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.25)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._loop = QSequentialAnimationGroup(self)
        self._loop.addAnimation(self._anim)
        rev = QPropertyAnimation(self, b"opacity", self)
        rev.setDuration(900)
        rev.setStartValue(0.25)
        rev.setEndValue(1.0)
        rev.setEasingCurve(QEasingCurve.InOutSine)
        self._loop.addAnimation(rev)
        self._loop.setLoopCount(-1)
        self.set_state(state)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, v):
        self._opacity = v
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def set_state(self, state: str, pulsing: bool | None = None):
        self._color = QColor(self.COLORS.get(state, TEXT_DIM))
        should_pulse = state in ("active",) if pulsing is None else pulsing
        if should_pulse:
            if self._loop.state() != QPropertyAnimation.Running:
                self._loop.start()
        else:
            self._loop.stop()
            self._opacity = 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, self._diameter, self._diameter)


def status_row(state: str, text: str, mono: bool = True) -> QWidget:
    """A small [dot] + label row, used all over the system-status panel."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(7)
    dot = StatusDot(state)
    lay.addWidget(dot, 0, Qt.AlignVCenter)
    lbl = QLabel(text)
    lbl.setObjectName("MonoValue" if mono else "DimLabel")
    lay.addWidget(lbl)
    lay.addStretch()
    w._dot = dot  # type: ignore[attr-defined]
    w._label = lbl  # type: ignore[attr-defined]
    return w


# ---------------------------------------------------------------------------
# Glow progress bar: normal QProgressBar + animated drop-shadow glow that
# intensifies while downloading, so activity reads at a glance.
# ---------------------------------------------------------------------------
class GlowProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setColor(QColor(RED))
        self._glow.setOffset(0, 0)
        self._glow.setBlurRadius(0)
        self.setGraphicsEffect(self._glow)
        self._anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._anim.setDuration(1100)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)

    def set_active(self, active: bool):
        self._anim.stop()
        if active:
            self._anim.setStartValue(4)
            self._anim.setEndValue(18)
            self._anim.setLoopCount(-1)
            group = QSequentialAnimationGroup(self)
            # QPropertyAnimation alone can't ping-pong without a group; use
            # setKeyValueAt instead for a lightweight back-and-forth.
            self._anim.setKeyValueAt(0.0, 4)
            self._anim.setKeyValueAt(0.5, 18)
            self._anim.setKeyValueAt(1.0, 4)
            self._anim.setDuration(1400)
            self._anim.setLoopCount(-1)
            self._anim.start()
        else:
            self._glow.setBlurRadius(0)


# ---------------------------------------------------------------------------
# Pipeline step: one node in the "auto-detecting source" row.
# ---------------------------------------------------------------------------
class PipelineStep(QFrame):
    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("PipelineStep")
        self.setProperty("done", False)
        self.setFixedHeight(58)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        icon_wrap = QLabel(icon)
        icon_wrap.setFixedWidth(22)
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setStyleSheet(f"font-size: 15px; color: {TEXT_DIM};")
        self._icon_lbl = icon_wrap
        lay.addWidget(icon_wrap)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("FaintLabel")
        text_col.addWidget(self.title_lbl)
        self.value_lbl = QLabel("—")
        self.value_lbl.setObjectName("MonoValue")
        self.value_lbl.setStyleSheet("font-size: 12px; font-weight: 700;")
        text_col.addWidget(self.value_lbl)
        lay.addLayout(text_col, 1)

        self.check_lbl = QLabel("")
        self.check_lbl.setFixedWidth(16)
        self.check_lbl.setStyleSheet(f"color: {GREEN}; font-weight: 900; font-size: 13px;")
        lay.addWidget(self.check_lbl)

        self._op_effect = QGraphicsDropShadowEffect(self)
        self._op_effect.setColor(QColor(RED_DIM))
        self._op_effect.setBlurRadius(0)
        self._op_effect.setOffset(0, 0)
        self.setGraphicsEffect(self._op_effect)
        self._glow_anim = QPropertyAnimation(self._op_effect, b"blurRadius", self)
        self._glow_anim.setDuration(420)
        self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)

    def set_value(self, value: str, done: bool = True):
        self.value_lbl.setText(value)
        was_done = self.property("done")
        self.setProperty("done", done)
        self.style().unpolish(self)
        self.style().polish(self)
        self.check_lbl.setText("✓" if done else "")
        if done and not was_done:
            self._glow_anim.stop()
            self._glow_anim.setStartValue(0)
            self._glow_anim.setKeyValueAt(0.5, 16)
            self._glow_anim.setEndValue(0)
            self._glow_anim.start()

    def reset(self):
        self.value_lbl.setText("—")
        self.setProperty("done", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.check_lbl.setText("")


# ---------------------------------------------------------------------------
# Card: a titled panel ("// SECTION TITLE" header + content body).
# ---------------------------------------------------------------------------
class Card(QFrame):
    def __init__(self, title: str = "", parent=None, alt: bool = False):
        super().__init__(parent)
        self.setObjectName("CardAlt" if alt else "Card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(10)
        if title:
            head = QLabel(f"//  {title}")
            head.setObjectName("SectionTitle")
            outer.addWidget(head)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body)
        self._outer = outer

    def add(self, widget_or_layout):
        if isinstance(widget_or_layout, QWidget):
            self.body.addWidget(widget_or_layout)
        else:
            self.body.addLayout(widget_or_layout)


class FadeStackWidget(QWidget):
    """Wraps a widget with a fade-in opacity animation, triggered by
    calling ``refresh()`` — used for small "content just changed" cues
    (e.g. platform detected) without importing QGraphicsOpacityEffect
    boilerplate at every call site."""

    def __init__(self, inner: QWidget, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(inner)
        self._effect = QGraphicsOpacityEffect(inner)
        inner.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(320)
        self._anim.setStartValue(0.25)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def refresh(self):
        self._anim.stop()
        self._anim.start()


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
class Sidebar(QFrame):
    page_changed = Signal(str)

    ITEMS = [
        ("grab", "⌂", "Grab"),
        ("search", "🔍", "Search"),
        ("batch", "▤", "Batch"),
        ("downloads", "⬇", "Downloads"),
        ("studio", "▣", "Media Studio"),
        ("engines", "◈", "Engines"),
        ("settings", "⚙", "Settings"),
        ("updates", "⟳", "Updates"),
        ("logs", "≣", "Logs"),
        ("about", "ⓘ", "About"),
    ]

    def __init__(self, version_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.setSpacing(8)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        logo = QLabel()
        logo_pix = QPixmap(str(Path(__file__).parent / "assets" / "logo.png"))
        if not logo_pix.isNull():
            logo.setPixmap(logo_pix.scaledToHeight(26, Qt.SmoothTransformation))
        brand_row.addWidget(logo)
        title = QLabel("Grab<span style='color:%s;'>It</span>" % RED)
        title.setTextFormat(Qt.RichText)
        title.setObjectName("BrandTitle")
        title.setStyleSheet("font-size: 17px;")
        brand_row.addWidget(title)
        brand_row.addStretch()
        lay.addLayout(brand_row)
        lay.addSpacing(4)

        self.list = QListWidget()
        self.list.setObjectName("NavList")
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setFocusPolicy(Qt.NoFocus)
        for key, icon, label in self.ITEMS:
            item = QListWidgetItem(f"  {icon}   {label}")
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.currentItemChanged.connect(self._on_change)
        lay.addWidget(self.list, 1)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        lay.addWidget(divider)
        lay.addSpacing(4)

        ver = QLabel(version_text)
        ver.setObjectName("FaintLabel")
        lay.addWidget(ver)
        tagline = QLabel('"Grab from anywhere,\nto everywhere."')
        tagline.setWordWrap(True)
        tagline.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic; font-size: 11px;")
        lay.addWidget(tagline)

    def _on_change(self, current, previous):
        if current is not None:
            self.page_changed.emit(current.data(Qt.UserRole))

    def select(self, key: str):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == key:
                self.list.setCurrentRow(i)
                return
