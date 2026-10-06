# GrabIt Windows packaging

The release target is Windows 10/11 x64.

## Build environment

The repository supports Python 3.9+, but the release build uses Python 3.11 as the packaging baseline because it is covered by CI and provides a conservative runtime for the current dependency graph.

Builds are performed on Windows. No cross-compilation is assumed.

## Build

From a clean checkout run: powershell -ExecutionPolicy Bypass -File packaging\\build_windows.ps1

The script removes previous build/dist directories, installs PyInstaller and the project, runs the repository test suite, and builds dist\\GrabIt.exe from packaging\\GrabIt.spec.

Optional engines are not installed by the build script. They remain optional and are not required for the core packaged application.

## Installer

After dist\\GrabIt.exe has been built, compile installer.iss with Inno Setup.

The installer is a normal visible wizard. It does not install Python, pip packages, FFmpeg, browsers, services, scheduled tasks, or other dependencies.

## Verification boundary

A successful build proves only that the executable was produced and source tests passed. It does not prove real-display behavior, installer behavior, uninstallation, or live download behavior until those checks are actually run on Windows.
