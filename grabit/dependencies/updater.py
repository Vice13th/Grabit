"""Check installed engine libraries against the latest PyPI release.

Version *checking* only talks to ``pypi.org`` (read-only, no installation)
and is always safe to run. Version *installation* reuses
:func:`grabit.dependencies.manager.install_package`, so it inherits the same
official-index-by-default / opt-in-mirror-fallback behavior.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import requests

from grabit.core.proc import no_window_kwargs
from grabit.dependencies.manager import UPDATABLE_PACKAGES, install_package
from grabit.dependencies.mirrors import Mirror

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PackageUpdate:
    installed: str
    latest: str


def _get_installed_version(package: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True, text=True, check=False, **no_window_kwargs(),
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        logger.exception("Could not query installed version of %s", package)
    return None


def _get_latest_version(package: str, timeout: float = 10.0) -> Optional[str]:
    try:
        response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=timeout)
        if response.status_code == 200:
            return response.json()["info"]["version"]
    except (requests.RequestException, ValueError, KeyError):
        logger.warning("Could not fetch latest PyPI version for %s", package)
    return None


def check_updates() -> Dict[str, PackageUpdate]:
    """Return every updatable package whose installed version differs from
    the latest one published on PyPI."""
    results: Dict[str, PackageUpdate] = {}
    for pkg in UPDATABLE_PACKAGES:
        installed = _get_installed_version(pkg)
        latest = _get_latest_version(pkg)
        if installed and latest and installed != latest:
            results[pkg] = PackageUpdate(installed=installed, latest=latest)
    return results


def update_all_packages(
    *,
    allow_mirror_fallback: bool = False,
    confirm_mirror: Optional[Callable[[Mirror], bool]] = None,
) -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    for pkg in UPDATABLE_PACKAGES:
        logger.info("Updating %s...", pkg)
        results[pkg] = install_package(
            pkg, allow_mirror_fallback=allow_mirror_fallback, confirm_mirror=confirm_mirror,
        )
    return results
