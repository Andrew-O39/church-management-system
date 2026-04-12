from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.normalization import normalize_email
from app.db.models.enums import UserRole
from app.db.models.member_profile import MemberProfile
from app.db.models.user import User
from app.modules.members.schemas import MemberAdminPatch, MemberSelfPatch


def _member_filters(
    *,
    search: str | None,
    role: UserRole | None,
    is_active: bool | None,
) -> list[Any]:
    conditions: list[Any] = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )
    if role is not None:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    return conditions


def _filtered_member_ids_stmt(
    *,
    search: str | None,
    role: UserRole | None,
    is_active: bool | None,
) -> Select[tuple[uuid.UUID]]:
    stmt = select(User.id).join(MemberProfile, MemberProfile.user_id == User.id)
    conds = _member_filters(search=search, role=role, is_active=is_active)
    if conds:
        stmt = stmt.where(and_(*conds))
    return stmt


def _member_list_stmt(
    *,
    search: str | None,
    role: UserRole | None,
    is_active: bool | None,
) -> Select[tuple[User]]:
    stmt = (
        select(User)
        .join(MemberProfile, MemberProfile.user_id == User.id)
        .options(selectinload(User.member_profile))
    )
    conds = _member_filters(search=search, role=role, is_active=is_active)
    if conds:
        stmt = stmt.where(and_(*conds))
    return stmt


async def email_in_use_by_other(
    session: AsyncSession,
    *,
    email: str,
    exclude_user_id: uuid.UUID,
) -> bool:
    q = await session.execute(
        select(User.id).where(User.email == email, User.id != exclude_user_id),
    )
    return q.first() is not None


async def count_active_admins_excluding(
    session: AsyncSession,
    exclude_user_id: uuid.UUID,
) -> int:
    """Active administrators other than ``exclude_user_id`` (for last-admin safeguards)."""
    q = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
            User.id != exclude_user_id,
        ),
    )
    return int(q.scalar_one())


async def list_members(
    session: AsyncSession,
    *,
    search: str | None,
    role: UserRole | None,
    is_active: bool | None,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    ids_subq = _filtered_member_ids_stmt(
        search=search,
        role=role,
        is_active=is_active,
    ).subquery()
    count_q = await session.execute(select(func.count()).select_from(ids_subq))
    total = int(count_q.scalar_one())

    list_stmt = _member_list_stmt(search=search, role=role, is_active=is_active)
    list_stmt = (
        list_stmt.order_by(User.full_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(list_stmt)
    users = list(result.scalars().unique().all())
    return users, total


async def get_user_with_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    stmt = (
        select(User)
        .join(MemberProfile, MemberProfile.user_id == User.id)
        .options(selectinload(User.member_profile))
        .where(User.id == user_id)
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def assert_admin_patch_role_safe(
    session: AsyncSession,
    *,
    acting_admin_id: uuid.UUID,
    target: User,
    new_role: UserRole | None,
) -> None:
    if new_role is None:
        return
    if acting_admin_id == target.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )


_LAST_ADMIN_MSG = (
    "Cannot remove administrator access or deactivate the last active administrator. "
    "Promote another user to administrator first, or have another active administrator make this change."
)


async def assert_last_active_admin_protected(
    session: AsyncSession,
    *,
    target: User,
    final_role: UserRole,
    final_active: bool,
) -> None:
    """Ensure at least one active admin remains (multiple admins supported; prevents lockout)."""
    was_active_admin = target.role == UserRole.ADMIN and target.is_active
    will_be_active_admin = final_role == UserRole.ADMIN and final_active
    if not was_active_admin or will_be_active_admin:
        return
    others = await count_active_admins_excluding(session, target.id)
    if others < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_LAST_ADMIN_MSG,
        )


async def apply_admin_patch(
    session: AsyncSession,
    *,
    target: User,
    patch: MemberAdminPatch,
    acting_admin_id: uuid.UUID,
) -> User:
    data = patch.model_dump(exclude_unset=True)
    new_role = data.pop("role", None)
    final_role = new_role if new_role is not None else target.role
    final_active = bool(data["is_active"]) if "is_active" in data else target.is_active

    await assert_admin_patch_role_safe(
        session,
        acting_admin_id=acting_admin_id,
        target=target,
        new_role=new_role,
    )
    await assert_last_active_admin_protected(
        session,
        target=target,
        final_role=final_role,
        final_active=final_active,
    )

    profile = target.member_profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )

    if "email" in data:
        norm = normalize_email(str(data["email"]))
        if await email_in_use_by_other(session, email=norm, exclude_user_id=target.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )
        target.email = norm

    if "full_name" in data and data["full_name"] is not None:
        target.full_name = str(data["full_name"]).strip()

    if "is_active" in data:
        target.is_active = bool(data["is_active"])

    if new_role is not None:
        target.role = new_role

    prof_keys = {
        "phone_number",
        "contact_email",
        "address",
        "marital_status",
        "date_of_birth",
        "baptism_date",
        "confirmation_date",
        "join_date",
        "whatsapp_enabled",
        "sms_enabled",
        "preferred_channel",
    }
    for key in prof_keys:
        if key not in data:
            continue
        val = data[key]
        if key == "contact_email" and val is not None:
            val = normalize_email(str(val))
        setattr(profile, key, val)

    await session.commit()
    await session.refresh(target)
    await session.refresh(profile)
    return target


async def apply_self_patch(
    session: AsyncSession,
    *,
    user: User,
    patch: MemberSelfPatch,
) -> User:
    data = patch.model_dump(exclude_unset=True)
    if "full_name" in data:
        user.full_name = str(data["full_name"]).strip()
    profile = user.member_profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )
    if "phone_number" in data:
        profile.phone_number = data["phone_number"]
    if "contact_email" in data:
        ce = data["contact_email"]
        profile.contact_email = normalize_email(str(ce)) if ce is not None else None
    if "address" in data:
        profile.address = data["address"]
    if "whatsapp_enabled" in data:
        profile.whatsapp_enabled = data["whatsapp_enabled"]
    if "sms_enabled" in data:
        profile.sms_enabled = data["sms_enabled"]
    if "preferred_channel" in data:
        profile.preferred_channel = data["preferred_channel"]

    await session.commit()
    await session.refresh(user)
    await session.refresh(profile)
    return user
