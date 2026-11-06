"""Fixed-window rate limiter backed by the Django cache (LocMem or Redis)."""
from __future__ import annotations

import time

from django.conf import settings
from django.core.cache import cache


class RateLimited(Exception):
    def __init__(self, scope: str, retry_after: int):
        super().__init__(f"Rate limit exceeded for {scope}")
        self.scope = scope
        self.retry_after = retry_after


def hit(scope: str, identity: str, limit: int | None = None, window: int | None = None) -> None:
    """Register one attempt; raise RateLimited when the window budget is exhausted."""
    default_limit, default_window = settings.RATE_LIMITS.get(scope, (30, 60))
    limit = limit or default_limit
    window = window or default_window
    bucket = int(time.time() // window)
    key = f"rl:{scope}:{identity}:{bucket}"
    if cache.add(key, 1, timeout=window + 1):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:  # key evicted between add() and incr()
            cache.set(key, 1, timeout=window + 1)
            count = 1
    if count > limit:
        retry_after = window - int(time.time() % window)
        raise RateLimited(scope, retry_after)
