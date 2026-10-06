# GrabIt — Technology Gap Report

Written after a profiling pass that surfaced a real GUI-thread-blocking bug
(see flame graph + the fix in `grab_page.py`). This report covers the
broader stack, not just that one finding.

## 1. Dependency architecture — the biggest real gap
Confirmed **twice in this session alone**: `bilix` (Bilibili) has no
Python 3.12 wheel for its `danmakuC` dependency and fails to build from
source; `sclib`/`soundcloud-lib`'s SoundCloud client relies on
screen-scraping SoundCloud's page for a client_id, which breaks whenever
SoundCloud changes their site. Both are now mitigated with a fallback to
yt-dlp, but the underlying pattern — 9 separate, small, loosely-maintained
per-platform libraries (`bilix`, `sclib`, `RedDownloader`,
`tiktok-downloader-py`, `instacapture`, `civitai-downloader`,
`pinterest-dl`) — is inherently higher-maintenance than the direction the
wider ecosystem has moved: consolidating around yt-dlp's actively-maintained
extractor set (1,800+ sites) wherever an extractor already exists, and
reserving separate libraries only for platforms yt-dlp genuinely doesn't
cover. **Gap:** audit which of those 9 libraries yt-dlp can already replace
outright (TikTok and Reddit both have mature yt-dlp extractors, for
instance) rather than keeping a fragile dedicated dependency.

## 2. Packaging: PyInstaller vs newer alternatives
`build_installer.md` uses PyInstaller (`--onefile`), which is the
established, safe choice but not the current leading edge — **Nuitka**
(compiles to C) typically gives faster startup and a smaller binary for a
Qt app this size, at the cost of longer build times. Not urgent — PyInstaller
is still widely used and fully supported — but worth a bake-off before a
v2.

## 3. Concurrency model
Every background task (downloads, playlist probing, now the net-connectivity
check) uses `QThread` subclasses — a traditional, well-tested Qt pattern,
and the right call for CPU/blocking-I/O-bound work like subprocess calls.
For the network-bound pieces specifically (HTTP requests, multiple
simultaneous API calls), `asyncio` + `qasync` would reduce per-task OS
thread overhead — not a correctness gap, just a scalability one that
would only matter at much higher concurrency than this app currently runs.

## 4. CI coverage
**RESOLVED at the repository-configuration level:** `.github/workflows/tests.yml`
now runs the pure-logic test suite on `ubuntu-latest`, `windows-latest`, and
`macos-latest` across Python 3.9–3.12. This improves platform regression
visibility, but the repository still needs fresh green CI receipts before
claiming those matrix combinations have passed.

## 5. Test coverage
19 recorded tests, all against the pure-logic layer (`SmartRouter`, `url_utils`).
Zero automated coverage of: the 18 engines (even mocked-network unit tests
would have caught the `soundcloud_lib`→`sclib` import-name bug and the
`scsearch`+flat-mode bug found this session before a user had to report
them), the GUI layer (no `pytest-qt`), or the dependency-install flow.

## 6. Static analysis
Type hints are used throughout (`from __future__ import annotations`,
dataclasses, typed signatures) but nothing enforces them — no `mypy` or
`pyright` in CI. Also no `ruff`/`flake8` lint gate.

## 7. Crash/error visibility
Logging is solid (rotating per-run log file, now with a live Qt bridge),
but there's no opt-in crash/error reporting (e.g. Sentry). Every bug this
session required the user to manually find and paste a log excerpt —
standard practice for a shipped desktop app at this scale is an opt-in
"send this error report" prompt on an unhandled exception.

## Resolved since this report was written
- Repository-level engineering contract, security policy, threat model, checkpoint, and roadmap are now present.
- Cross-platform CI workflow is now present; green status remains unverified until a completed run is observed.

## Not a gap
- PySide6 (`>=6.6` floor) is a fine choice and current — Qt for Python is
  actively developed and PySide6 remains the standard, officially-supported
  Python Qt binding as of this writing.
- The dark/red UI, sidebar navigation, and animation primitives
  (`QPropertyAnimation`-based) are a normal, current approach for a Qt
  desktop app — no gap there.
