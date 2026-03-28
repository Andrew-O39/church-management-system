from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.db.models.member_profile import MemberProfile
from app.db.models.user import User
from app.modules.users.schemas import RegistryFilter, UserSearchItem, UserSearchResponse


def _registry_link_status(
    user_member_id: uuid.UUID | None,
    for_member_id: uuid.UUID | None,
) -> Literal["unlinked", "linked_this_member", "linked_other_member"] | None:
    if for_member_id is None:
        return None
    if user_member_id is None:
        return "unlinked"
    if user_member_id == for_member_id:
        return "linked_this_member"
    return "linked_other_member"


def _apply_user_search_filters(
    stmt: Select,
    *,
    q_trim: str,
    registry_filter: RegistryFilter,
) -> Select:
    if q_trim:
        stmt = stmt.outerjoin(MemberProfile, MemberProfile.user_id == User.id).where(
            or_(
                User.full_name.ilike(f"%{q_trim}%"),
                User.email.ilike(f"%{q_trim}%"),
                MemberProfile.phone_number.ilike(f"%{q_trim}%"),
                MemberProfile.contact_email.ilike(f"%{q_trim}%"),
            ),
        )
    if registry_filter == RegistryFilter.unlinked:
        stmt = stmt.where(User.member_id.is_(None))
    elif registry_filter == RegistryFilter.linked:
        stmt = stmt.where(User.member_id.isnot(None))
    return stmt


async def search_users_for_admin(
    session: AsyncSession,
    *,
    q: str | None,
    page: int,
    page_size: int,
    registry_filter: RegistryFilter,
    for_member_id: uuid.UUID | None,
) -> UserSearchResponse:
    q_trim = (q or "").strip()

    count_stmt = select(func.count()).select_from(
        _apply_user_search_filters(select(User.id).select_from(User), q_trim=q_trim, registry_filter=registry_filter).subquery(),
    )
    total = int((await session.execute(count_stmt)).scalar_one())

    offset = (page - 1) * page_size
    data_stmt = _apply_user_search_filters(
        select(User).options(
            joinedload(User.member_profile),
            joinedload(User.church_member),
        ).order_by(User.full_name.asc()),
        q_trim=q_trim,
        registry_filter=registry_filter,
    )
    data_stmt = data_stmt.offset(offset).limit(page_size)

    rows = (await session.execute(data_stmt)).unique().scalars().all()

    items: list[UserSearchItem] = []
    for u in rows:
        phone = u.member_profile.phone_number if u.member_profile else None
        cm_name = u.church_member.full_name if u.church_member else None
        status = _registry_link_status(u.member_id, for_member_id)
        items.append(
            UserSearchItem(
                user_id=u.id,
                full_name=u.full_name,
                email=u.email,
                phone_number=phone,
                role=u.role,
                member_id=u.member_id,
                linked_church_member_name=cm_name,
                registry_link_status=status,
            ),
        )

    return UserSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
