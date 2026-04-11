"""Rate limit dependency for /auth/login and /auth/register."""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status

from app.core.rate_limit import SimpleWindowRateLimiter
from app.core.settings import settings

logger = logging.getLogger(__name__)

_limiter: SimpleWindowRateLimiter | None = None


def reset_auth_rate_limiter_for_tests() -> None:
    """Clear per-process counters (used by pytest autouse fixture)."""
    global _limiter
    _limiter = None


def _get_limiter() -> SimpleWindowRateLimiter:
    global _limiter
    max_r = max(0, settings.AUTH_RATE_LIMIT_PER_MINUTE)
    if _limiter is None or _limiter.max_requests != max_r:
        _limiter = SimpleWindowRateLimiter(max_r or 1, 60)
    return _limiter


async def enforce_auth_rate_limit(request: Request) -> None:
    """Reject with 429 if this IP exceeded the per-minute auth attempt budget."""
    lim = settings.AUTH_RATE_LIMIT_PER_MINUTE
    if lim <= 0:
        return
    ip = request.client.host if request.client else "unknown"
    limiter = _get_limiter()
    if not limiter.allow(ip):
        logger.warning("auth rate limit exceeded ip=%s", ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many sign-in attempts. Please wait a minute and try again.",
        )
