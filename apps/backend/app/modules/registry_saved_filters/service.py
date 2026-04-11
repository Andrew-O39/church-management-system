from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.registry_saved_filter import RegistrySavedFilter
from app.modules.registry_saved_filters.validation import normalize_registry_filters_payload

_MAX_FILTERS = 64


async def list_for_user(session: AsyncSession, *, user_id: uuid.UUID) -> list[RegistrySavedFilter]:
    stmt = (
        select(RegistrySavedFilter)
        .where(RegistrySavedFilter.created_by_user_id == user_id)
        .order_by(RegistrySavedFilter.name.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def create_saved(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str,
    filters: dict[str, str],
) -> RegistrySavedFilter:
    if len(filters) > _MAX_FILTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many filter keys",
        )
    normalized = normalize_registry_filters_payload(filters)
    row = RegistrySavedFilter(
        name=name.strip(),
        created_by_user_id=user_id,
        filters_json=normalized,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_owned_or_404(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    saved_id: uuid.UUID,
) -> RegistrySavedFilter:
    stmt = select(RegistrySavedFilter).where(
        RegistrySavedFilter.id == saved_id,
        RegistrySavedFilter.created_by_user_id == user_id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")
    return row


async def update_saved(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    saved_id: uuid.UUID,
    name: str | None,
    filters: dict[str, str] | None,
) -> RegistrySavedFilter:
    row = await get_owned_or_404(session, user_id=user_id, saved_id=saved_id)
    if name is not None:
        row.name = name.strip()
    if filters is not None:
        if len(filters) > _MAX_FILTERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many filter keys",
            )
        row.filters_json = normalize_registry_filters_payload(filters)
    row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(row)
    return row


async def delete_saved(session: AsyncSession, *, user_id: uuid.UUID, saved_id: uuid.UUID) -> None:
    row = await get_owned_or_404(session, user_id=user_id, saved_id=saved_id)
    await session.delete(row)
    await session.commit()


def to_out(row: RegistrySavedFilter) -> dict:
    raw = row.filters_json or {}
    filters: dict[str, str] = {}
    for k, v in raw.items():
        if v is None:
            continue
        s = str(v).strip()
        if s:
            filters[str(k)] = s
    return {
        "id": row.id,
        "name": row.name,
        "filters": filters,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
