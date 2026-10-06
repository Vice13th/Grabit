# Changelog — GrabIt

> Current package metadata is **1.0.4**. The historical entry below documents the v1.0.0 modular release work; it is not a claim that a v1.0.4 release has been published.

## GUI redesign (dark/red terminal theme, inspired by reference mockup)
- New sidebar navigation (`Sidebar` + `QStackedWidget`) replacing the old `QTabWidget`.
- Rebuilt **Grab** page: URL → pipeline strip (URL/Platform/Engine/Media Type/Output) →
  media options + thumbnail preview → progress card → session queue table, plus a right
  column (Detected Platform, Quick Actions, live Engine Log, System Status).
- New pages that didn't exist before: **Settings** (real UI for previously-dead `AppConfig`
  toggles), **Downloads** (session history), **Media Studio** (save-folder file browser),
  **Engines** (live registry + availability), **Logs** (tails the real log file).
- Animated primitives: pulsing status dots, glow progress bars, pipeline-step glow-flash,
  fade transitions — `grabit/gui/anim_widgets.py`.
- Real branded logo applied across sidebar + splash (`grabit/gui/assets/logo.png`).

## Startup experience
- New animated splash screen (`grabit/gui/splash.py`): fade-in/out, drop-shadow depth,
  real determinate progress tied to actual startup steps (not fake/indeterminate).
- Dependency install no longer opens a terminal: a tkinter GUI window
  (`grabit/bootstrap_ui.py`) replaces the console `input()` prompt (falls back to
  console only if tkinter itself is unavailable). No re-check/re-download on runs where
  everything required is already present — the underlying check was already a fast,
  local, no-network probe.

## Security fixes
- `grabit/core/url_utils.py`: added `sanitize_filename()` — closes a path-traversal
  vulnerability where a malicious/compromised server's `Content-Disposition` header
  (`direct_engines.py`) or a browser download event (`playwright_fallback.py`) could
  write outside the chosen save folder. Also applied to SoundCloud artist/title
  filenames (`social_video_engines.py`) for robustness.

## Housekeeping
- Removed two non-functional Instagram-only checkboxes from the Image options tab
  (behavior preserved via existing dataclass defaults).
- `.github/workflows/tests.yml` — CI running `pytest tests/` on Python 3.10–3.12.
- `.gitignore` extended (`grab_data/`, `settings.json`, `*.log`, `.venv/`, etc.).
- Version bumped `7.0.0` → `1.0.0` (`grabit/__init__.py`, `pyproject.toml`).

## Verification performed
- `pytest tests/` — 19/19 passing throughout.
- Headless (`QT_QPA_PLATFORM=offscreen`) smoke tests of: full window construction, all
  9 sidebar pages switching, URL routing/pipeline population, settings save round-trip,
  log bridge, splash screen fade/progress/handoff, sanitize_filename against traversal,
  absolute-path and slash-in-metadata cases.

## Not independently verified
- Visual rendering on a real display (all testing here was headless/offscreen).
- The tkinter dependency-install window (`bootstrap_ui.py`) — this container has no
  tkinter available to run it; only AST-validated for syntax correctness.
