# GrabIt Windows release packaging

The supported packaged target is Windows 10/11 x64. The executable must be built on Windows; this repository does not claim cross-compilation.

## Reproducible build

Use the maintained build entry point:

    powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1

The script creates a fresh Python 3.11 packaging environment and installs only the dependencies listed in `requirements-packaging.txt`, plus PyInstaller and pytest. It does not install the full optional engine dependency set.

The packaging configuration is `packaging/GrabIt.spec`. It includes the existing GrabIt PNG/ICO assets and relies on normal PyInstaller analysis rather than a blanket hidden-import or recursive collection list.

## Dependency model

Required runtime dependencies are intentionally small and are listed in `requirements.txt` / `pyproject.toml`.

Optional engines are declared in `requirements-optional.txt` and the `extra` project extra. Their packages are not installed into the Windows packaging environment simply to make optional features appear bundled.

The packaged application must continue to report unavailable optional backends honestly rather than silently installing them.

FFmpeg and external executables such as aria2c, rclone, and megadl are not silently installed by the installer.

## Application executable

The packaged executable is `GrabIt.exe`, GUI/no-console, with the existing GrabIt icon and bundled application assets. A successful build does not by itself prove display rendering, installer behavior, uninstallation, or live download behavior.

## Installer

Compile the visible Inno Setup installer with:

    iscc installer.iss

The output name is `GrabIt-1.0.4-Windows-x64-Setup.exe`.

The installer presents normal user choices for Start Menu/Desktop shortcuts and whether GrabIt should launch after installation. It does not install Python, pip packages, FFmpeg, browsers, services, scheduled tasks, or unrelated system components.

## Verification boundary

Use the evidence labels from AGENTS.md. Do not call the packaged release READY until the Windows executable and installer have actually been built and smoke-tested on Windows.
