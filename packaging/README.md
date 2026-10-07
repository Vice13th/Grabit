# GrabIt Windows packaging

The release target is Windows 10/11 x64.

## Build environment

The repository supports Python 3.9+, but the release build uses Python 3.11 as the packaging baseline because it is covered by CI and is the supported Windows packaging baseline.

The packaging script creates a fresh `.venv-grabit-release` virtual environment for every build. It installs only `requirements-packaging.txt`, PyInstaller, pytest, and the local GrabIt package with `--no-deps`.

This isolation is intentional: optional engine packages must not contaminate the PyInstaller analysis graph.

## Build

From a clean checkout run:

    powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1

The script:

1. removes previous build/dist output and the temporary packaging virtual environment;
2. creates a fresh Python 3.11 virtual environment;
3. installs the minimal packaging dependency set;
4. installs PyInstaller and pytest;
5. installs GrabIt itself with `--no-deps`;
6. runs a core-only import probe;
7. records the installed packaging environment;
8. rejects unexpected heavy packages such as Torch/TensorFlow/Gradio/SciPy;
9. runs the repository tests;
10. builds `dist\GrabIt.exe` from `packaging\GrabIt.spec`.

Optional engine dependencies are deliberately absent from the packaging environment. They remain available for separate source/development environments.

## Dependency boundary

Required runtime dependencies are listed in `requirements.txt` and `pyproject.toml`.

Optional engine integrations are listed in `requirements-optional.txt` and the `extra` project extra.

The packaging environment uses `requirements-packaging.txt` so the Windows release artifact is not affected by optional backend dependency graphs.

## Installer

After `dist\GrabIt.exe` has been built, compile `installer.iss` with Inno Setup.

The installer is a normal visible wizard. It does not install Python, pip packages, FFmpeg, browsers, services, scheduled tasks, or other dependencies.

## Verification boundary

A successful build proves that the executable was produced and source tests passed. It does not prove real-display behavior, installer behavior, uninstallation, or live download behavior until those checks are actually run on Windows.
