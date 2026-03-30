from __future__ import annotations

from app.db.models.user import User


def sms_phone_from_user_profile(user: User) -> str | None:
    """E.164-style number from app user profile only (never parish registry)."""
    profile = user.member_profile
    if profile is None or not profile.phone_number:
        return None
    raw = profile.phone_number.strip()
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) < 10:
        return None
    return f"+{digits}"
