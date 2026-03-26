from __future__ import annotations


def normalize_email(email: str) -> str:
    """Lowercase and strip for canonical storage and lookup on User.email."""
    return email.strip().lower()
