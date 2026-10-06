# GrabIt Security Policy

## Security posture

GrabIt is a desktop media downloader. Security-sensitive behavior includes dependency installation, filesystem writes, subprocess/external-tool execution, URL handling, browser automation, and optional third-party download engines.

GrabIt does not claim anonymity, DRM circumvention, account-security guarantees, or protection against malicious media servers beyond the explicitly implemented controls.

## Security invariants

1. Missing dependencies are not silently installed without user consent.
2. The default package source is the official PyPI index; mirror fallback requires explicit opt-in.
3. System package-manager installation requires explicit opt-in.
4. Remote filenames and browser-generated filenames must be sanitized before filesystem writes.
5. Download destinations must remain within the configured save directory after normalization.
6. External commands must use structured argument lists rather than unsafe shell interpolation where practical.
7. Cancellation must not be converted into a successful download result.
8. A failing optional engine must not take down unrelated application functionality.
9. Logs must not intentionally include credentials, authentication tokens, or unnecessarily sensitive user data.
10. Security claims must distinguish unit/headless evidence from real-world Windows/macOS/Linux execution.

## Trust boundaries

### User-provided URLs
Treat pasted/imported URLs as untrusted input. Parsing and routing must validate schemes and normalize known forms without executing arbitrary content.

### Remote metadata
Titles, filenames, content-disposition headers, playlist names, and browser download names may be attacker-controlled. Sanitize them before touching the filesystem.

### Download engines
Third-party engines are independent trust boundaries. They may fail, change APIs, or return malformed metadata. Keep engine-specific failures localized.

### External executables
`aria2c`, `rclone`, `megadl`, ffmpeg, and similar tools operate outside Python's direct control. Verify their executable paths and invoke them without shell-string expansion when possible.

### Dependency installation
Installing Python packages changes executable application code and therefore requires explicit user consent and visible failure reporting.

## Known limitations

- No comprehensive security audit of every third-party download engine.
- No hardened multi-writer protection for the shared yt-dlp archive in parallel mode.
- No formal signing/provenance verification for downloaded packages and external executables.
- No dedicated sandbox for untrusted browser automation.
- No production crash-reporting pipeline.
- No exhaustive end-to-end tests against every supported external platform.

These are limitations, not hidden capabilities.

## Vulnerability reporting

For a private development repository, report suspected security issues privately to the project maintainer rather than publishing credentials, tokens, personal data, or working exploit material in a public issue.

Include affected version/commit, reproduction steps, impact, and tested mitigation.

## Security-sensitive changes

Any change affecting installation, path handling, subprocess execution, browser automation, or external downloads should include focused regression coverage and documentation updates.