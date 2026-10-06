# GrabIt — Current Checkpoint

This checkpoint is a documentation snapshot, not a substitute for fresh execution.

- Package metadata version: **1.0.4**.
- Current repository evidence records **19 pure-logic tests**.
- The tests focus on routing and URL utilities.
- The application is a PySide6 desktop application with multiple download engines and optional backends.
- Standalone Windows packaging is documented in `build_installer.md` but is not proven by this file.

## Implemented / observed

- Modular `grabit/` package with core, dependencies, engines, workers, and GUI layers.
- Plugin-style engine registry.
- Typed core models.
- Explicit dependency-install consent flow.
- Mirror fallback and system package installation are opt-in.
- Filename/path sanitization is implemented.
- Background download/playlist workers are used for blocking work.
- Concurrent batch mode defaults to sequential behavior (`1`).
- Current documentation set includes README, PRODUCT, CHANGELOG, TECH_GAPS, and installer notes.

## Verification boundaries

The 19-test evidence does not prove:

- every engine works against its live platform;
- real network behavior;
- real-display rendering;
- packaged EXE behavior;
- installer/uninstaller behavior;
- all optional dependency combinations;
- third-party executable interoperability.

## Current high-priority gaps

1. Expand automated test coverage beyond the pure routing/URL layer.
2. Run CI on supported operating systems and keep platform regressions visible.
3. Add focused GUI/worker tests for lifecycle, cancellation, and failure isolation.
4. Add controlled tests for dependency-install decisions without performing unrestricted installation.
5. Harden or serialize concurrent yt-dlp archive writes before relying on parallel mode for critical use.
6. Revisit third-party engine dependencies and retire redundant libraries where a stable shared backend can replace them.
7. Perform real Windows packaged-EXE and installer smoke verification.

## Evidence rule

No fresh command output = no fresh verification claim.