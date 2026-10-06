# Grabit — Visual / Loading / Easter Egg Handoff

## Purpose
Give Grabit a practical media-tool identity that feels fast, polished, and tactile while remaining visibly separate from the rest of VICE13TH LABS.

## Shared VICE13TH LABS DNA
Shared structure, not shared colors: dark foundation, premium typography, disciplined spacing, material depth, restrained motion.

## Grabit visual identity
Direction: **Acrylic + Soft Metallic + Glass**.
Base: slate / graphite.
Primary accent: warm copper/orange.
The accent should communicate activity, download progress, media actions, and completion—not security alerts or scientific telemetry.

## Loading states — REQUIRED
Audit and design:
- application startup
- URL parsing/routing
- metadata extraction
- engine initialization
- queued/batched downloads
- active download progress
- post-processing
- completion/failure
- dependency/install operations

Progress states must make active work obvious without blocking the main UI. Distinguish queued, active, paused, retrying, completed, and failed states.

## Easter Eggs — REQUIRED
Use media/download themed Easter Eggs: subtle format references, playful filename details, hidden power-user shortcuts, or carefully authored UI responses.
They must never interfere with downloading, path handling, retries, or error recovery.

## Anti-patterns
No random green/purple panels, no generic SaaS rainbow gradients, no fake progress, no duplicated branding, no blocking animation pretending work is happening, and no decorative elements that compete with download status.

## Verification gate
Capture startup, queue, active transfer, retry/error, and completion states. Verify loading animations do not interfere with worker/UI responsiveness.

> WORKFLOW: INSPECT → REPORT → IMPLEMENT → VERIFY
> BEFORE IMPLEMENTATION: Read AGENTS.md, CHECKPOINT.md, and the current roadmap/technical-gap document. Reconcile this handoff with those sources before changing code.

## Execution hardening

### OBSERVED implementation anchors
- Main UI: grabit/gui/main_window.py
- Shared visual theme: grabit/gui/theme.py and styles.py
- Startup splash: grabit/gui/splash.py
- Motion helpers: grabit/gui/anim_widgets.py
- Logo asset: grabit/gui/assets/logo.png
- Main window owns DownloadThread and pages communicate through signals/update methods.

### CURRENT baseline versus TARGET
The current theme and splash are red-led. The target is slate/graphite with warm copper/orange product identity. This is a coherent theme migration, not permission to recolor every semantic state orange.

### Loading hard rule
Preserve the existing SplashScreen API, real progress updates, fade handoff and logo asset. Do not create a second splash or replace real progress with fake timed progress.

### Worker/UI hard rule
Visual work must never move download/network work into the GUI thread or alter DownloadThread ownership, pause/resume/cancel semantics, engine routing, retry behavior or dependency safety controls.

### Semantic color hard rule
Copper/orange is product identity/activity. Green remains semantic success. Yellow/orange may represent warning when appropriate. Red remains actual error/danger. Do not flatten all statuses into one accent.

### Easter Egg hard rule
Easter Eggs must not modify URLs, target paths, retries, engine selection, download state or worker lifecycle. They must remain non-blocking.

### Stop and report
Stop if a requested state has no real lifecycle signal, progress is unavailable, a design change would require editing worker behavior, or a new dependency is needed solely for decoration.

### Evidence required before completion
Verify splash launch, each real splash update, handoff, idle/active download, queue, progress, pause/resume, cancellation, retry, completion, failure, Engines, Settings, Logs, Media Studio, dependency/update surfaces, resize/focus states and Easter Eggs.
