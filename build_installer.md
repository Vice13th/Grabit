# GrabIt Windows release packaging

The supported packaged target is Windows 10/11 x64. The executable must be built on Windows; this repository does not claim cross-compilation.

## Reproducible build

Use the maintained build entry point:

    powershell -ExecutionPolicy Bypass -File packaging\\build_windows.ps1

The script cleans previous build output, installs the project and PyInstaller, runs the repository tests, and builds dist\\GrabIt.exe.

The packaging configuration is packaging/GrabIt.spec. It explicitly includes the existing GrabIt PNG/ICO assets and required runtime imports. yt-dlp and gallery-dl submodules are collected because their extractor/plugin registries use runtime imports.

Optional engines are not installed just to make the release look complete.

## Application executable

The packaged executable is GrabIt.exe, GUI/no-console, with the existing GrabIt icon and bundled application assets. A successful build does not by itself prove display rendering, installer behavior, uninstallation, or live download behavior.

## Installer

Compile the visible Inno Setup installer with:

    iscc installer.iss

The output name is GrabIt-1.0.4-Windows-x64-Setup.exe.

The installer presents normal user choices for Start Menu/Desktop shortcuts and whether GrabIt should launch after installation. It does not install Python, pip packages, FFmpeg, browsers, services, scheduled tasks, or unrelated system components.

## Dependency model

Required Python dependencies are bundled into the executable at build time. Optional engines remain optional. FFmpeg and external executables such as aria2c, rclone, and megadl are not silently installed by the installer.

## Verification boundary

Use the evidence labels from AGENTS.md. Do not call the packaged release READY until the Windows executable and installer have actually been built and smoke-tested on Windows.
