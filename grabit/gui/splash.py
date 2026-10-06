"""Animated startup splash screen (world-class polish pass).

Review of the previous version: abrupt show/hide (no fade), an
indeterminate bar paired with messages that weren't tied to real
progress, no depth/shadow against the desktop, and a flat logo with no
breathing motion. This rebuild fixes all four while keeping the same
public API (`set_status`, `finish`) so `grabit.app.main` needs no
structural changes — only real progress calls added.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel, QProgressBar,
    QVBoxLayout, QWidget,
)

from grabit import __version__
from grabit.gui.theme import BG, BORDER, RED, RED_GLOW, TEXT_DIM


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._card_size = (460, 380)
        self.setFixedSize(self._card_size[0] + 60, self._card_size[1] + 60)
        self._center_on_screen()
        self._build_ui()
        self._start_animations()
        self._fade_in()

    def _center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.setGeometry(QRect(x, y, self.width(), self.height()))

    def _build_ui(self):
        cw, ch = self._card_size
        self.card = QWidget(self)
        self.card.setGeometry(30, 30, cw, ch)
        self.card.setStyleSheet(f"background-color: {BG}; border: 1px solid {BORDER}; border-radius: 16px;")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addStretch(3)

        self.logo = QLabel(alignment=Qt.AlignCenter)
        self.logo.setStyleSheet("background: transparent; border: none;")
        logo_pix = QPixmap(str(Path(__file__).parent / "assets" / "logo.png"))
        if not logo_pix.isNull():
            self.logo.setPixmap(logo_pix.scaledToHeight(130, Qt.SmoothTransformation))
        self._logo_glow = QGraphicsDropShadowEffect(self.logo)
        self._logo_glow.setColor(QColor(RED_GLOW))
        self._logo_glow.setBlurRadius(20)
        self._logo_glow.setOffset(0, 0)
        self.logo.setGraphicsEffect(self._logo_glow)
        lay.addWidget(self.logo)
        lay.addSpacing(18)

        self.tagline = QLabel("F A S T   /   S M A R T   /   U N I V E R S A L", alignment=Qt.AlignCenter)
        self.tagline.setStyleSheet(f"color: {RED_GLOW}; font-size: 10px; font-weight: 700; letter-spacing: 2px; background: transparent; border: none;")
        lay.addWidget(self.tagline)
        lay.addStretch(3)

        self.status_lbl = QLabel("Starting up...", alignment=Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-family: 'JetBrains Mono', monospace; font-size: 11px; background: transparent; border: none;")
        lay.addWidget(self.status_lbl)
        lay.addSpacing(10)

        bar_wrap = QWidget()
        bar_wrap.setStyleSheet("background: transparent; border: none;")
        bar_lay = QVBoxLayout(bar_wrap)
        bar_lay.setContentsMargins(60, 0, 60, 6)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(4)
        self.bar.setStyleSheet(
            f"QProgressBar {{ background-color: #16161a; border: none; border-radius: 2px; }}"
            f"QProgressBar::chunk {{ background-color: {RED}; border-radius: 2px; }}"
        )
        bar_lay.addWidget(self.bar)
        self.pct_lbl = QLabel("0%", alignment=Qt.AlignCenter)
        self.pct_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-family: 'JetBrains Mono', monospace; font-size: 9px; background: transparent; border: none;")
        bar_lay.addWidget(self.pct_lbl)
        lay.addWidget(bar_wrap)

        self.ver_lbl = QLabel(f"v{__version__} · Modular Edition", alignment=Qt.AlignCenter)
        self.ver_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent; border: none;")
        lay.addWidget(self.ver_lbl)
        lay.addSpacing(14)

        self._bar_anim = QPropertyAnimation(self.bar, b"value", self)
        self._bar_anim.setDuration(400)
        self._bar_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _start_animations(self):
        self._pulse = QPropertyAnimation(self._logo_glow, b"blurRadius", self)
        self._pulse.setDuration(1400)
        self._pulse.setKeyValueAt(0.0, 14)
        self._pulse.setKeyValueAt(0.5, 32)
        self._pulse.setKeyValueAt(1.0, 14)
        self._pulse.setLoopCount(-1)
        self._pulse.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse.start()

    def _fade_in(self):
        self._card_opacity = QGraphicsOpacityEffect(self)
        # Card already owns the shadow effect; fade the whole splash window
        # via the widget's windowOpacity instead so both stack cleanly.
        self.setWindowOpacity(0.0)
        self.show()
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(260)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.start()

    def set_status(self, text: str, progress: int | None = None):
        self.status_lbl.setText(text)
        if progress is not None:
            self._bar_anim.stop()
            self._bar_anim.setStartValue(self.bar.value())
            self._bar_anim.setEndValue(max(0, min(100, progress)))
            self._bar_anim.start()
            self.pct_lbl.setText(f"{max(0, min(100, progress))}%")

    def finish(self, target_window):
        self.set_status("Ready", 100)
        self._pulse.stop()

        def _swap():
            target_window.setWindowOpacity(0.0)
            target_window.show()
            fade_in = QPropertyAnimation(target_window, b"windowOpacity", target_window)
            fade_in.setDuration(220)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutCubic)
            fade_in.start()
            target_window._splash_fade_in = fade_in  # keep alive
            self.close()
            self.deleteLater()

        fade_out = QPropertyAnimation(self, b"windowOpacity", self)
        fade_out.setDuration(260)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(_swap)
        fade_out.start()
        self._fade_out = fade_out  # keep alive
