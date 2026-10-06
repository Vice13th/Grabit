# GrabIt — Threat Model

## Scope

This model covers URL ingestion, routing, filesystem writes, dependency installation, external process execution, third-party engines, GUI workers, and packaging.

## Assets

- User-selected download destination and local files.
- Application integrity and configuration.
- Credentials or session material exposed to third-party engines by user choice.
- Availability and correctness of the GUI/download state.

## Threats

### Malicious remote metadata
A server or page may provide a hostile filename, title, content-disposition value, or browser download name.

Defense: sanitize filenames and keep normalized destinations inside the configured save directory.

### Untrusted URL input
A pasted or imported URL can contain malformed schemes, unexpected syntax, or data intended to trigger unintended routing.

Defense: validate supported schemes and keep core parsing/routing deterministic and offline.

### Compromised or broken third-party engine
An engine may fail, change APIs, return malformed metadata, or raise unexpected exceptions.

Defense: isolate engine failures, preserve typed result/error paths, and do not let one backend redefine global application state.

### Dependency supply-chain risk
Installing a package changes executable application code.

Defense: explicit user consent, official PyPI by default, explicit mirror fallback, and explicit system-package installation.

### External command abuse
aria2c, rclone, megadl, ffmpeg, and browser tooling operate outside Python's process boundary.

Defense: structured subprocess arguments, bounded inputs, path validation, and explicit user configuration.

### GUI-thread denial of service
Blocking network/download work on the Qt GUI thread can freeze the application.

Defense: workers/QThreads for blocking work and focused lifecycle/cancellation tests.

### Parallel-state corruption
Multiple workers may interact with shared yt-dlp archive state.

Defense: parallel mode defaults to concurrency 1; shared-archive hardening remains a roadmap item.

## Verification principle

Unit tests demonstrate tested logic under test doubles. They do not prove real platform compatibility, every live engine, visual correctness, or packaged Windows behavior.
