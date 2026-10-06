# PyInstaller spec for the Windows x64 release build.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent.parent
ASSET_DIR = ROOT / "grabit" / "gui" / "assets"
datas = [
    (str(ASSET_DIR / "logo.png"), "grabit/gui/assets"),
    (str(ASSET_DIR / "logo.ico"), "grabit/gui/assets"),
]
hiddenimports = [
    "PySide6", "requests", "yt_dlp", "gallery_dl", "instaloader",
    "yaml", "pinterest_dl", "gdown", "bilix", "twitch_archiver",
    "sclib", "RedDownloader", "tiktok_downloader", "instacapture",
    "civitai_downloader",
]
hiddenimports += collect_submodules("yt_dlp")
hiddenimports += collect_submodules("gallery_dl")

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter.test", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="GrabIt", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon=str(ASSET_DIR / "logo.ico"),
)
