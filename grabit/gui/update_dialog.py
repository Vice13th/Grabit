"""Update checker/installer tab.

Mirror fallback during "Update All" is gated on
``AppConfig.allow_mirror_fallback``; when it's enabled, each non-official
mirror is still confirmed one at a time via a message box rather than used
silently — see :mod:`grabit.dependencies.manager` for why that matters.
"""
from __future__ import annotations

from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from grabit.config import AppConfig
from grabit.dependencies.updater import check_updates, update_all_packages
from grabit.dependencies.mirrors import Mirror


class UpdateDialog(QWidget):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        title = QLabel("📦 Library Update Checker")
        layout.addWidget(title)
        desc = QLabel("Checking PyPI for latest versions of core engines...\nRegular updates ensure compatibility with changing websites.")
        desc.setStyleSheet("color: #9a9a9a; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text, 1)

        btn_row = QHBoxLayout()
        self.check_btn = QPushButton("🔍 Check for Updates")
        self.check_btn.setObjectName("SmallBtn")
        self.check_btn.clicked.connect(self._check)
        btn_row.addWidget(self.check_btn)
        self.update_btn = QPushButton("⬆ Update All")
        self.update_btn.setObjectName("SmallBtn")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self._update_all)
        btn_row.addWidget(self.update_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._check()

    def _check(self):
        self.results_text.clear()
        self.results_text.append("Checking PyPI for updates...\n")
        QApplication.processEvents()
        updates = check_updates()
        if not updates:
            self.results_text.append("✅ All packages are up to date!")
            self.update_btn.setEnabled(False)
            return
        self.results_text.append(f"Found {len(updates)} update(s):\n")
        for pkg, info in updates.items():
            self.results_text.append(f"  • {pkg}: {info.installed} → {info.latest}")
        self.results_text.append("\nClick 'Update All' to upgrade to latest versions.")
        self.update_btn.setEnabled(True)

    def _confirm_mirror(self, mirror: Mirror) -> bool:
        reply = QMessageBox.question(
            self, "Use third-party mirror?",
            f"The official PyPI index failed. Try the {mirror.name} mirror instead?\n\n"
            f"{mirror.index_url}\n\nOnly do this if you trust this host.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _update_all(self):
        self.results_text.clear()
        self.results_text.append("Updating packages...\n")
        QApplication.processEvents()
        results = update_all_packages(
            allow_mirror_fallback=self.config.allow_mirror_fallback,
            confirm_mirror=self._confirm_mirror if self.config.allow_mirror_fallback else None,
        )
        for pkg, success in results.items():
            icon = "✓" if success else "✗"
            self.results_text.append(f"  {icon} {pkg}")
        self.results_text.append("\n✅ Update complete! Restart GrabIt.")
        self.update_btn.setEnabled(False)
