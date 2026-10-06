# GrabIt v1.0.0 — Universal Media Downloader

A desktop app (PySide6) that detects the platform behind a pasted URL and
routes it to the right download engine — yt-dlp, gallery-dl, Instaloader,
direct HTTP, and about a dozen more specialized backends (Bilibili, Twitch,
SoundCloud, Reddit, TikTok, CivitAI, Mega, Google Drive,
live streams via Streamlink, torrents/metalinks via aria2, cloud remotes via
rclone, and a Playwright-based fallback for JS-heavy pages).

This is a from-scratch **architectural rewrite** of a single 2,547-line
script into a modular package, built around four priorities: **security**,
**architecture/maintainability**, **reliability/error-handling**, and
**performance** — plus permission to improve UX/behavior where it helped.
Every original engine, URL pattern and workflow is preserved; nothing was
dropped silently (see "What changed" below for the handful of deliberate,
documented exceptions).

## Running it

```bash
python main.py                 # first run offers to install missing packages
python main.py --yes           # non-interactive install (official PyPI only)
python main.py --no-install    # never install; prints the pip command instead
python main.py --verbose       # debug logging
```

Or install as a package: `pip install -e .` then run `grabit`.

For a portable install (all data in `grab_data/` next to `main.py` instead of
your home directory), create an empty `portable.flag` file next to `main.py`
before first launch.

## Project layout

```
main.py                     Entry point
grabit/
  app.py                    Bootstrap: config → logging → dependency check → Qt
  config.py                 Paths, portable-mode detection, persisted settings
  logging_setup.py          Central logging (console + rotating-by-run log file)
  core/                     Pure logic — no Qt, no engine libraries
    models.py                 DownloadOptions / DownloadResult / RouteDecision
    exceptions.py              DownloadCancelled / DownloadPaused / EngineNotAvailableError
    url_utils.py               URL validation & extraction (TXT/CSV/JSON/YAML/XML/MD)
    router.py                  SmartRouter: URL -> engine decision
    retry.py                   Exponential-backoff retry decorator
  dependencies/              Detection + EXPLICIT, opt-in installation
    manager.py                 check_dependencies(), install_package(), try_install_ffmpeg()
    mirrors.py                  PyPI mirror list (opt-in only)
    updater.py                  PyPI version checks + updates
  engines/                   One registry, six family modules, ~18 backends
    base.py                    BaseEngine ABC
    ytdlp_engine.py, direct_engines.py, gallery_engines.py,
    social_video_engines.py, transport_engines.py, playwright_fallback.py
  workers/
    download_thread.py         QThread; sequential or concurrent batch execution
    playlist_probe_thread.py   YouTube playlist detection before download
  gui/                       The only subpackage that imports Qt
    main_window.py, single_tab.py, batch_tab.py, settings_panel.py,
    update_dialog.py, about_tab.py, widgets.py, styles.py
tests/                      Unit tests for the pure-logic layer (no Qt/network)
requirements.txt / requirements-optional.txt / pyproject.toml
```

## What changed, and why

### Security
- **No more silent auto-install.** The original ran `pip install` for every
  missing package *at import time*, before you'd seen any UI, falling back
  through six third-party PyPI mirrors (several in jurisdictions outside the
  usual trust boundary) using `--trusted-host` — which disables TLS
  certificate hostname verification for that host. `grabit.dependencies`
  only *reports* what's missing now; installation happens only after you
  say yes (console prompt on first run, or `--yes`/`--no-install` flags),
  hits the official index only by default, and mirror fallback requires an
  explicit, persisted `allow_mirror_fallback` opt-in *plus* a per-mirror
  confirmation.
- **No more silent `sudo apt-get install`.** ffmpeg installation now prefers
  the pure-Python `imageio-ffmpeg` wheel (official index); shelling out to
  `sudo apt-get`/`brew` requires `allow_sudo_system_install=True`, off by
  default. Otherwise GrabIt prints the exact command for you to run.
- Both toggles live in `~/.grabit/settings.json` (`AppConfig`), so the
  choice is explicit, visible, and yours.

### Architecture / maintainability
- **Plugin-style engine registry** (`grabit/engines/__init__.py`): each
  engine self-registers with `@register_engine("name")` instead of living
  in a hardcoded dict next to the GUI code. `BaseEngine` is now an `ABC`, so
  a broken engine implementation fails at import time, not mid-download.
- **Typed data models** (`grabit/core/models.py`): `DownloadOptions` and
  `DownloadResult` dataclasses replace loosely-shaped dicts passed between
  the router, the thread and every engine.
- **The settings panel is now actually used.** It was fully built in the
  original script but never instantiated — the single-download tab had a
  separate, duplicate "YouTube options" frame instead. That duplication is
  gone; the one settings panel now shows appropriate options for *any*
  engine that has them, not just YouTube.
- **The GUI is composed, not monolithic.** The original ~800-line
  `GrabItApp` class handled layout, events, playlist probing and thread
  management for two tabs at once, with near-duplicate pause/cancel wiring
  for each. Now each tab is a self-contained widget that emits Qt signals
  (`start_requested`, `pause_requested`, ...) and exposes plain update
  methods (`set_status`, `set_progress`, ...); `GrabItApp` is the *only*
  place that owns the download thread.
- **Bug fix:** the original's direct-file "kind" classification used
  slice indices (`DIRECT_EXTENSIONS[13:26]` etc.) that didn't line up with
  where each format group actually started, so most audio extensions were
  reported as `"image"` and several image extensions (plus `.zip`!) were
  reported as `"audio"`. It had no visible effect only because nothing read
  `kind` yet — now that the settings panel is live, it's fixed and covered
  by a regression test (`tests/test_router.py`).
- Dead code made honest: the instacapture-based Instagram engine (present
  in the original but never wired into routing) is now registered under an
  explicit `"instacapture"` name with a docstring explaining its status,
  instead of silently unreachable code.

### Reliability / error handling
- Real logging (`grabit/logging_setup.py`) to both console and a per-run
  log file, replacing scattered `print()` banners and a bare
  `traceback.print_exc()`. Engine failures are logged with full tracebacks
  (`logger.exception`) even though the GUI still shows a short message.
- `grabit/core/retry.py`: a small exponential-backoff decorator, applied to
  `DirectHttpEngine`'s connection step, so a transient DNS/connection error
  gets retried instead of failing the whole download outright. (Mid-stream
  interruptions are intentionally *not* retried — see the docstring there.)
- Cancellation (`DownloadCancelled`) is never swallowed by the retry
  decorator, so asking to cancel still wins immediately.

### Performance
- **Optional concurrent batch downloads.** The batch tab has a "Parallel
  downloads" spinbox (default **1**, i.e. identical to the original's
  fully-sequential behavior). Values above 1 run multiple URLs at once via
  a `ThreadPoolExecutor`; pause/cancel remain cooperative and shared across
  every in-flight download. See `DownloadThread._run_concurrent`.

### Tests
`tests/` covers the pure-logic layer — `SmartRouter` (including the
extension-classification bug fix) and the URL-extraction helpers — with no
Qt or network dependency, so it runs in CI easily: `pytest tests/`.

## Honest limitations / things not attempted

- The engine family modules (`gallery_engines.py`,
  `social_video_engines.py`, etc.) group several related engines per file
  rather than one file per engine. This keeps the file count manageable;
  splitting further (one engine per file, ~19 files) is a mechanical,
  low-risk follow-up if you want it.
- Concurrent batch downloads share one on-disk yt-dlp "archive" file across
  workers; concurrent small appends to it are very unlikely to corrupt it
  in practice, but it isn't a hardened multi-writer format. Sequential mode
  (the default) is unaffected.
- No packaging (PyInstaller/Nuitka) spec is included; the original didn't
  have one either. `pyproject.toml` is set up so `pip install -e .` and a
  `grabit` console script work, which is the piece that was missing before.
