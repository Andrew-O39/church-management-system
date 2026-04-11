"""Simple in-memory rate limiting for sensitive auth endpoints (per-process)."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable


class SimpleWindowRateLimiter:
    """
    Fixed window: at most `max_requests` per `window_seconds` per key.
    Not suitable for multi-process horizontal scale (each worker has its own counter).
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._window_start: dict[str, float] = {}
        self._count: dict[str, int] = defaultdict(int)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        start = self._window_start.get(key, now)
        if now - start >= self.window_seconds:
            self._window_start[key] = now
            self._count[key] = 0
        if self._count[key] >= self.max_requests:
            return False
        self._count[key] += 1
        return True


def client_host_key(get_remote: Callable[[], str | None]) -> str:
    ip = get_remote()
    return ip or "unknown"
