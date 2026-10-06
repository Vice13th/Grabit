"""Dependency detection and installation.

SECURITY CHANGE vs. the original script
----------------------------------------
The original ``grabitgpt.py`` ran ``bootstrap_dependencies()`` as a
module-level side effect at *import time* — before the user had seen any UI
— which silently invoked ``pip install`` for every missing package, falling
back through a hardcoded list of third-party PyPI mirrors (several outside
the usual trust boundary) using ``--trusted-host`` (which disables TLS
certificate hostname verification for that host). On Linux it could also
shell out to ``sudo apt-get install`` without asking.

That combination — unattended installs, silent mirror fallback, and silent
privilege escalation — is a supply-chain risk: a compromised or MITM'd
mirror could serve a malicious package and the user would have no idea it
even ran. This module keeps the *convenience* (one call tells you exactly
what's missing) but removes the *automatic, silent* part:

* :func:`check_dependencies` only inspects the environment; it never
  installs anything.
* :func:`install_package` / :func:`install_missing` only hit the official
  index by default. Mirror fallback requires ``allow_mirror_fallback=True``
  (an explicit, persisted opt-in — see ``grabit.config.AppConfig``) and,
  when a ``confirm_mirror`` callback is supplied, per-mirror confirmation.
* :func:`try_install_ffmpeg` never calls ``sudo`` unless
  ``allow_sudo_system_install=True``; otherwise it returns the exact command
  the user can run themselves via :func:`manual_install_hint`.
"""
from __future__ import annotations

import importlib
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from grabit.core.block_detect import looks_like_block as _looks_like_block
from grabit.core.proc import no_window_kwargs
from grabit.dependencies.mirrors import PYPI_MIRRORS, Mirror

logger = logging.getLogger(__name__)

MIN_PYTHON = (3, 9)

# (import name, pip package name)
# Only packages the app cannot run *at all* without belong here. Per-platform
# engine libraries (bilix, twitch-archiver, etc.) are OPTIONAL_PACKAGES below:
# each engine already catches ImportError and reports itself unavailable
# (see engines/*.py, grabit.core.exceptions.EngineNotAvailableError), so one
# broken/uninstallable niche package (e.g. bilix's own transitive dependency
# failing to build on a given Python/OS) must never block the whole app from
# starting — it previously did, because everything below was required.
REQUIRED_PACKAGES: List[Tuple[str, str]] = [
    ("PySide6", "PySide6"),
    ("requests", "requests"),
    ("yt_dlp", "yt-dlp"),
    ("gallery_dl", "gallery-dl"),
    ("instaloader", "instaloader"),
    ("yaml", "PyYAML"),
]

UPDATABLE_PACKAGES: List[str] = [
    "yt-dlp", "gallery-dl", "pinterest-dl", "instaloader", "gdown",
    "PyYAML", "bilix", "twitch-archiver", "soundcloud-lib",
    "RedDownloader", "tiktok-downloader-py", "instacapture",
    "civitai-downloader",
]

OPTIONAL_PACKAGES: List[Tuple[str, str]] = [
    ("pinterest_dl", "pinterest-dl"),
    ("gdown", "gdown"),
    ("bilix", "bilix"),
    ("twitch_archiver", "twitch-archiver"),
    ("sclib", "soundcloud-lib"),
    ("RedDownloader", "RedDownloader"),
    ("tiktok_downloader", "tiktok-downloader-py"),
    ("instacapture", "instacapture"),
    ("civitai_downloader", "civitai-downloader"),
    ("streamlink", "streamlink"),
    ("playwright", "playwright"),
]
OPTIONAL_EXECUTABLES: Tuple[str, ...] = ("aria2c", "rclone", "deno")


@dataclass
class DependencyReport:
    missing_required: List[Tuple[str, str]] = field(default_factory=list)
    missing_optional: List[Tuple[str, str]] = field(default_factory=list)
    ffmpeg_available: bool = False
    megadl_available: bool = False
    optional_executables: Dict[str, bool] = field(default_factory=dict)

    @property
    def all_required_satisfied(self) -> bool:
        return not self.missing_required


def is_python_supported() -> bool:
    return sys.version_info >= MIN_PYTHON


def _is_importable(import_name: str) -> bool:
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def is_ffmpeg_available() -> bool:
    if shutil.which("ffmpeg") is not None:
        return True
    return get_ffmpeg_path() is not None


def get_ffmpeg_path() -> Optional[str]:
    """Resolve a usable ffmpeg binary path, including the pure-Python
    ``imageio-ffmpeg`` wheel — which :func:`try_install_ffmpeg` installs by
    default, but which does NOT put anything on PATH. Engines that shell
    out to ``ffmpeg`` must use
    this instead of assuming ``shutil.which("ffmpeg")`` covers every case
    ffmpeg could have been installed through, or they'll wrongly report
    "ffmpeg missing" even right after GrabIt's own install succeeded."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def detect_optional_dependencies() -> Dict[str, bool]:
    """Probe which optional backends are usable right now.

    Real imports are somewhat expensive, so callers should compute this once
    at startup and reuse the dict (e.g. pass it into every
    ``SmartRouter.route()`` call) rather than calling this per URL.
    """
    status: Dict[str, bool] = {}
    for import_name, package_name in OPTIONAL_PACKAGES:
        # Current Streamlink releases require Python 3.10+. Keep GrabIt
        # itself compatible with its Python 3.9 minimum by disabling only
        # this optional integration on Python 3.9.
        if import_name in {"streamlink"} and sys.version_info < (3, 10):
            status[package_name] = False
            continue
        status[package_name] = _is_importable(import_name)
    for exe in OPTIONAL_EXECUTABLES:
        status[exe] = shutil.which(exe) is not None
    return status


def check_dependencies() -> DependencyReport:
    """Read-only environment scan. Never installs anything."""
    return DependencyReport(
        missing_required=[(i, p) for i, p in REQUIRED_PACKAGES if not _is_importable(i)],
        missing_optional=[(i, p) for i, p in OPTIONAL_PACKAGES if not _is_importable(i)],
        ffmpeg_available=is_ffmpeg_available(),
        megadl_available=shutil.which("megadl") is not None,
        optional_executables={exe: shutil.which(exe) is not None for exe in OPTIONAL_EXECUTABLES},
    )


def manual_install_hint(report: DependencyReport) -> str:
    """A copy-pasteable command the user can run themselves instead of
    letting GrabIt touch their environment at all."""
    names = " ".join(p for _, p in report.missing_required)
    return f'"{sys.executable}" -m pip install {names}' if names else ""


def _running_frozen() -> bool:
    """True when running as a PyInstaller-frozen executable, where
    ``sys.executable`` is GrabIt.exe itself — not a real Python
    interpreter. Building ``[sys.executable, "-m", "pip", ...]`` in that
    case doesn't invoke pip at all; it re-launches GrabIt.exe with those as
    its OWN argv, which our argparse parser then rejects with a confusing
    "unrecognized arguments" error that has nothing to do with pip. A
    correctly built release bundles every dependency at build time (see
    build_installer.md's --hidden-import list) specifically so this path
    is never needed there; this function lets us fail honestly instead of
    producing that misleading error when it's hit anyway."""
    return getattr(sys, "frozen", False)


def _run_pip_install(package: str, mirror: Mirror, upgrade: bool, timeout: int) -> Tuple[bool, str]:
    if _running_frozen():
        return False, (
            "Running as a bundled executable — there's no separate Python/pip "
            "to install into. This package should have been bundled at build "
            "time (see build_installer.md); it can't be installed at runtime."
        )
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(package)
    if mirror.index_url:
        cmd.extend(["-i", mirror.index_url])
        if mirror.trusted_host:
            cmd.extend(["--trusted-host", mirror.trusted_host])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False, **no_window_kwargs())
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output[-4000:]
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s"
    except OSError as exc:
        return False, str(exc)


def install_package(
    package: str,
    *,
    allow_mirror_fallback: bool = False,
    confirm_mirror: Optional[Callable[[Mirror], bool]] = None,
    upgrade: bool = True,
    timeout: int = 300,
) -> bool:
    """Install one package, official index first.

    Mirror fallback normally only runs when ``allow_mirror_fallback`` is
    True. Exception: if the official index's failure looks like PyPI
    itself rate-limiting/blocking us (see ``_looks_like_block``) rather
    than an ordinary "package not found"-type failure, mirrors are offered
    anyway — but each one still goes through ``confirm_mirror`` first, so
    this never silently reaches a third-party index without the user
    (or, headless, an explicit yes) actually agreeing to that one mirror.
    """
    official = PYPI_MIRRORS[0]
    logger.info("Installing %s via %s...", package, official.name)
    ok, output = _run_pip_install(package, official, upgrade, timeout)
    if ok:
        logger.info("Installed %s via %s", package, official.name)
        return True
    logger.warning("%s failed for %s: %s", official.name, package,
                    output.strip().splitlines()[-1] if output.strip() else "no output")

    try_mirrors = allow_mirror_fallback or _looks_like_block(output)
    if not try_mirrors:
        logger.error("All attempted sources failed for %s", package)
        return False
    if not allow_mirror_fallback:
        logger.info("%s looks like a PyPI rate-limit/block, not a missing package — offering mirrors for %s",
                     package, package)

    for mirror in PYPI_MIRRORS[1:]:
        if confirm_mirror is not None and not confirm_mirror(mirror):
            logger.info("Skipped mirror %s for %s (declined)", mirror.name, package)
            continue
        logger.info("Installing %s via %s...", package, mirror.name)
        ok, output = _run_pip_install(package, mirror, upgrade, timeout)
        if ok:
            logger.info("Installed %s via %s", package, mirror.name)
            return True
        logger.warning("%s failed for %s: %s", mirror.name, package,
                        output.strip().splitlines()[-1] if output.strip() else "no output")
    logger.error("All attempted sources failed for %s", package)
    return False


def install_missing(
    report: DependencyReport,
    *,
    allow_mirror_fallback: bool = False,
    confirm_mirror: Optional[Callable[[Mirror], bool]] = None,
) -> Dict[str, bool]:
    """Install every required package the report found missing.

    Returns a ``{pip_name: succeeded}`` map so the caller (GUI or CLI) can
    show a per-package result instead of a single pass/fail flag.
    """
    results: Dict[str, bool] = {}
    for _import_name, pip_name in report.missing_required:
        results[pip_name] = install_package(
            pip_name, allow_mirror_fallback=allow_mirror_fallback, confirm_mirror=confirm_mirror,
        )
    return results


def try_install_ffmpeg(*, allow_sudo_system_install: bool = False) -> bool:
    """Best-effort ffmpeg install: prefers the pure-Python ``imageio-ffmpeg``
    wheel (official PyPI only), and only shells out to the system package
    manager with ``sudo``/``brew`` when the caller explicitly allows it."""
    if install_package("imageio-ffmpeg", allow_mirror_fallback=False):
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.exists(exe):
                os.environ["PATH"] = os.path.dirname(exe) + os.pathsep + os.environ.get("PATH", "")
                return True
        except Exception:
            logger.exception("imageio-ffmpeg installed but its bundled binary could not be located")

    if not allow_sudo_system_install:
        logger.info(
            "ffmpeg is still unavailable. Enable 'allow system installs' in "
            "Settings, or run this yourself: sudo apt-get install ffmpeg "
            "(Linux) / brew install ffmpeg (macOS)."
        )
        return False

    system = platform.system().lower()
    if system == "linux" and shutil.which("apt-get"):
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False, **no_window_kwargs())
        return is_ffmpeg_available()
    if system == "darwin" and shutil.which("brew"):
        subprocess.run(["brew", "install", "ffmpeg"], check=False, **no_window_kwargs())
        return is_ffmpeg_available()
    return False
