# Building the final GrabIt.exe (no console, icon, splash logo, zero runtime installs)

This can't be cross-compiled from Linux — a Windows .exe must be built
*on Windows*. Run this once, on Windows, with Python + your repo checked out.

## The bug in the previous command (why the last build had no window/icon)

`--onefile` only bundles **Python bytecode**. It does **not** bundle
arbitrary files like `grabit/gui/assets/logo.png` / `logo.ico` unless you
tell it to with `--add-data`. Without that flag, the frozen exe has no
logo file to load at runtime, so:
- `QApplication.setWindowIcon()` silently gets a null icon → no taskbar icon
- The splash screen's `QPixmap(logo.png)` is also null → blank/no logo

That's exactly what was reported. Fixed below.

## The correct command

```bat
pip install pyinstaller
pip install -r requirements.txt
pip install -r requirements-optional.txt

pyinstaller --onefile --noconsole --name GrabIt ^
  --icon grabit\gui\assets\logo.ico ^
  --add-data "grabit\gui\assets;grabit\gui\assets" ^
  --hidden-import PySide6 --hidden-import requests --hidden-import yt_dlp ^
  --hidden-import gallery_dl --hidden-import instaloader --hidden-import yaml ^
  --hidden-import pinterest_dl --hidden-import gdown --hidden-import bilix ^
  --hidden-import twitch_archiver --hidden-import sclib --hidden-import RedDownloader ^
  --hidden-import tiktok_downloader --hidden-import instacapture --hidden-import civitai_downloader ^
  --hidden-import streamlink --hidden-import playwright --hidden-import imageio_ffmpeg ^
  main.py
```

- `--onefile` → single `dist\GrabIt.exe`, nothing else to ship.
- `--noconsole` → no terminal window, ever.
- `--icon` → the .exe file itself, and its taskbar/shortcut icon, use the brand logo.
- `--add-data` → bundles `grabit/gui/assets/` (logo.png, logo.ico) into the exe
  so the window icon and splash screen actually have a logo to load at runtime.
- `--hidden-import` (one per required + optional package) → every dependency
  ships **inside** the exe. The end user never sees a "missing packages"
  prompt at all — first run goes straight to the splash screen.
  - The `pip install -r requirements*.txt` step before building is required:
    PyInstaller can only bundle a package if it's installed in the
    environment you're building from.
  - `bilix` may still fail to `pip install` on Python 3.12 (see the
    Bilibili section of the source's own comments — its `danmakuC`
    dependency has no 3.12 wheel yet). If so, just drop
    `--hidden-import bilix` from the command; GrabIt's Bilibili engine
    already falls back to yt-dlp automatically when bilix isn't bundled.

Result: `dist\GrabIt.exe` — double-click, no terminal, branded icon,
branded splash, and (aside from the bilix caveat above) zero dependency
prompts on first run.

## Building the branded installer on top of that
```bat
iscc installer.iss
```
Produces `GrabIt-Setup-<version>.exe` (see `installer.iss` — Inno Setup,
free, https://jrsoftware.org/isinfo.php). Installer wizard icon, Start
Menu/Desktop shortcuts and uninstaller all use `GrabIt.exe`'s own icon, so
there's nothing else to configure. The installer itself runs silently
through its GUI wizard — no console at any point.

## Right now, without building anything
`GrabIt.pyw` (repo root) already gives the same no-console guarantee on any
machine with Python installed — but still requires the user to have Python
and the dependencies installed separately; only the built `.exe` above is
fully self-contained.
