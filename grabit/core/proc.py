"""Windows-only: prevent child processes from flashing a console window.

``subprocess.run``/``Popen`` create a new console window for the child by
default on Windows *even when the parent has none* (i.e. even when GrabIt
itself was launched via ``GrabIt.pyw`` or a ``--noconsole`` build) — that's
a Windows default, not something inherited from the parent. Every
subprocess call in the app (pip installs, yt-dlp/aria2c/rclone/megadl
invocations, sudo/brew) must pass these kwargs to stay console-free.
"""
from __future__ import annotations

import subprocess
import sys


def no_window_kwargs() -> dict:
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}
