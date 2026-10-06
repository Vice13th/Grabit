"""The contract every download engine implements.

The original script relied on duck typing: any class with a matching
``download(url, save_dir, options, progress_cb, status_cb)`` static method
worked, because ``DOWNLOAD_ENGINES`` just held classes and called
``.download(...)`` on whichever one the router picked. That's fine until an
engine's signature drifts — nothing catches it until that exact engine runs.

Making it an ``ABC`` doesn't change runtime behavior for correct engines,
but a subclass that forgets to implement ``download`` now fails loudly
(``TypeError`` at class-definition time) instead of only when a user
happens to hit that platform.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from grabit.core.models import DownloadOptions, DownloadResult, ProgressCallback, StatusCallback


class BaseEngine(ABC):
    """Common interface for a single download backend."""

    @staticmethod
    @abstractmethod
    def download(
        url: str,
        save_dir: str,
        options: DownloadOptions,
        progress_cb: ProgressCallback,
        status_cb: StatusCallback,
    ) -> DownloadResult:
        """Download ``url`` into ``save_dir``.

        Implementations should call ``options.checkpoint()`` at any point
        where pausing/cancelling is safe (e.g. inside a chunked read loop or
        a library's own progress hook), and let
        :class:`grabit.core.exceptions.DownloadCancelled` propagate rather
        than catching it — the worker thread relies on that exception to
        stop promptly.
        """
        raise NotImplementedError
