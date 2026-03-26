from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.normalization import normalize_email
from app.db.models.enums import PreferredChannel, UserRole
from app.db.models.member_profile import MemberProfile
from app.db.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    normalized_email = normalize_email(email)
    q = await session.execute(select(User).where(User.email == normalized_email))
    return q.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    q = await session.execute(select(User).where(User.id == user_id))
    return q.scalar_one_or_none()


async def create_registered_user(
    session: AsyncSession,
    *,
    full_name: str,
    email: str,
    password: str,
) -> User:
    """Create user + empty member profile. Caller must ensure email is available."""
    normalized_email = normalize_email(email)

    user = User(
        full_name=full_name,
        email=normalized_email,
        password_hash=hash_password(password),
        is_active=True,
        role=UserRole.MEMBER,
    )
    user.member_profile = MemberProfile(
        whatsapp_enabled=True,
        sms_enabled=True,
        preferred_channel=PreferredChannel.WHATSAPP,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user