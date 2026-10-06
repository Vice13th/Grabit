# GrabIt v1.0.0 — Universal Media Downloader
### Product Overview

GrabIt is a desktop application (Windows/macOS/Linux, PySide6) that takes any
pasted URL, automatically detects the platform behind it, and routes the
download to the right specialized engine — no manual tool-picking required.

---

## 1. Supported Platforms & Engines (18 backends)

| Category | Platforms / Engines |
|---|---|
| Video (general) | **yt-dlp** — YouTube + hundreds of generic video sites (playlists, subtitles, chapters) |
| Image galleries | **gallery-dl** — Pixiv, DeviantArt, Danbooru and other booru/art sites |
| Social | **Instaloader** (Instagram posts/stories/reels), **Pinterest**, **Reddit**, **TikTok** (no-watermark) |
| Streaming platforms | **Bilibili**, **Twitch** (VOD + clips), **Streamlink** (live-stream capture) |
| Audio | **SoundCloud** (tracks/playlists) |
| AI / creative | **CivitAI** (model files + previews) |
| Cloud storage | **Google Drive**, **Dropbox**, **Mega.nz**, **rclone** (any configured remote) |
| Generic / fallback | **Direct HTTP(S)** (resumable), **aria2** (multi-connection, torrents/metalinks), **Playwright** (headless-browser fallback for JS-heavy pages) |

Every engine self-registers into a single plugin-style registry — adding a new
platform doesn't touch the UI or routing logic.

---

## 2. Smart Routing
Paste a URL → GrabIt instantly identifies the platform, picks the correct
engine, and shows a live "pipeline" (URL → Platform → Engine → Media Type →
Output) so you always see exactly what's about to happen before you click
Grab. Unrecognized URLs still get a sensible generic-fetch attempt.

## 3. Media Options
- Quality/format selection (per-engine, only relevant options shown)
- Playlist download toggle, subtitle download/embed, audio-only conversion
- Auto-classified media type (Video / Audio / Image / File)
- Thumbnail + title/duration/format preview before downloading
- YouTube playlist detection with an explicit "whole playlist vs. this video
  only" prompt — never silently grabs more than intended

## 4. Batch Downloads
Paste a list of URLs (or import from TXT/CSV/JSON/YAML/XML/MD) and download
them all in one run — sequential by default, or **parallel** (configurable
concurrency) via a bounded thread pool, with cooperative pause/resume/cancel
shared across every in-flight download.

## 5. Full Application (9 sections)
| Page | What it does |
|---|---|
| **Grab** | Single-URL download with live platform detection, quick actions (paste/open/save/reset), a live engine log, and real-time system status (CPU/RAM/disk/connectivity) |
| **Batch** | Multi-URL queued/parallel downloads |
| **Downloads** | Session history — every download this session, with result and destination |
| **Media Studio** | Browse everything already saved to your download folder — open or reveal any file |
| **Engines** | Live status of all 18 backends — which are installed and available right now |
| **Settings** | Save folder, auto-paste-from-clipboard, parallel batch download count, and the two off-by-default security toggles below |
| **Updates** | Checks PyPI for newer GrabIt releases |
| **Logs** | Live-tailed application log, exportable |
| **About** | Version, links, credits |

## 6. Reliability
- Real per-run rotating log file (not scattered console prints)
- Automatic retry with exponential backoff on transient network errors
  (connection drops are retried; mid-download interruptions are not — they
  fail cleanly instead of silently corrupting a partial file)
- Deterministic pause/resume/cancel — cancellation is never swallowed by retry logic

## 7. Security-first design
- **No silent installs.** Missing packages are only ever installed with
  explicit consent — shown in a graphical window, never installed
  automatically at startup.
- **Official PyPI index only by default.** Third-party mirror fallback is
  off unless you opt in, and each mirror still asks for confirmation.
- **No silent `sudo`.** ffmpeg installs via a pure-Python wheel first; system
  package-manager installs require an explicit opt-in toggle.
- **Path-traversal hardened.** Filenames derived from server responses or
  browser download events are sanitized before ever touching disk — a
  malicious server cannot write outside your chosen save folder.

## 8. First-run & startup experience
- Missing dependencies are detected once (instant, local, no network) and
  only prompted for — via a graphical window, **never a terminal** — the
  moment something is actually missing. Nothing is re-checked or
  re-downloaded on runs where everything's already installed.
- A branded animated splash screen (fade transitions, real progress tied to
  actual startup steps) covers the brief interface build time.
- Optional portable mode: keep all data next to the app instead of your home
  directory.

## 9. Requirements
- Python 3.10+
- PySide6 (bundled as a required dependency)
- ~1 GB disk for the full engine set; individual engines can be skipped if
  their platform isn't needed

## 10. Getting it running
```bash
python main.py            # first run offers to install missing packages
pip install -e .          # or install as a package → `grabit` command
```
Windows users: double-click `GrabIt.pyw` for a guaranteed no-terminal launch,
or build a single-file `.exe` via the included PyInstaller instructions.

---
*Open source, MIT licensed — free to use, modify, and redistribute.*
