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
