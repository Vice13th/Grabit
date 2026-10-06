"""Application settings page.

The original script (and the v7 modular rewrite) had no UI for
``AppConfig``'s persisted toggles — ``allow_mirror_fallback``,
``allow_sudo_system_install``, ``concurrent_batch_downloads`` and
``auto_paste_from_clipboard`` could only be edited by hand-editing
``settings.json``. This page is new: it's a straightforward form bound to
the existing :class:`~grabit.config.AppConfig` fields, saved via the same
``AppConfig.save()`` used at shutdown.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from grabit.config import AppConfig
from grabit.gui.anim_widgets import Card


class SettingsPage(QWidget):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        general_card = Card("GENERAL")
        save_row = QHBoxLayout()
        save_row.addWidget(QLabel("Default save folder:"))
        self.save_dir_edit = QLineEdit(str(config.default_save_dir))
        self.save_dir_edit.setReadOnly(True)
        save_row.addWidget(self.save_dir_edit, 1)
        general_card.add(save_row)

        self.cb_auto_paste = QCheckBox("Auto-paste URL from clipboard when the URL field is focused")
        self.cb_auto_paste.setChecked(config.auto_paste_from_clipboard)
        general_card.add(self.cb_auto_paste)

        concurrency_row = QHBoxLayout()
        concurrency_row.addWidget(QLabel("Parallel batch downloads:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 8)
        self.concurrency_spin.setValue(config.concurrent_batch_downloads)
        concurrency_row.addWidget(self.concurrency_spin)
        concurrency_row.addStretch()
        general_card.add(concurrency_row)
        outer.addWidget(general_card)

        security_card = Card("SECURITY")
        note = QLabel(
            "Both options below are off by default. Turning them on trades a little safety "
            "for convenience — see the README's \"Security\" section for details."
        )
        note.setObjectName("DimLabel")
        note.setWordWrap(True)
        security_card.add(note)
        self.cb_mirror = QCheckBox("Allow falling back to third-party PyPI mirrors if the official index fails")
        self.cb_mirror.setChecked(config.allow_mirror_fallback)
        security_card.add(self.cb_mirror)
        self.cb_sudo = QCheckBox("Allow installing ffmpeg via sudo apt-get / brew when no pure-Python wheel exists")
        self.cb_sudo.setChecked(config.allow_sudo_system_install)
        security_card.add(self.cb_sudo)
        outer.addWidget(security_card)

        save_btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("GrabBtn")
        self.save_btn.setFixedHeight(38)
        self.save_btn.clicked.connect(self._save)
        save_btn_row.addWidget(self.save_btn)
        self.saved_lbl = QLabel("")
        self.saved_lbl.setObjectName("DimLabel")
        save_btn_row.addWidget(self.saved_lbl)
        save_btn_row.addStretch()
        outer.addLayout(save_btn_row)
        outer.addStretch()

    def _save(self):
        self.config.auto_paste_from_clipboard = self.cb_auto_paste.isChecked()
        self.config.concurrent_batch_downloads = self.concurrency_spin.value()
        self.config.allow_mirror_fallback = self.cb_mirror.isChecked()
        self.config.allow_sudo_system_install = self.cb_sudo.isChecked()
        self.config.save()
        self.saved_lbl.setText("✓ Saved")
