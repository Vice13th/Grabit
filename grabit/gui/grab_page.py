"""The 'Grab' page — redesigned single-URL download screen.

Functionally this replaces :class:`grabit.gui.single_tab.SingleDownloadTab`
(same public signals/slots so :class:`~grabit.gui.main_window.GrabItApp`
wires it identically), but the layout, visuals and a few UX additions
(pipeline visualization, detected-platform panel, quick actions, live
engine log, system status, session queue) follow the reference design.
"""
from __future__ import annotations

import os
import shutil
import socket
import time

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from grabit.core.models import DownloadOptions, RouteDecision
from grabit.core.router import SmartRouter
from grabit.core.url_utils import is_valid_url
from grabit.gui.anim_widgets import Card, GlowProgressBar, PipelineStep, status_row
from grabit.gui.engine_meta import features_for
from grabit.gui.log_bridge import QtLogBridge, install as install_log_bridge
from grabit.gui.settings_panel import SettingsPanel
from grabit.gui.theme import BORDER, GREEN, RED, RED_GLOW, TEXT_DIM, YELLOW
from grabit.gui.widgets import ClipboardAwareLineEdit
from grabit.workers.playlist_probe_thread import PlaylistProbeThread

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional
    psutil = None


class _NetCheckThread(QThread):
    """Runs the blocking connectivity probe off the GUI thread — see the
    comment in GrabPage._refresh_system_status for why this exists."""
    result = Signal(bool)

    def run(self):
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=1.2).close()
            self.result.emit(True)
        except OSError:
            self.result.emit(False)


class GrabPage(QWidget):
    start_requested = Signal(str, str, object)  # url, save_dir, DownloadOptions
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, default_save_dir: str, optional_status: dict, parent=None):
        super().__init__(parent)
        self.optional_status = optional_status
        self.current_decision: RouteDecision | None = None
        self.last_save_dir = ""
        self._busy = False
        self._pending_download = None
        self.playlist_probe: PlaylistProbeThread | None = None
        self._net_check_thread: _NetCheckThread | None = None
        self._queue_row_index: int | None = None
        self._start_time: float | None = None
        self._build_ui(default_save_dir)
        self._log_bridge = install_log_bridge()
        self._log_bridge.line_emitted.connect(self._on_log_line)
        self._refresh_system_status()

    # -- UI ------------------------------------------------------------
    def _build_ui(self, default_save_dir: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(14)
        right = QVBoxLayout()
        right.setSpacing(14)

        outer.addLayout(left, 2)
        outer.addLayout(right, 1)

        # -- GRAB NEW MEDIA -------------------------------------------------
        grab_card = Card("GRAB NEW MEDIA")
        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_entry = ClipboardAwareLineEdit()
        self.url_entry.setPlaceholderText("Paste a URL (page or direct file) and press Enter, or hit Grab It")
        self.url_entry.setFixedHeight(42)
        self.url_entry.textChanged.connect(self._on_url_changed)
        self.url_entry.returnPressed.connect(self._on_enter_pressed)
        self.url_entry.url_pasted.connect(self._on_url_pasted)
        url_row.addWidget(self.url_entry, 1)

        self.download_btn = QPushButton("[  GRAB IT  ]")
        self.download_btn.setObjectName("GrabBtn")
        self.download_btn.setFixedHeight(42)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._start_download)
        url_row.addWidget(self.download_btn)
        grab_card.add(url_row)

        self.detect_status_lbl = QLabel("WAITING FOR URL...")
        self.detect_status_lbl.setObjectName("FaintLabel")
        self.detect_status_lbl.setStyleSheet(f"letter-spacing: 1px; color: {TEXT_DIM}; font-family: 'JetBrains Mono', monospace; font-size: 10px;")
        grab_card.add(self.detect_status_lbl)

        pipeline_row = QHBoxLayout()
        pipeline_row.setSpacing(6)
        self.step_url = PipelineStep("🔗", "URL")
        self.step_platform = PipelineStep("◆", "PLATFORM")
        self.step_engine = PipelineStep("⚙", "ENGINE")
        self.step_kind = PipelineStep("▣", "MEDIA TYPE")
        self.step_output = PipelineStep("⤓", "OUTPUT")
        for i, step in enumerate([self.step_url, self.step_platform, self.step_engine, self.step_kind, self.step_output]):
            pipeline_row.addWidget(step, 1)
            if i < 4:
                arrow = QLabel("→")
                arrow.setStyleSheet(f"color: {BORDER}; font-size: 14px;")
                pipeline_row.addWidget(arrow)
        grab_card.add(pipeline_row)
        left.addWidget(grab_card)

        # -- MEDIA OPTIONS ----------------------------------------------
        opts_card = Card("MEDIA OPTIONS")
        opts_row = QHBoxLayout()
        opts_row.setSpacing(14)

        opts_col = QVBoxLayout()
        opts_col.setSpacing(10)
        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        self._type_buttons = {}
        for key, label in (("video", "🎬  Video"), ("audio", "🎵  Audio"), ("image", "🖼  Image"), ("file", "📄  File")):
            btn = QPushButton(label)
            btn.setObjectName("MediaTypeBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked, k=key: self._on_type_clicked(k))
            self.type_group.addButton(btn)
            self._type_buttons[key] = btn
        self._type_buttons["video"].setChecked(True)
        for b in self._type_buttons.values():
            type_row.addWidget(b)
        opts_col.addLayout(type_row)

        self.settings_panel = SettingsPanel()
        opts_col.addWidget(self.settings_panel)

        path_label = QLabel("Save to:")
        path_label.setObjectName("FieldLabel")
        opts_col.addWidget(path_label)
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_entry = QLineEdit()
        self.path_entry.setText(default_save_dir)
        self.path_entry.setFixedHeight(38)
        path_row.addWidget(self.path_entry, 1)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("BrowseBtn")
        self.browse_btn.setFixedHeight(38)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(self.browse_btn)
        opts_col.addLayout(path_row)
        opts_row.addLayout(opts_col, 1)

        preview_col = QVBoxLayout()
        preview_col.setSpacing(6)
        self.preview_thumb = QLabel("🎞")
        self.preview_thumb.setFixedSize(220, 130)
        self.preview_thumb.setAlignment(Qt.AlignCenter)
        self.preview_thumb.setStyleSheet(
            f"background-color: #16161a; border: 1px solid {BORDER}; border-radius: 10px; font-size: 34px; color: {TEXT_DIM};"
        )
        preview_col.addWidget(self.preview_thumb)
        self.preview_title = QLabel("No media selected")
        self.preview_title.setWordWrap(True)
        self.preview_title.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 13px;")
        preview_col.addWidget(self.preview_title)
        self.preview_meta = QLabel("")
        self.preview_meta.setObjectName("DimLabel")
        self.preview_meta.setWordWrap(True)
        preview_col.addWidget(self.preview_meta)
        preview_col.addStretch()
        opts_row.addLayout(preview_col)
        opts_card.add(opts_row)
        left.addWidget(opts_card)

        # -- DOWNLOAD PROGRESS --------------------------------------------
        prog_card = Card("DOWNLOAD PROGRESS")
        prog_top = QHBoxLayout()
        prog_top.setSpacing(12)
        self.prog_thumb = QLabel("⬇")
        self.prog_thumb.setFixedSize(70, 70)
        self.prog_thumb.setAlignment(Qt.AlignCenter)
        self.prog_thumb.setStyleSheet(
            f"background-color: #16161a; border: 1px solid {BORDER}; border-radius: 8px; font-size: 22px; color: {TEXT_DIM};"
        )
        prog_top.addWidget(self.prog_thumb)
        prog_info = QVBoxLayout()
        prog_info.setSpacing(2)
        self.prog_title = QLabel("Nothing downloading yet")
        self.prog_title.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 14px;")
        prog_info.addWidget(self.prog_title)
        self.prog_sub = QLabel("Paste a URL above to get started")
        self.prog_sub.setObjectName("DimLabel")
        prog_info.addWidget(self.prog_sub)
        prog_top.addLayout(prog_info, 1)
        prog_card.add(prog_top)

        bar_row = QHBoxLayout()
        bar_row.setSpacing(10)
        self.progress_bar = GlowProgressBar()
        bar_row.addWidget(self.progress_bar, 1)
        self.progress_pct = QLabel("0%")
        self.progress_pct.setStyleSheet(f"color: {RED_GLOW}; font-weight: 800; font-family: 'JetBrains Mono', monospace; font-size: 13px;")
        self.progress_pct.setFixedWidth(44)
        bar_row.addWidget(self.progress_pct)
        prog_card.add(bar_row)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        prog_card.add(self.status_label)

        control_row = QHBoxLayout()
        control_row.setSpacing(8)
        self.pause_btn = QPushButton("⏸ Pause")
        self.resume_btn = QPushButton("▶ Resume")
        self.cancel_btn = QPushButton("✕ Cancel")
        self.open_folder_btn = QPushButton("📂 Open Folder")
        for btn, name in ((self.pause_btn, "SmallBtn"), (self.resume_btn, "SmallBtn"),
                          (self.cancel_btn, "SmallBtn"), (self.open_folder_btn, "OpenFolderBtn")):
            btn.setObjectName(name)
            btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.open_folder_btn.setVisible(False)
        self.pause_btn.clicked.connect(self.pause_requested.emit)
        self.resume_btn.clicked.connect(self.resume_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.open_folder_btn.clicked.connect(self._open_save_folder)
        control_row.addWidget(self.pause_btn)
        control_row.addWidget(self.resume_btn)
        control_row.addWidget(self.cancel_btn)
        control_row.addStretch()
        control_row.addWidget(self.open_folder_btn)
        prog_card.add(control_row)
        left.addWidget(prog_card)

        # -- DOWNLOAD QUEUE -------------------------------------------------
        queue_card = Card("DOWNLOAD QUEUE (SESSION)")
        self.queue_table = QTableWidget(0, 6)
        self.queue_table.setHorizontalHeaderLabels(["#", "Title", "Platform", "Type", "Status", "Progress"])
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setShowGrid(False)
        self.queue_table.setSelectionMode(QTableWidget.NoSelection)
        self.queue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.queue_table.setFixedHeight(140)
        header = self.queue_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (0, 2, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        queue_card.add(self.queue_table)
        left.addWidget(queue_card)
        left.addStretch()

        # ===================== RIGHT COLUMN ================================
        detect_card = Card("DETECTED PLATFORM")
        plat_row = QHBoxLayout()
        self.platform_icon = QLabel("❓")
        self.platform_icon.setFixedSize(34, 34)
        self.platform_icon.setAlignment(Qt.AlignCenter)
        self.platform_icon.setStyleSheet(f"background-color: #16161a; border-radius: 8px; font-size: 16px; border: 1px solid {BORDER};")
        plat_row.addWidget(self.platform_icon)
        self.platform_name = QLabel("Unknown")
        self.platform_name.setStyleSheet("font-weight: 800; color: #ffffff; font-size: 15px;")
        plat_row.addWidget(self.platform_name, 1)
        self.detected_badge = QLabel("")
        self.detected_badge.setObjectName("PlatformBadge")
        self.detected_badge.setStyleSheet(f"color: {GREEN}; border: 1px solid {GREEN}; background-color: transparent; font-size: 10px;")
        plat_row.addWidget(self.detected_badge)
        detect_card.add(plat_row)

        self.detect_grid = QGridLayout()
        self.detect_grid.setHorizontalSpacing(10)
        self.detect_grid.setVerticalSpacing(6)
        self._detect_value_labels = {}
        for r, key in enumerate(["URL", "Engine", "Media Type", "Quality", "Format", "Features"]):
            k = QLabel(key)
            k.setObjectName("MonoKey")
            v = QLabel("—")
            v.setObjectName("MonoValue")
            v.setWordWrap(True)
            self.detect_grid.addWidget(k, r, 0, Qt.AlignTop)
            self.detect_grid.addWidget(v, r, 1)
            self._detect_value_labels[key] = v
        self.detect_grid.setColumnStretch(1, 1)
        detect_card.add(self.detect_grid)
        right.addWidget(detect_card)

        quick_card = Card("QUICK ACTIONS")
        qa_grid = QGridLayout()
        qa_grid.setSpacing(8)
        paste_btn = QPushButton("📋  Paste from Clipboard")
        open_btn = QPushButton("🔗  Open URL")
        save_btn = QPushButton("📁  Save to...")
        reset_btn = QPushButton("↺  Reset")
        for b in (paste_btn, open_btn, save_btn, reset_btn):
            b.setObjectName("QuickActionBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(38)
        paste_btn.clicked.connect(self._quick_paste)
        open_btn.clicked.connect(self._quick_open_url)
        save_btn.clicked.connect(self._browse_folder)
        reset_btn.clicked.connect(self._quick_reset)
        qa_grid.addWidget(paste_btn, 0, 0)
        qa_grid.addWidget(open_btn, 0, 1)
        qa_grid.addWidget(save_btn, 1, 0)
        qa_grid.addWidget(reset_btn, 1, 1)
        quick_card.add(qa_grid)
        right.addWidget(quick_card)

        log_card = Card("ENGINE LOG")
        log_head = QHBoxLayout()
        log_head.addStretch()
        copy_btn = QPushButton("⧉")
        clear_btn = QPushButton("🗑")
        for b in (copy_btn, clear_btn):
            b.setObjectName("IconBtn")
            b.setFixedSize(26, 26)
            b.setCursor(Qt.PointingHandCursor)
        copy_btn.setToolTip("Copy log")
        clear_btn.setToolTip("Clear log")
        copy_btn.clicked.connect(self._copy_log)
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        log_head.addWidget(copy_btn)
        log_head.addWidget(clear_btn)
        log_card.add(log_head)
        from PySide6.QtWidgets import QPlainTextEdit
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(170)
        self.log_view.setPlaceholderText("Engine activity will appear here...")
        log_card.add(self.log_view)
        right.addWidget(log_card)

        status_card = Card("SYSTEM STATUS")
        self._status_rows = {}
        for key, initial_state, initial_text in (
            ("active", "idle", "Active Downloads: 0"),
            ("engine", "ok", "Engine Status: Ready"),
            ("net", "ok", "Internet: Connected"),
        ):
            row = status_row(initial_state, initial_text)
            self._status_rows[key] = row
            status_card.add(row)
        self.disk_lbl = QLabel("Disk Space: —")
        self.disk_lbl.setObjectName("DimLabel")
        status_card.add(self.disk_lbl)
        self.sys_lbl = QLabel("CPU — · RAM — ")
        self.sys_lbl.setObjectName("DimLabel")
        status_card.add(self.sys_lbl)
        self.version_lbl = QLabel("Version: v7.0 (Modular · GUI v8)")
        self.version_lbl.setObjectName("FaintLabel")
        status_card.add(self.version_lbl)
        right.addWidget(status_card)
        right.addStretch()

    # -- URL handling ---------------------------------------------------
    def _on_url_changed(self, text: str):
        text = text.strip()
        if not text or not is_valid_url(text):
            self.current_decision = None
            self._reset_pipeline()
            self.settings_panel.set_engine(None, None)
            self.detect_status_lbl.setText("WAITING FOR URL...")
            return
        self.detect_status_lbl.setText("AUTO-DETECTING SOURCE...")
        decision = SmartRouter.route(text, self.optional_status)
        self.current_decision = decision
        self.settings_panel.set_engine(decision.engine, decision.kind)
        self._sync_type_buttons(decision.kind)
        self._apply_pipeline(text, decision)
        self._apply_detect_panel(text, decision)
        if decision.is_known:
            self.detect_status_lbl.setText(f"SOURCE DETECTED — ROUTED TO {decision.engine.upper()}")
        else:
            self.detect_status_lbl.setText("UNRECOGNIZED SOURCE — WILL TRY GENERIC FETCH")

    def _reset_pipeline(self):
        for step in (self.step_url, self.step_platform, self.step_engine, self.step_kind, self.step_output):
            step.reset()
        self.platform_icon.setText("❓")
        self.platform_name.setText("Unknown")
        self.detected_badge.setText("")
        for v in self._detect_value_labels.values():
            v.setText("—")

    def _apply_pipeline(self, url: str, decision: RouteDecision):
        self.step_url.set_value("Received", True)
        self.step_platform.set_value(decision.platform, decision.is_known)
        self.step_engine.set_value(decision.engine or "—", decision.is_known)
        self.step_kind.set_value((decision.kind or "—").title(), decision.is_known)
        self.step_output.set_value(self._output_summary(decision), decision.is_known)

    def _output_summary(self, decision: RouteDecision) -> str:
        if decision.kind == "audio":
            return "MP3 / best"
        if decision.kind == "image":
            return "Original res."
        if decision.kind == "file":
            return "As-is"
        return "MP4 / 1080p"

    def _apply_detect_panel(self, url: str, decision: RouteDecision):
        self.platform_icon.setText(decision.icon or "❓")
        self.platform_name.setText(decision.platform)
        self.detected_badge.setText("Detected" if decision.is_known else "Unsupported")
        self.detected_badge.setStyleSheet(
            "color: {c}; border: 1px solid {c}; background-color: transparent; font-size: 10px; padding: 4px 10px;".format(
                c=GREEN if decision.is_known else YELLOW
            )
        )
        shortened = url if len(url) <= 46 else url[:43] + "..."
        self._detect_value_labels["URL"].setText(shortened)
        eng_txt = decision.engine or "—"
        self._detect_value_labels["Engine"].setText(eng_txt + ("  (Available)" if decision.is_known else ""))
        self._detect_value_labels["Media Type"].setText((decision.kind or "—").title())
        self._detect_value_labels["Quality"].setText("1080p (Best)" if decision.kind == "video" else "Best available")
        self._detect_value_labels["Format"].setText({"video": "MP4", "audio": "MP3", "image": "Original", "file": "Original"}.get(decision.kind, "—"))
        self._detect_value_labels["Features"].setText(features_for(decision.engine))

    def _sync_type_buttons(self, kind: str | None):
        if kind in self._type_buttons:
            self._type_buttons[kind].setChecked(True)

    def _on_type_clicked(self, key: str):
        if self.current_decision and self.current_decision.engine == "yt-dlp":
            if hasattr(self.settings_panel, "video_mode_combo"):
                self.settings_panel.video_mode_combo.setCurrentIndex(1 if key == "audio" else 0)

    def _on_enter_pressed(self):
        if not self._busy:
            self._start_download()

    def _on_url_pasted(self, url: str):
        self.set_status("📋 URL pasted from clipboard — press Enter to download", "#3ddc84")

    def _quick_paste(self):
        text = (QApplication.clipboard().text() or "").strip()
        if text:
            self.url_entry.setText(text)
            self.url_entry.selectAll()

    def _quick_open_url(self):
        url = self.url_entry.text().strip()
        if url and is_valid_url(url):
            QDesktopServices.openUrl(QUrl(url))

    def _quick_reset(self):
        self.url_entry.clear()
        self._reset_pipeline()
        self.detect_status_lbl.setText("WAITING FOR URL...")
        self.preview_title.setText("No media selected")
        self.preview_meta.setText("")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.path_entry.text())
        if folder:
            self.path_entry.setText(folder)

    def _open_save_folder(self):
        if self.last_save_dir and os.path.isdir(self.last_save_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_save_dir))

    def _copy_log(self):
        QApplication.clipboard().setText(self.log_view.toPlainText())

    def _on_log_line(self, level: str, line: str):
        self.log_view.appendPlainText(line)

    # -- download lifecycle ----------------------------------------------
    def _start_download(self):
        if self._busy:
            return
        url = self.url_entry.text().strip()
        if not url:
            self.set_status("⚠ Please enter a media URL", "#ffb84d")
            return
        if not is_valid_url(url):
            self.set_status("⚠ Invalid URL format", "#ffb84d")
            return
        if not self.current_decision:
            self.current_decision = SmartRouter.route(url, self.optional_status)
        save_dir = self.path_entry.text().strip()
        if not save_dir:
            self.set_status("⚠ Please select a save folder", "#ffb84d")
            return
        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            self.set_status(f"✗ Cannot create folder: {e}", "#ff3b3b")
            return

        options = self.settings_panel.get_options()
        if self._is_youtube_playlist_candidate(url):
            self._begin_playlist_probe(url, save_dir, options)
            return
        self._launch(url, save_dir, options)

    @staticmethod
    def _is_youtube_url(url: str) -> bool:
        import re
        return bool(re.search(r"(?:youtube\.com|youtu\.be)", (url or "").lower()))

    @classmethod
    def _is_youtube_playlist_candidate(cls, url: str) -> bool:
        value = (url or "").lower()
        return cls._is_youtube_url(value) and ("list=" in value or "/playlist" in value)

    def _begin_playlist_probe(self, url: str, save_dir: str, options: DownloadOptions):
        self._busy = True
        self._pending_download = (url, save_dir, options)
        self._set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.set_status("🔎 Checking YouTube playlist...", "#8a8a90")
        self.playlist_probe = PlaylistProbeThread(url, parent=self)
        self.playlist_probe.finished_probe.connect(self._on_playlist_probe_finished)
        self.playlist_probe.finished.connect(self._on_playlist_probe_thread_finished)
        self.playlist_probe.start()

    def _on_playlist_probe_finished(self, is_playlist, count, title, playlist_only, error):
        if error:
            self._busy = False
            self._set_ui_enabled(True)
            QMessageBox.warning(self, "YouTube playlist check",
                                 f"Could not inspect the playlist.\n\n{error}\n\nThe download was not started.")
            return
        pending = self._pending_download
        if not pending:
            self._busy = False
            self._set_ui_enabled(True)
            return
        url, save_dir, options = pending
        if not is_playlist:
            self._busy = False
            self._set_ui_enabled(True)
            self._launch(url, save_dir, options)
            return
        count_text = f"{count} item(s)" if count else "multiple items"
        box = QMessageBox(self)
        box.setWindowTitle("YouTube playlist detected")
        box.setText(f"This link contains a YouTube playlist.\n\n{title}\n{count_text}\n\nDownload the entire playlist?")
        box.setInformativeText("Choose No to download only the selected video when the URL points to one.")
        yes = box.addButton("Download Playlist", QMessageBox.YesRole)
        no = box.addButton("Selected Video Only", QMessageBox.NoRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is yes:
            options.playlist_mode = "yes"
        elif clicked is no and not playlist_only:
            options.playlist_mode = "no"
        else:
            self._busy = False
            self._set_ui_enabled(True)
            return
        self._launch(url, save_dir, options)

    def _on_playlist_probe_thread_finished(self):
        if self.playlist_probe is not None:
            self.playlist_probe.deleteLater()
            self.playlist_probe = None

    def _launch(self, url: str, save_dir: str, options: DownloadOptions):
        self._busy = True
        self._start_time = time.time()
        self.last_save_dir = save_dir
        self._set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.set_active(True)
        self.progress_pct.setText("0%")
        self.open_folder_btn.setVisible(False)
        self.set_controls(running=True, paused=False)
        self.set_status("⏳ Starting download...", "#8a8a90")
        decision = self.current_decision
        title = url if len(url) < 60 else url[:57] + "..."
        self.prog_title.setText(title)
        platform = decision.platform if decision else "Unknown"
        engine = decision.engine if decision else "—"
        self.prog_sub.setText(f"{platform} · {engine}")
        self._status_rows["active"]._label.setText("Active Downloads: 1")
        self._status_rows["active"]._dot.set_state("active")
        self._status_rows["engine"]._label.setText(f"Engine: {engine} Busy")
        self._add_queue_row(title, platform, (decision.kind if decision else "file") or "file")
        self.start_requested.emit(url, save_dir, options)

    def _set_ui_enabled(self, enabled: bool):
        self.url_entry.setEnabled(enabled)
        self.path_entry.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
        self.settings_panel.setEnabled(enabled)
        for b in self._type_buttons.values():
            b.setEnabled(enabled)

    # -- queue table -------------------------------------------------------
    def _add_queue_row(self, title: str, platform: str, kind: str):
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        vals = [str(row + 1), title, platform, kind.title(), "Downloading", "0%"]
        for c, val in enumerate(vals):
            item = QTableWidgetItem(val)
            if c == 4:
                item.setForeground(Qt.red)
            self.queue_table.setItem(row, c, item)
        self._queue_row_index = row
        self.queue_table.scrollToBottom()

    def _update_queue_row(self, status: str, progress_text: str):
        if self._queue_row_index is None:
            return
        row = self._queue_row_index
        if row >= self.queue_table.rowCount():
            return
        self.queue_table.setItem(row, 4, QTableWidgetItem(status))
        self.queue_table.setItem(row, 5, QTableWidgetItem(progress_text))

    # -- slots driven by the main window / worker thread -------------------
    def set_status(self, text: str, color: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-family: 'JetBrains Mono', monospace; font-size: 12px;")

    def set_progress(self, value: float):
        pct = int(value * 100)
        self.progress_bar.setValue(pct)
        self.progress_pct.setText(f"{pct}%")
        self._update_queue_row("Downloading", f"{pct}%")

    def set_controls(self, running: bool = False, paused: bool = False, cancelling: bool = False):
        self.pause_btn.setEnabled(bool(running and not paused and not cancelling))
        self.resume_btn.setEnabled(bool(running and paused and not cancelling))
        self.cancel_btn.setEnabled(bool(running and not cancelling))

    def on_download_finished(self, success: bool):
        self._busy = False
        self._set_ui_enabled(True)
        self.set_controls(running=False)
        self.progress_bar.set_active(False)
        self.open_folder_btn.setVisible(bool(success))
        self._status_rows["active"]._label.setText("Active Downloads: 0")
        self._status_rows["active"]._dot.set_state("idle")
        self._status_rows["engine"]._label.setText("Engine Status: Ready")
        self._update_queue_row("Done" if success else "Failed", "100%" if success else "—")
        if success:
            # Clear the URL box so it's immediately ready for the next
            # link — only on success: a failed download keeps its URL in
            # the box so the user can see/retry/debug what just failed.
            self.url_entry.clear()

    # -- system status panel ------------------------------------------------
    def _refresh_system_status(self):
        try:
            usage = shutil.disk_usage(self.path_entry.text() or os.path.expanduser("~"))
            free_gb = usage.free / (1024 ** 3)
            self.disk_lbl.setText(f"Disk Space: {free_gb:.0f} GB free")
        except Exception:
            self.disk_lbl.setText("Disk Space: —")

        # The connectivity check below is a blocking socket call (up to
        # ~1.2s on a slow/firewalled network) — profiling this page's
        # refresh loop showed it was responsible for ~97% of total time,
        # running synchronously on the GUI thread every 5 seconds, which
        # would periodically freeze the whole UI. Run it on a background
        # thread instead; skip starting a new one if one's still in flight.
        if self._net_check_thread is None or not self._net_check_thread.isRunning():
            self._net_check_thread = _NetCheckThread(self)
            self._net_check_thread.result.connect(self._on_net_check_result)
            self._net_check_thread.finished.connect(self._net_check_thread.deleteLater)
            self._net_check_thread.start()

        if psutil is not None:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                self.sys_lbl.setText(f"CPU {cpu:.0f}%  ·  RAM {ram:.0f}%")
            except Exception:
                self.sys_lbl.setText("CPU —  ·  RAM —")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(5000, self._refresh_system_status)

    def _on_net_check_result(self, connected: bool):
        self._status_rows["net"]._dot.set_state("ok" if connected else "error")
        self._status_rows["net"]._label.setText("Internet: Connected" if connected else "Internet: Offline")

    @staticmethod
    def _has_internet() -> bool:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=1.2).close()
            return True
        except OSError:
            return False
