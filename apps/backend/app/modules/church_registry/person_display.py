"""Display and identity helpers for ChurchMember + optional linked User.

church_member_id: canonical parish person (domain, attendance, ministries, volunteers).
user_id: login account (authentication only). Domain code should resolve User.member_id → ChurchMember
before applying business rules.
"""

from __future__ import annotations

import uuid

from app.db.models.church_member import ChurchMember
from app.db.models.user import User


def normalize_full_name_key(full_name: str) -> str:
    """Lowercase, collapse internal whitespace — used for soft duplicate detection."""
    return " ".join(full_name.strip().lower().split())


def contact_email(*, church_member: ChurchMember, linked_user: User | None) -> str | None:
    """Prefer registry email on ChurchMember; if unset, use linked User.email (login)."""
    if church_member.email and church_member.email.strip():
        return church_member.email.strip().lower()
    if linked_user is not None:
        return linked_user.email
    return None


def linked_account_fields(linked_user: User | None) -> tuple[uuid.UUID | None, str | None, str | None]:
    """(user_id, user_full_name, user_email) for API rows; all None when no linked account."""
    if linked_user is None:
        return None, None, None
    return linked_user.id, linked_user.full_name, linked_user.email
