"""
One-time / idempotent dev bootstrap for the first admin user.

Run after migrations with BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD set.
Does not create duplicate admins for the same email; safe to re-run.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.normalization import normalize_email
from app.core.security import hash_password
from app.core.settings import settings
from app.db.models.enums import PreferredChannel, UserRole
from app.db.models.member_profile import MemberProfile
from app.db.models.user import User
from app.db.session import async_session_factory
from app.modules.auth import service as auth_service


async def run() -> int:
    raw_email = settings.BOOTSTRAP_ADMIN_EMAIL
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    if not raw_email or not password:
        print(
            "bootstrap-admin: skipping (set BOOTSTRAP_ADMIN_EMAIL and "
            "BOOTSTRAP_ADMIN_PASSWORD to create or promote an admin)",
            file=sys.stderr,
        )
        return 0

    if len(password) < 8:
        print("bootstrap-admin: password must be at least 8 characters", file=sys.stderr)
        return 1

    email = normalize_email(raw_email)

    async with async_session_factory() as session:
        existing = await auth_service.get_user_by_email(session, email)
        if existing is not None:
            if existing.role == UserRole.ADMIN:
                print(f"bootstrap-admin: admin already exists for {email!r} — skipping")
                return 0
            existing.role = UserRole.ADMIN
            await session.commit()
            print(f"bootstrap-admin: promoted existing user {email!r} to admin")
            return 0

        user = User(
            full_name="Bootstrap Admin",
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            role=UserRole.ADMIN,
        )
        user.member_profile = MemberProfile(
            whatsapp_enabled=True,
            sms_enabled=True,
            preferred_channel=PreferredChannel.WHATSAPP,
        )
        session.add(user)
        await session.commit()
        print(f"bootstrap-admin: created admin {email!r}")
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))
