# GrabIt — Roadmap

## P0 — correctness and testability

- Keep the pure-core contract stable: routing and URL parsing remain deterministic and offline.
- Add regression tests for path sanitization, dependency decisions, cancellation, retry boundaries, and download-result classification.
- Add CI coverage for Windows, Linux, and macOS.
- Add compile/static checks that catch import and syntax regressions early.

## P1 — desktop reliability

- Add focused headless Qt tests for worker lifecycle, cancellation, exception propagation, and window teardown.
- Add tests for settings persistence and malformed settings recovery.
- Add controlled dependency-manager tests for official-index vs mirror fallback decisions.
- Exercise optional-engine availability handling without requiring every optional package.

## P2 — packaging and integration

- Build and smoke-test the Windows standalone EXE on Windows.
- Build and verify the Inno Setup installer/uninstaller.
- Verify icon/assets, no-console behavior, startup, download flow, cancellation, and clean shutdown.
- Test a representative sample of external engines against controlled/live endpoints.

## P3 — architecture hardening

- Decide whether parallel yt-dlp archive access needs locking or per-worker isolation.
- Audit the smaller per-platform dependencies and consolidate onto maintained backends where behavior is equivalent and regression coverage exists.
- Evaluate Nuitka vs PyInstaller using measured startup/build/package-size results.
- Add optional, privacy-conscious crash diagnostics only if the product explicitly opts into them.

## Out of scope until separately justified

- Claims of anonymity or untraceability.
- Unrestricted automatic dependency installation.
- Silent system package-manager changes.
- Treating headless tests as visual proof.
- Treating a single live-engine success as proof that every supported platform works.