from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.church_profile import CHURCH_PROFILE_SINGLETON_ID, ChurchProfile
from app.modules.church_profile.schemas import ChurchProfileResponse, ChurchProfileUpdateRequest


def _to_response(row: ChurchProfile | None) -> ChurchProfileResponse:
    if row is None:
        return ChurchProfileResponse()
    return ChurchProfileResponse(
        id=row.id,
        church_name=row.church_name,
        short_name=row.short_name,
        address=row.address,
        phone=row.phone,
        email=row.email,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_church_profile(session: AsyncSession) -> ChurchProfileResponse:
    row = await session.get(ChurchProfile, CHURCH_PROFILE_SINGLETON_ID)
    if row is None:
        alt = await session.scalar(select(ChurchProfile).limit(1))
        row = alt
    return _to_response(row)


async def update_or_create_church_profile(
    session: AsyncSession,
    body: ChurchProfileUpdateRequest,
) -> ChurchProfileResponse:
    now = datetime.now(timezone.utc)
    row = await session.get(ChurchProfile, CHURCH_PROFILE_SINGLETON_ID)
    if row is None:
        alt = await session.scalar(select(ChurchProfile).limit(1))
        row = alt
    if row is None:
        row = ChurchProfile(
            id=CHURCH_PROFILE_SINGLETON_ID,
            church_name=body.church_name.strip(),
            short_name=_empty_to_none(body.short_name),
            address=_empty_to_none(body.address),
            phone=_empty_to_none(body.phone),
            email=_empty_to_none(body.email),
            created_at=now,
            updated_at=now,
        )
        session.add(row)
    else:
        row.church_name = body.church_name.strip()
        row.short_name = _empty_to_none(body.short_name)
        row.address = _empty_to_none(body.address)
        row.phone = _empty_to_none(body.phone)
        row.email = _empty_to_none(body.email)
        row.updated_at = now
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


def _empty_to_none(s: str | None) -> str | None:
    if s is None:
        return None
    t = s.strip()
    return t if t else None
