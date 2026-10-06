"""GrabIt v8 visual theme — dark 'terminal' aesthetic with red accents.

Replaces the old flat DARK_QSS. Kept as a separate module (``theme.py``)
rather than overwriting ``styles.py`` in place so the accent palette and
fonts live in one obvious place; ``styles.py`` re-exports ``DARK_QSS`` from
here for anything that still imports the old name.
"""
from __future__ import annotations

# -- palette --------------------------------------------------------------
BG = "#0a0a0c"
BG_PANEL = "#111114"
BG_PANEL_ALT = "#0d0d10"
BG_INPUT = "#16161a"
BORDER = "#232327"
BORDER_SOFT = "#1a1a1e"
TEXT = "#e8e8ea"
TEXT_DIM = "#8a8a90"
TEXT_FAINT = "#57575d"
RED = "#ff3b3b"
RED_DIM = "#c4302f"
RED_GLOW = "#ff6b5f"
GREEN = "#3ddc84"
YELLOW = "#ffb84d"
BLUE = "#4a9eff"

FONT_MONO = '"JetBrains Mono", "Cascadia Mono", "Consolas", "Fira Code", monospace'
FONT_UI = '"Segoe UI", "Inter", "Roboto", sans-serif'

DARK_QSS = f"""
* {{ outline: none; }}
QWidget {{ background-color: {BG}; color: {TEXT}; font-family: {FONT_UI}; font-size: 13px; }}
QMainWindow {{ background-color: {BG}; }}
QToolTip {{ background-color: {BG_PANEL}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px 8px; font-family: {FONT_MONO}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {RED_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 4px; min-width: 24px; }}

/* -- typography ---------------------------------------------------- */
QLabel#BrandTitle {{ font-family: {FONT_UI}; font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px; }}
QLabel#BrandTitleAccent {{ color: {RED}; }}
QLabel#BrandSubtitle {{ font-family: {FONT_MONO}; font-size: 10px; color: {TEXT_DIM}; letter-spacing: 1px; }}
QLabel#SectionTitle {{ font-family: {FONT_MONO}; font-size: 11px; font-weight: 600; color: {TEXT_DIM}; letter-spacing: 1.5px; }}
QLabel#SectionTitleAccent {{ color: {RED}; font-family: {FONT_MONO}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}
QLabel#FieldLabel {{ font-size: 12px; font-weight: 600; color: #c8c8cc; }}
QLabel#StatusLabel {{ font-family: {FONT_MONO}; font-size: 12px; color: {TEXT_DIM}; }}
QLabel#DimLabel {{ color: {TEXT_DIM}; font-size: 12px; }}
QLabel#FaintLabel {{ color: {TEXT_FAINT}; font-size: 11px; }}
QLabel#MonoValue {{ font-family: {FONT_MONO}; font-size: 12px; color: {TEXT}; }}
QLabel#MonoKey {{ font-family: {FONT_MONO}; font-size: 11px; color: {TEXT_DIM}; }}
QLabel#PageTitle {{ font-size: 20px; font-weight: 700; color: #ffffff; }}
QLabel#RunTag {{ font-family: {FONT_MONO}; font-size: 10px; font-weight: 700; color: {RED}; letter-spacing: 2px; }}

/* -- panels / cards -------------------------------------------------- */
QFrame#Card {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 10px; }}
QFrame#CardAlt {{ background-color: {BG_PANEL_ALT}; border: 1px solid {BORDER_SOFT}; border-radius: 10px; }}
QFrame#HeaderBar {{ background-color: {BG_PANEL}; border-bottom: 1px solid {BORDER}; }}
QFrame#Divider {{ background-color: {BORDER}; max-height: 1px; min-height: 1px; }}
QFrame#Sidebar {{ background-color: #0c0c0f; border-right: 1px solid {BORDER}; }}
QFrame#PipelineStep {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 10px; }}
QFrame#PipelineStep[done="true"] {{ border: 1px solid {RED_DIM}; }}

/* -- inputs ------------------------------------------------------------ */
QLineEdit {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 9px; padding: 9px 12px; color: #ffffff; font-family: {FONT_MONO}; selection-background-color: {RED}; }}
QLineEdit:focus {{ border: 1px solid {RED}; }}
QLineEdit:disabled {{ background-color: #131316; color: {TEXT_FAINT}; }}
QPlainTextEdit, QTextEdit {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px; color: #d6d6da; font-family: {FONT_MONO}; font-size: 12px; selection-background-color: {RED}; }}
QPlainTextEdit:focus, QTextEdit:focus {{ border: 1px solid {RED}; }}
QComboBox {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 10px; color: #ffffff; min-height: 22px; }}
QComboBox:hover {{ border: 1px solid #35353b; }}
QComboBox:focus {{ border: 1px solid {RED}; }}
QComboBox:disabled {{ background-color: #131316; color: {TEXT_FAINT}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; selection-background-color: {RED_DIM}; color: #ffffff; outline: none; padding: 4px; }}
QCheckBox {{ color: #c8c8cc; spacing: 9px; font-size: 12px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {BORDER}; background-color: {BG_INPUT}; }}
QCheckBox::indicator:checked {{ background-color: {RED}; border: 1px solid {RED}; }}
QCheckBox::indicator:hover {{ border: 1px solid {RED}; }}

/* -- buttons ------------------------------------------------------------ */
QPushButton {{ font-family: {FONT_UI}; }}
QPushButton#GrabBtn {{ background-color: rgba(255,59,59,0.12); color: {RED_GLOW}; border: 1px solid {RED}; border-radius: 10px; padding: 10px 22px; font-size: 14px; font-weight: 700; letter-spacing: 1px; }}
QPushButton#GrabBtn:hover {{ background-color: rgba(255,59,59,0.22); }}
QPushButton#GrabBtn:pressed {{ background-color: rgba(255,59,59,0.32); }}
QPushButton#GrabBtn:disabled {{ background-color: {BG_INPUT}; color: {TEXT_FAINT}; border: 1px solid {BORDER}; }}
QPushButton#BrowseBtn {{ background-color: {BG_INPUT}; color: #d6d6da; border: 1px solid {BORDER}; border-radius: 9px; padding: 8px 14px; font-weight: 600; }}
QPushButton#BrowseBtn:hover {{ border: 1px solid {RED_DIM}; color: #ffffff; }}
QPushButton#BrowseBtn:disabled {{ color: {TEXT_FAINT}; }}
QPushButton#SmallBtn {{ background-color: {BG_INPUT}; color: #c8c8cc; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600; }}
QPushButton#SmallBtn:hover {{ border: 1px solid {RED_DIM}; color: #ffffff; }}
QPushButton#SmallBtn:disabled {{ color: {TEXT_FAINT}; border: 1px solid {BORDER_SOFT}; }}
QPushButton#OpenFolderBtn {{ background-color: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 12px; font-size: 12px; }}
QPushButton#OpenFolderBtn:hover {{ color: #ffffff; border: 1px solid {RED_DIM}; }}
QPushButton#QuickActionBtn {{ background-color: {BG_INPUT}; color: #d6d6da; border: 1px solid {BORDER}; border-radius: 9px; padding: 10px; text-align: left; font-size: 12px; font-weight: 600; }}
QPushButton#QuickActionBtn:hover {{ border: 1px solid {RED_DIM}; background-color: #1a1a1f; }}
QPushButton#IconBtn {{ background-color: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 7px; padding: 4px; }}
QPushButton#IconBtn:hover {{ color: #ffffff; border: 1px solid {RED_DIM}; }}
QPushButton#WinBtn {{ background-color: transparent; color: {TEXT_DIM}; border: none; padding: 6px 10px; font-size: 13px; }}
QPushButton#WinBtn:hover {{ background-color: {BG_INPUT}; color: #ffffff; }}
QPushButton#WinBtnClose:hover {{ background-color: {RED}; color: #ffffff; }}

/* -- media type toggle -------------------------------------------------- */
QPushButton#MediaTypeBtn {{ background-color: {BG_INPUT}; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 9px; padding: 10px; font-weight: 700; font-size: 12px; }}
QPushButton#MediaTypeBtn:checked {{ background-color: rgba(255,59,59,0.14); color: #ffffff; border: 1px solid {RED}; }}
QPushButton#MediaTypeBtn:hover {{ border: 1px solid {RED_DIM}; }}

/* -- progress ------------------------------------------------------------ */
QProgressBar {{ background-color: {BG_INPUT}; border: none; border-radius: 4px; height: 8px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background-color: {RED}; border-radius: 4px; }}

/* -- sidebar nav ---------------------------------------------------------- */
QListWidget#NavList {{ background-color: transparent; border: none; padding: 6px; font-size: 13px; }}
QListWidget#NavList::item {{ color: {TEXT_DIM}; padding: 10px 12px; border-radius: 9px; margin: 2px 0; }}
QListWidget#NavList::item:hover {{ background-color: {BG_INPUT}; color: #ffffff; }}
QListWidget#NavList::item:selected {{ background-color: rgba(255,59,59,0.14); color: #ffffff; border: 1px solid {RED_DIM}; }}

/* -- tables ---------------------------------------------------------------- */
QTableWidget {{ background-color: transparent; border: none; gridline-color: {BORDER_SOFT}; color: #d6d6da; font-size: 12px; selection-background-color: rgba(255,59,59,0.15); }}
QHeaderView::section {{ background-color: transparent; color: {TEXT_FAINT}; border: none; border-bottom: 1px solid {BORDER}; padding: 6px; font-family: {FONT_MONO}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QTableWidget::item {{ border-bottom: 1px solid {BORDER_SOFT}; padding: 4px; }}

/* -- tabs (legacy pages that still use QTabWidget) ------------------------- */
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; background-color: {BG_PANEL}; }}
QTabBar::tab {{ background-color: {BG_INPUT}; color: {TEXT_DIM}; padding: 8px 16px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }}
QTabBar::tab:selected {{ background-color: {RED}; color: #ffffff; }}

/* -- legacy object names kept for pages not fully rebuilt ----------------- */
QLabel#TitleLabel {{ font-size: 24px; font-weight: 800; color: #ffffff; }}
QLabel#SubtitleLabel {{ font-size: 12px; color: {TEXT_DIM}; }}
QLabel#PlatformBadge {{ font-size: 11px; font-weight: 700; padding: 5px 14px; border-radius: 9px; background-color: {BG_INPUT}; color: {RED_GLOW}; border: 1px solid {BORDER}; }}
QPushButton#DownloadBtn {{ background-color: rgba(255,59,59,0.12); color: {RED_GLOW}; border: 1px solid {RED}; border-radius: 10px; padding: 12px 20px; font-size: 14px; font-weight: 700; }}
QPushButton#DownloadBtn:hover {{ background-color: rgba(255,59,59,0.22); }}
QPushButton#DownloadBtn:disabled {{ background-color: {BG_INPUT}; color: {TEXT_FAINT}; border: 1px solid {BORDER}; }}

QScrollArea {{ border: none; background: transparent; }}
QSpinBox {{ background-color: {BG_INPUT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 8px; color: #fff; }}
QSpinBox:focus {{ border: 1px solid {RED}; }}
"""
