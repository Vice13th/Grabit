#!/usr/bin/env pythonw
"""No-console launcher for Windows.

Double-clicking a .py file runs it with python.exe, which always opens a
terminal window - that's inherent to python.exe, not something the app
itself can suppress. .pyw files are launched with pythonw.exe instead,
which has no console attached at all, so this is the correct fix rather
than a workaround inside main.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grabit.app import main

if __name__ == "__main__":
    sys.exit(main())
