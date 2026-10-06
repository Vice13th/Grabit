"""Application bootstrap.

Sequence:

1. Load config + logging (no third-party imports needed for this).
2. *Report* what's missing (never installs anything automatically) — this
   check is a handful of local ``importlib.import_module`` probes, so it's
   fast and makes no network call; nothing is ever re-downloaded on a run
   where everything required is already present.
3. If something required is missing, ask — via a small tkinter window
   (stdlib, no terminal involved) rather than a console prompt, since
   PySide6 itself can be one of the missing packages and we can't show a
   Qt dialog before Qt is installed. ``--yes`` skips the prompt for
   non-interactive use; ``--no-install`` never installs. If tkinter itself
   isn't available, this falls back to the original console prompt rather
   than failing outright.
4. Only past that point do we import anything from ``grabit.gui`` (which
   transitively imports PySide6). An animated splash screen covers the
   (already fast) optional-dependency probe and window construction so
   startup has a deliberate branded moment instead of a frozen blank window.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grabit import __version__
from grabit.config import AppConfig
from grabit.logging_setup import configure_logging


def _patch_streams_for_frozen_noconsole() -> None:
    """A ``--noconsole``/``--windowed`` PyInstaller build has no console at
    all, so Python sets ``sys.stdout``/``sys.stderr`` to ``None`` — not a
    closed stream, literally ``None``. Any third-party library that does a
    bare ``print()`` or ``sys.stderr.write()``/``.flush()`` without checking
    for that crashes outright. Confirmed in the wild: pinterest-dl's tqdm
    progress bar does exactly that (``sys.stderr.flush()`` ->
    ``AttributeError: 'NoneType' object has no attribute 'flush'``), taking
    down the whole Pinterest engine on every download in a frozen build.
    Giving both streams a harmless no-op file-like object fixes this for
    every engine at once, not just Pinterest, without needing a console."""
    import io

    class _NullStream(io.TextIOBase):
        def write(self, *a, **k):
            return 0

        def flush(self):
            pass

        def isatty(self):
            return False

    if sys.stdout is None:
        sys.stdout = _NullStream()
    if sys.stderr is None:
        sys.stderr = _NullStream()


def _console_confirm(prompt: str) -> bool:
    try:
        reply = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return reply in ("y", "yes")


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="grabit", description="GrabIt — Universal Media Downloader")
    parser.add_argument("--yes", action="store_true",
                         help="Install missing required packages without prompting (official PyPI index only).")
    parser.add_argument("--no-install", action="store_true",
                         help="Never install anything; print the pip command and exit if something is missing.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    parser.add_argument("--version", action="version", version=f"GrabIt {__version__}")
    return parser.parse_args(argv)


def _install_with_console(report, config: AppConfig, logger) -> bool:
    from grabit.dependencies.manager import install_missing

    if not _console_confirm("Install them now from the official PyPI index?"):
        return False
    confirm_mirror = lambda mirror: _console_confirm(
        f"Official index failed — try the {mirror.name} mirror ({mirror.index_url})?"
    )
    results = install_missing(report, allow_mirror_fallback=config.allow_mirror_fallback, confirm_mirror=confirm_mirror)
    failed = [pkg for pkg, ok in results.items() if not ok]
    if failed:
        logger.error("Failed to install: %s", ", ".join(failed))
        print(f"Could not install: {', '.join(failed)}. See the log for details.")
        return False
    return True


def _install_with_gui(report, config: AppConfig, logger) -> bool:
    """tkinter dependency-install window; falls back to the console prompt
    if tkinter isn't available in this Python install."""
    try:
        from grabit.bootstrap_ui import confirm_and_install
        import tkinter.messagebox as messagebox
    except Exception:
        return _install_with_console(report, config, logger)

    from grabit.dependencies.manager import install_missing

    def _confirm_mirror(mirror) -> bool:
        return messagebox.askyesno(
            "GrabIt — mirror fallback",
            f"Official index failed for a package — try the {mirror.name} mirror?\n{mirror.index_url}",
        )

    def _install_fn(log):
        handler = logging.Handler()
        handler.setLevel(logging.INFO)
        handler.emit = lambda record: log(record.getMessage())
        dep_logger = logging.getLogger("grabit.dependencies.manager")
        dep_logger.addHandler(handler)
        try:
            return install_missing(
                report, allow_mirror_fallback=config.allow_mirror_fallback, confirm_mirror=_confirm_mirror,
            )
        finally:
            dep_logger.removeHandler(handler)

    names = [p for _, p in report.missing_required]
    try:
        outcome = confirm_and_install(names, _install_fn)
    except Exception:
        logger.exception("Dependency-install window failed; falling back to console")
        return _install_with_console(report, config, logger)

    if outcome is None:
        return False
    failed = [pkg for pkg, ok in outcome.items() if not ok]
    if failed:
        logger.error("Failed to install: %s", ", ".join(failed))
    return not failed


def _ensure_dependencies(config: AppConfig, args, logger) -> bool:
    from grabit.dependencies.manager import check_dependencies, manual_install_hint

    report = check_dependencies()
    if report.all_required_satisfied:
        return True

    names = ", ".join(p for _, p in report.missing_required)
    logger.info("Missing %d required package(s): %s", len(report.missing_required), names)

    if args.no_install:
        print(f"GrabIt needs: {names}\nRun this yourself, then start GrabIt again:")
        print(f"  {manual_install_hint(report)}")
        return False

    if args.yes:
        from grabit.dependencies.manager import install_missing
        results = install_missing(report, allow_mirror_fallback=config.allow_mirror_fallback)
        failed = [pkg for pkg, ok in results.items() if not ok]
        if failed:
            logger.error("Failed to install: %s", ", ".join(failed))
        return not failed

    ok = _install_with_gui(report, config, logger)
    if not ok:
        print(f"Not installed. Run this yourself, then start GrabIt again:")
        print(f"  {manual_install_hint(report)}")
    return ok


def main(argv=None) -> int:
    _patch_streams_for_frozen_noconsole()
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    # main.py at the project root is the "script" for portable-mode purposes,
    # matching the original single-file script's own-directory check.
    script_dir = Path(sys.argv[0]).resolve().parent
    config = AppConfig.load(script_dir)
    logger = configure_logging(config.data_dir, verbose=args.verbose)
    logger.info("GrabIt %s starting (portable=%s)", __version__, config.portable)

    from grabit.dependencies.manager import is_python_supported, MIN_PYTHON
    if not is_python_supported():
        print(f"GrabIt requires Python {'.'.join(map(str, MIN_PYTHON))}+ (found {sys.version.split()[0]}).")
        return 1

    if not _ensure_dependencies(config, args, logger):
        return 1

    # Only now do we touch Qt.
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from grabit.gui.styles import DARK_QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    icon_path = Path(__file__).parent / "gui" / "assets" / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from grabit.gui.splash import SplashScreen
    splash = SplashScreen()
    app.processEvents()

    splash.set_status("Detecting optional backends...", 30)
    app.processEvents()
    from grabit.dependencies.manager import detect_optional_dependencies
    optional_status = detect_optional_dependencies()
    logger.info("Optional backends available: %s",
                ", ".join(sorted(k for k, v in optional_status.items() if v)) or "none")

    splash.set_status("Building interface...", 70)
    app.processEvents()
    from grabit.gui.main_window import GrabItApp
    window = GrabItApp(config, optional_status)

    splash.set_status("Ready", 100)
    from PySide6.QtCore import QTimer
    QTimer.singleShot(350, lambda: splash.finish(window))
    return app.exec()
