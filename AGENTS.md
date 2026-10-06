# GrabIt — Agent / Engineering Contract

## Source of truth

The repository is authoritative. Inspect the current tree, source, tests, packaging metadata, CHANGELOG, PRODUCT, TECH_GAPS, and this document before making a substantive change.

Never treat chat history, old reports, generated output, or remembered state as stronger evidence than the repository.

Use evidence labels:

- VERIFIED — directly executed and observed with fresh evidence.
- OBSERVED — directly present in source or repository metadata, but not executed for the claim.
- UNVERIFIED — requires an environment, dependency, display, network, or artifact that was not exercised.
- FAILED — fresh execution shows the claim is false.
- INFERRED — reasoned conclusion, not direct evidence.

No receipt → no epistemic upgrade.

## Execution contract

Use:

INSPECT → REPORT → IMPLEMENT → TEST → VERIFY → DOCUMENT

Rules:
1. Make the smallest safe change that satisfies the requirement.
2. Preserve existing behavior unless the task explicitly changes it.
3. Never fabricate test results, downloads, packaging results, UI observations, network behavior, dependency availability, or release status.
4. Do not claim a real-display, real-network, or packaged-executable result from a headless/unit test.
5. Do not loop on the same failed action. After a failure, inspect the cause and change the hypothesis or stop with the blocker.
6. Do not silently broaden scope.
7. Do not silently add new runtime dependencies when a standard-library or existing-dependency solution is sufficient.
8. Security-sensitive behavior must fail safely and must not become less explicit merely to improve UX.
9. Keep user-controlled installation and external-tool execution explicit.
10. Prefer deterministic, testable pure logic at the core; keep Qt-specific behavior at the GUI boundary.

## Architecture boundaries

- `grabit/core/` should remain free of Qt and heavy engine imports where practical.
- URL parsing/routing must not perform network access.
- GUI code belongs under `grabit/gui/`.
- Long-running or blocking work must not execute on the Qt GUI thread.
- Engine failures must be contained so one backend does not crash unrelated application functionality.
- Cancellation must remain distinguishable from ordinary download failure.
- Dependency installation must remain explicit and user-visible.
- Mirror fallback and system package-manager installation are opt-in capabilities.
- Paths derived from remote metadata must be sanitized before filesystem writes.

## Packaging

The supported source-tree path is `pip install -e .`.
Windows standalone packaging is performed on Windows and is documented in `build_installer.md`.
Do not claim a packaged artifact is valid until the actual executable and installer have been built and smoke-tested in the target environment.

## Testing

Baseline:

`python -m pytest -q`

Current repository evidence records 19 pure-logic tests. The test count is not proof of a fresh run.

For changes affecting GUI lifecycle, worker/thread behavior, packaging, or optional engines, add or execute focused tests appropriate to the changed boundary.

Headless Qt tests do not prove visual correctness on a real display.

Network/engine integration tests should use controlled fixtures or mocks unless real integration is explicitly required and safely reproducible.

## Documentation synchronization

Keep these consistent with actual repository state:

- `README.md`
- `PRODUCT.md`
- `CHANGELOG.md`
- `TECH_GAPS.md`
- `CHECKPOINT.md`
- `ROADMAP.md`
- `SECURITY.md`
- `build_installer.md`

Do not leave stale version numbers, test counts, platform claims, or resolved gaps in those files.

## Completion report

At the end of a task report:

1. files changed;
2. behavior or documentation changed;
3. exact tests actually run;
4. exact build/artifact evidence, if any;
5. remaining UNVERIFIED areas;
6. blockers or follow-up work.