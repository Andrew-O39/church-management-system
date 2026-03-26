from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.normalization import normalize_email
from app.db.models.enums import MinistryRoleInMinistry
from app.db.models.ministry_group import MinistryGroup
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.modules.auth import service as auth_service
from app.modules.ministries.schemas import (
    MinistryCreate,
    MinistryDetailResponse,
    MinistryListItem,
    MinistryMemberRow,
    MinistryMembershipCreate,
    MinistryMembershipPatch,
    MinistryPatch,
    MyMinistryItem,
)


def normalize_ministry_name_key(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def display_ministry_name(name: str) -> str:
    s = name.strip()
    return re.sub(r"\s+", " ", s)


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await auth_service.get_user_by_id(session, user_id)


async def assert_user_exists(session: AsyncSession, user_id: uuid.UUID) -> User:
    u = await get_user_by_id(session, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return u


async def get_ministry(session: AsyncSession, ministry_id: uuid.UUID) -> MinistryGroup | None:
    res = await session.execute(select(MinistryGroup).where(MinistryGroup.id == ministry_id))
    return res.scalar_one_or_none()


async def get_ministry_or_404(session: AsyncSession, ministry_id: uuid.UUID) -> MinistryGroup:
    m = await get_ministry(session, ministry_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministry not found")
    return m


async def active_member_count(session: AsyncSession, ministry_id: uuid.UUID) -> int:
    q = await session.execute(
        select(func.count())
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.ministry_id == ministry_id,
            MinistryMembership.is_active.is_(True),
        ),
    )
    return int(q.scalar_one())


async def list_ministries(
    session: AsyncSession,
    *,
    search: str | None,
    is_active: bool | None,
    page: int,
    page_size: int,
) -> tuple[list[MinistryGroup], int]:
    stmt = select(MinistryGroup)
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(MinistryGroup.name.ilike(term))
    if is_active is not None:
        stmt = stmt.where(MinistryGroup.is_active.is_(is_active))

    count_base = stmt.subquery()
    count_q = await session.execute(select(func.count()).select_from(count_base))
    total = int(count_q.scalar_one())

    stmt = (
        stmt.order_by(MinistryGroup.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    res = await session.execute(stmt)
    rows = list(res.scalars().unique().all())
    return rows, total


async def ministry_to_list_item(session: AsyncSession, m: MinistryGroup) -> MinistryListItem:
    n = await active_member_count(session, m.id)
    return MinistryListItem(
        id=m.id,
        name=m.name,
        description=m.description,
        is_active=m.is_active,
        leader_user_id=m.leader_user_id,
        active_member_count=n,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


async def load_memberships_for_ministry(
    session: AsyncSession,
    ministry_id: uuid.UUID,
    *,
    active_only: bool = False,
) -> list[MinistryMembership]:
    stmt = (
        select(MinistryMembership)
        .where(MinistryMembership.ministry_id == ministry_id)
        .options(selectinload(MinistryMembership.user))
        .order_by(MinistryMembership.joined_at.asc())
    )
    if active_only:
        stmt = stmt.where(MinistryMembership.is_active.is_(True))
    res = await session.execute(stmt)
    return list(res.scalars().unique().all())


def membership_to_row(mm: MinistryMembership) -> MinistryMemberRow:
    u = mm.user
    return MinistryMemberRow(
        membership_id=mm.id,
        user_id=u.id,
        full_name=u.full_name,
        email=u.email,
        role_in_ministry=mm.role_in_ministry,
        is_active=mm.is_active,
        joined_at=mm.joined_at,
    )


async def ministry_detail_for_admin(
    session: AsyncSession,
    ministry: MinistryGroup,
) -> MinistryDetailResponse:
    mms = await load_memberships_for_ministry(session, ministry.id, active_only=False)
    return MinistryDetailResponse(
        id=ministry.id,
        name=ministry.name,
        description=ministry.description,
        is_active=ministry.is_active,
        leader_user_id=ministry.leader_user_id,
        created_at=ministry.created_at,
        updated_at=ministry.updated_at,
        members=[membership_to_row(x) for x in mms],
    )


async def ministry_detail_for_member(
    session: AsyncSession,
    ministry: MinistryGroup,
    viewer_id: uuid.UUID,
) -> MinistryDetailResponse:
    stmt = (
        select(MinistryMembership)
        .where(
            MinistryMembership.ministry_id == ministry.id,
            MinistryMembership.user_id == viewer_id,
            MinistryMembership.is_active.is_(True),
        )
        .options(selectinload(MinistryMembership.user))
    )
    res = await session.execute(stmt)
    mm = res.scalar_one_or_none()
    if mm is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an active member of this ministry",
        )
    return MinistryDetailResponse(
        id=ministry.id,
        name=ministry.name,
        description=ministry.description,
        is_active=ministry.is_active,
        leader_user_id=ministry.leader_user_id,
        created_at=ministry.created_at,
        updated_at=ministry.updated_at,
        members=[membership_to_row(mm)],
    )


async def create_ministry(session: AsyncSession, body: MinistryCreate) -> MinistryGroup:
    disp = display_ministry_name(body.name)
    nk = normalize_ministry_name_key(body.name)
    existing = await session.execute(select(MinistryGroup.id).where(MinistryGroup.name_key == nk))
    if existing.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A ministry with this name already exists",
        )
    if body.leader_user_id is not None:
        await assert_user_exists(session, body.leader_user_id)

    m = MinistryGroup(
        name=disp,
        name_key=nk,
        description=body.description.strip() if body.description else None,
        is_active=body.is_active,
        leader_user_id=body.leader_user_id,
    )
    session.add(m)
    await session.commit()
    await session.refresh(m)
    return m


async def patch_ministry(
    session: AsyncSession,
    ministry: MinistryGroup,
    body: MinistryPatch,
) -> MinistryGroup:
    data = body.model_dump(exclude_unset=True)
    if "leader_user_id" in data and data["leader_user_id"] is not None:
        await assert_user_exists(session, data["leader_user_id"])
    if "name" in data and data["name"] is not None:
        disp = display_ministry_name(data["name"])
        nk = normalize_ministry_name_key(data["name"])
        existing = await session.execute(
            select(MinistryGroup.id).where(
                MinistryGroup.name_key == nk,
                MinistryGroup.id != ministry.id,
            ),
        )
        if existing.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A ministry with this name already exists",
            )
        ministry.name = disp
        ministry.name_key = nk
    if "description" in data:
        ministry.description = data["description"].strip() if data["description"] else None
    if "is_active" in data and data["is_active"] is not None:
        ministry.is_active = data["is_active"]
    if "leader_user_id" in data:
        ministry.leader_user_id = data["leader_user_id"]

    await session.commit()
    await session.refresh(ministry)
    return ministry


async def resolve_target_user(
    session: AsyncSession,
    body: MinistryMembershipCreate,
) -> User:
    if body.user_id is not None:
        return await assert_user_exists(session, body.user_id)
    assert body.email is not None
    em = normalize_email(str(body.email))
    u = await auth_service.get_user_by_email(session, em)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found for that email",
        )
    return u


async def add_or_reactivate_membership(
    session: AsyncSession,
    ministry: MinistryGroup,
    body: MinistryMembershipCreate,
) -> MinistryMembership:
    if not ministry.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add members to an inactive ministry",
        )
    target = await resolve_target_user(session, body)

    stmt = select(MinistryMembership).where(
        MinistryMembership.ministry_id == ministry.id,
        MinistryMembership.user_id == target.id,
    )
    res = await session.execute(stmt)
    mm = res.scalar_one_or_none()

    if mm is None:
        mm = MinistryMembership(
            ministry_id=ministry.id,
            user_id=target.id,
            role_in_ministry=body.role_in_ministry,
            is_active=True,
        )
        session.add(mm)
        await session.commit()
        await session.refresh(mm)
        mm.user = target
        return mm

    if mm.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already an active member of this ministry",
        )

    mm.is_active = True
    mm.role_in_ministry = body.role_in_ministry
    await session.commit()
    await session.refresh(mm)
    mm.user = target
    return mm


async def patch_membership(
    session: AsyncSession,
    ministry_id: uuid.UUID,
    user_id: uuid.UUID,
    body: MinistryMembershipPatch,
) -> MinistryMembership:
    stmt = select(MinistryMembership).where(
        MinistryMembership.ministry_id == ministry_id,
        MinistryMembership.user_id == user_id,
    )
    res = await session.execute(stmt)
    mm = res.scalar_one_or_none()
    if mm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    data = body.model_dump(exclude_unset=True)
    if "role_in_ministry" in data and data["role_in_ministry"] is not None:
        mm.role_in_ministry = data["role_in_ministry"]
    if "is_active" in data and data["is_active"] is not None:
        mm.is_active = data["is_active"]

    await session.commit()
    await session.refresh(mm)
    u = await get_user_by_id(session, user_id)
    if u:
        mm.user = u
    return mm


async def deactivate_membership(
    session: AsyncSession,
    ministry_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    stmt = select(MinistryMembership).where(
        MinistryMembership.ministry_id == ministry_id,
        MinistryMembership.user_id == user_id,
    )
    res = await session.execute(stmt)
    mm = res.scalar_one_or_none()
    if mm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    mm.is_active = False
    await session.commit()


async def list_my_ministries(session: AsyncSession, user_id: uuid.UUID) -> list[MyMinistryItem]:
    stmt = (
        select(MinistryMembership, MinistryGroup)
        .join(MinistryGroup, MinistryGroup.id == MinistryMembership.ministry_id)
        .where(
            MinistryMembership.user_id == user_id,
            MinistryMembership.is_active.is_(True),
        )
        .order_by(MinistryGroup.name.asc())
    )
    res = await session.execute(stmt)
    out: list[MyMinistryItem] = []
    for mm, mg in res.all():
        out.append(
            MyMinistryItem(
                ministry_id=mg.id,
                name=mg.name,
                description=mg.description,
                ministry_is_active=mg.is_active,
                membership_id=mm.id,
                role_in_ministry=mm.role_in_ministry,
                membership_is_active=mm.is_active,
                joined_at=mm.joined_at,
            ),
        )
    return out
