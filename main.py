#!/usr/bin/env python3
"""GrabIt entry point.

Run this file directly (``python main.py``) to launch the app. Command-line
options (``--yes``, ``--no-install``, ``--verbose``) are documented in
``grabit.app`` / ``python main.py --help``.

To run GrabIt in portable mode (all data kept in ``grab_data/`` next to this
file instead of your home directory), create an empty file named
``portable.flag`` in this same directory before first launch.
"""
import sys
from pathlib import Path

# Allow running this file directly from a source checkout without installing
# the package first.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grabit.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
