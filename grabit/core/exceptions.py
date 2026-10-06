"""Cooperative control-flow exceptions used by the download workers.

Engines call ``options.control_checkpoint()`` periodically (inside progress
hooks, read loops, etc.). That checkpoint blocks while paused and raises
:class:`DownloadCancelled` once the user cancels, so a long-running engine
call unwinds promptly instead of finishing an unwanted download.
"""


class DownloadPaused(Exception):
    """Internal marker for a cooperative pause checkpoint."""


class DownloadCancelled(Exception):
    """Internal marker for cooperative cancellation."""


class EngineNotAvailableError(Exception):
    """Raised when a resolved engine has no usable backend installed.

    Distinct from a plain ``ImportError`` so callers can tell "the platform
    was recognized but its backend isn't installed" apart from "our own code
    has a bug" without inspecting exception message text.
    """
