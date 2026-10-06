"""Central logging configuration.

The original script's only observability was scattered ``print()`` banners
and a bare ``traceback.print_exc()`` inside the download loop — useful while
staring at a terminal, useless once the app is packaged as a windowed .exe
with no visible console. This module gives every part of the app a real
logger (``logging.getLogger(__name__)``) that writes to both the console and
a rotating-by-run log file the user can attach to a bug report.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(data_dir: Path, *, verbose: bool = False) -> logging.Logger:
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "grabit.log"

    root = logging.getLogger("grabit")
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.handlers.clear()  # safe to call again (e.g. from tests) without duplicating handlers

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    root.info("Logging to %s", log_file)
    return root
