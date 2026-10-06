"""Typed data structures shared across the app.

The original script passed raw ``dict`` objects between the router, the
worker thread and every engine. That works, but a typo in a key name (or a
key an engine forgot to read) fails silently at runtime instead of at
review/import time. Using dataclasses here gives autocompletion, makes every
field's default explicit in one place, and turns "engine returned the wrong
shape" into an immediate ``TypeError`` instead of a mysterious ``None``
three calls later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

ProgressCallback = Callable[[float], None]
StatusCallback = Callable[[str, str], None]
CheckpointCallback = Callable[[], None]
CancelledPredicate = Callable[[], bool]


@dataclass(frozen=True)
class RouteDecision:
    """The result of :meth:`SmartRouter.route` for a single URL."""

    engine: Optional[str]
    kind: Optional[str]
    platform: str
    color: str
    icon: str

    @property
    def is_known(self) -> bool:
        return self.engine is not None

    # Kept for any call site that still expects dict-style access
    # (e.g. code shared with older tests or notebooks).
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@dataclass
class DownloadOptions:
    """Per-download configuration passed from the GUI into an engine.

    ``extra`` absorbs any engine-specific knob that doesn't deserve a
    top-level field yet; engines should still prefer a named field once a
    setting is used by more than one call site.
    """

    output_mode: str = "video"                 # "video" | "audio"
    video_quality: str = "best"                 # "best" | "2160" | ... | "360"
    video_format: str = "mp4"                   # "mp4" | "mkv" | "webm"
    audio_quality: str = "192"                  # kbps, as a string
    audio_format: str = "mp3"                   # "mp3" | "m4a" | "opus" | "flac" | "wav"
    playlist_mode: Optional[str] = None          # None | "yes" | "no"

    gallery_min_size: int = 500
    ig_download_pictures: bool = True
    ig_download_videos: bool = True

    # Wired in by DownloadThread right before a run; engines should treat
    # these as read-only.
    download_archive: Optional[str] = None
    control_checkpoint: Optional[CheckpointCallback] = None
    cancel_requested: Optional[CancelledPredicate] = None

    extra: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style ``.get`` so engines read either named fields or
        ad-hoc ``extra`` values through one uniform call."""
        if hasattr(self, key) and key != "extra":
            return getattr(self, key)
        return self.extra.get(key, default)

    def checkpoint(self) -> None:
        """Call the cooperative pause/cancel checkpoint, if one is wired."""
        if self.control_checkpoint is not None:
            self.control_checkpoint()

    def is_cancelled(self) -> bool:
        return bool(self.cancel_requested and self.cancel_requested())


@dataclass
class DownloadResult:
    """What every engine's ``download()`` returns."""

    success: bool
    message: str = ""
    cancelled: bool = False
    count: Optional[int] = None
    title: Optional[str] = None

    @classmethod
    def ok(cls, message: str, **extra: Any) -> "DownloadResult":
        return cls(success=True, message=message, **extra)

    @classmethod
    def fail(cls, message: str, **extra: Any) -> "DownloadResult":
        return cls(success=False, message=message, **extra)

    @classmethod
    def cancelled_result(cls, message: str = "Download cancelled") -> "DownloadResult":
        return cls(success=False, message=message, cancelled=True)
