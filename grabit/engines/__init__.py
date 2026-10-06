"""Engine registry — a lightweight plugin system.

The original script had one hardcoded ``DOWNLOAD_ENGINES = {"yt-dlp":
YtDlpEngine, ...}`` dict living next to the GUI code. Adding an engine meant
finding that dict and remembering to update it. Here, each engine module
registers itself with ``@register_engine("name")`` right where it's
defined, so the engine's file is the single source of truth for both its
implementation and its registry key.

``grabit.core.router.SmartRouter`` still owns the *routing rules* (which
URL patterns map to which engine name) — that's a genuinely separate
concern from "how does the civitai engine work", so it stays a distinct,
explicit step rather than being folded into engine auto-discovery magic.
"""
from __future__ import annotations

from typing import Dict, List, Type

from grabit.engines.base import BaseEngine

_ENGINE_REGISTRY: Dict[str, Type[BaseEngine]] = {}


def register_engine(*names: str):
    """Class decorator: register an engine under one or more names.

    Several route decisions intentionally point at the same implementation
    (e.g. ``"dropbox"`` uses the same class as ``"direct"``), so this
    accepts multiple aliases in one call instead of repeating the decorator.
    """

    def decorator(cls: Type[BaseEngine]) -> Type[BaseEngine]:
        for name in names:
            _ENGINE_REGISTRY[name] = cls
        return cls

    return decorator


def get_engine(name: str) -> Type[BaseEngine] | None:
    return _ENGINE_REGISTRY.get(name)


def available_engine_names() -> List[str]:
    return sorted(_ENGINE_REGISTRY)


# Importing these modules triggers their @register_engine decorators.
# Grouped into a small number of "family" modules (rather than one file per
# platform) to keep the engine count manageable while still isolating each
# backend's third-party import behind its own try/except.
from grabit.engines import ytdlp_engine  # noqa: E402,F401
from grabit.engines import direct_engines  # noqa: E402,F401
from grabit.engines import gallery_engines  # noqa: E402,F401
from grabit.engines import social_video_engines  # noqa: E402,F401
from grabit.engines import transport_engines  # noqa: E402,F401
from grabit.engines import playwright_fallback  # noqa: E402,F401
