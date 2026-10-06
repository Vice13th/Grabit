"""Shared "does this look like a block/rate-limit, not an ordinary
failure?" heuristic — used by both the PyPI install fallback
(:mod:`grabit.dependencies.manager`) and yt-dlp's client-fallback ladder
(:mod:`grabit.engines.ytdlp_engine`), so both call it the same way instead
of drifting into two slightly different definitions of "blocked".
"""
from __future__ import annotations

_BLOCK_SIGNATURES = (
    "429", "too many requests", "temporarily blocked", "rate limit",
    "connection reset", "connection refused", "503 service unavailable",
    "403", "forbidden", "sign in to confirm",
)


def looks_like_block(text: str) -> bool:
    low = (text or "").lower()
    return any(sig in low for sig in _BLOCK_SIGNATURES)
