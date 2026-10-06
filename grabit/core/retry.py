"""A small, dependency-free retry decorator with exponential backoff.

Several engines in the original script made a single network attempt and
surfaced any transient failure (a dropped connection, a 503, a DNS hiccup)
straight to the user as a hard failure. This decorator gives those engines a
uniform, bounded retry policy without duplicating try/except/sleep logic in
each one.

It deliberately never swallows :class:`DownloadCancelled` — a user asking to
cancel must win immediately, not after a retry's backoff sleep.
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Tuple, Type, TypeVar

from grabit.core.exceptions import DownloadCancelled

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


def retry_on_exception(
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    attempts: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable[[F], F]:
    """Retry the wrapped call up to ``attempts`` times on ``exceptions``.

    Args:
        exceptions: exception types worth retrying (e.g. network errors).
        attempts: total attempts including the first, must be >= 1.
        base_delay: seconds to wait before the second attempt.
        backoff: multiplier applied to the delay after each failed attempt.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc: BaseException | None = None
            for attempt in range(1, max(1, attempts) + 1):
                try:
                    return func(*args, **kwargs)
                except DownloadCancelled:
                    raise
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    if attempt >= attempts:
                        break
                    logger.warning(
                        "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        getattr(func, "__qualname__", func.__name__),
                        attempt, attempts, exc, delay,
                    )
                    time.sleep(delay)
                    delay *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
