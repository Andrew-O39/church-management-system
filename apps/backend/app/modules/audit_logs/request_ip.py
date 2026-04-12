from __future__ import annotations

from starlette.requests import Request


def client_ip_from_request(request: Request) -> str | None:
    """Best-effort client IP (respects X-Forwarded-For when present)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    if request.client:
        return request.client.host
    return None
