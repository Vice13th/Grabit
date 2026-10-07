# PyInstaller spec for the Windows x64 release build.
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
ASSET_DIR = ROOT / "grabit" / "gui" / "assets"
datas = [
    (str(ASSET_DIR / "logo.png"), "grabit/gui/assets"),
    (str(ASSET_DIR / "logo.ico"), "grabit/gui/assets"),
]
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
