from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.church_event import ChurchEvent
from app.db.models.enums import EventVisibility, UserRole
from app.db.models.event_attendance import EventAttendance
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.modules.attendance.schemas import (
    AttendanceCreateInput,
    AttendancePatchInput,
    AttendanceRow,
    EventAttendanceListResponse,
    MyAttendanceResponse,
)
from app.modules.auth import service as auth_service


async def get_event_or_404(session: AsyncSession, event_id: uuid.UUID) -> ChurchEvent:
    stmt = (
        select(ChurchEvent)
        .where(ChurchEvent.id == event_id)
        .options(selectinload(ChurchEvent.ministry))
    )
    res = await session.execute(stmt)
    ev = res.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return ev


async def _is_active_member_of_ministry(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    ministry_id: uuid.UUID,
) -> bool:
    exists_q = (
        select(1)
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.user_id == user_id,
            MinistryMembership.ministry_id == ministry_id,
            MinistryMembership.is_active.is_(True),
        )
        .exists()
    )
    return bool((await session.execute(select(exists_q))).scalar_one())


async def can_user_view_event(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    user: User,
) -> bool:
    if not event.is_active:
        return False

    if user.role == UserRole.ADMIN:
        return True

    # Church-wide events (public/internal) visible to authenticated users.
    if event.ministry_id is None:
        return event.visibility in {EventVisibility.PUBLIC, EventVisibility.INTERNAL}

    return await _is_active_member_of_ministry(
        session,
        user_id=user.id,
        ministry_id=event.ministry_id,
    )


async def is_user_eligible_for_event(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    target_user: User,
) -> bool:
    if not target_user.is_active:
        return False
    if event.ministry_id is None:
        return True
    return await _is_active_member_of_ministry(
        session,
        user_id=target_user.id,
        ministry_id=event.ministry_id,
    )


def _to_row(att: EventAttendance, user: User) -> AttendanceRow:
    return AttendanceRow(
        id=att.id,
        event_id=att.event_id,
        user_id=att.user_id,
        user_full_name=user.full_name,
        user_email=user.email,
        status=att.status,
        recorded_by_user_id=att.recorded_by_user_id,
        created_at=att.created_at,
        updated_at=att.updated_at,
    )


async def list_event_attendance(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
) -> EventAttendanceListResponse:
    await get_event_or_404(session, event_id)

    stmt = select(EventAttendance).where(EventAttendance.event_id == event_id)
    rows = list((await session.execute(stmt)).scalars().all())

    out: list[AttendanceRow] = []
    for row in rows:
        user = await auth_service.get_user_by_id(session, row.user_id)
        if user is None:
            # Should not happen due to FK; skip defensively.
            continue
        out.append(_to_row(row, user))

    # Stable ordering for UI/tests.
    out.sort(key=lambda r: (r.user_full_name.lower(), str(r.user_id)))
    return EventAttendanceListResponse(items=out)


async def create_event_attendance(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    body: AttendanceCreateInput,
    admin_user_id: uuid.UUID,
) -> AttendanceRow:
    event = await get_event_or_404(session, event_id)
    if not event.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record attendance for inactive event",
        )

    target = await auth_service.get_user_by_id(session, body.user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not await is_user_eligible_for_event(session, event=event, target_user=target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not eligible for attendance on this event",
        )

    existing_stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.user_id == body.user_id,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this user and event; use PATCH",
        )

    row = EventAttendance(
        event_id=event_id,
        user_id=body.user_id,
        status=body.status,
        recorded_by_user_id=admin_user_id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_row(row, target)


async def patch_event_attendance(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    user_id: uuid.UUID,
    body: AttendancePatchInput,
    admin_user_id: uuid.UUID,
) -> AttendanceRow:
    event = await get_event_or_404(session, event_id)
    if not event.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update attendance for inactive event",
        )

    target = await auth_service.get_user_by_id(session, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not await is_user_eligible_for_event(session, event=event, target_user=target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not eligible for attendance on this event",
        )

    stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.user_id == user_id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found")

    row.status = body.status
    row.recorded_by_user_id = admin_user_id
    await session.commit()
    await session.refresh(row)
    return _to_row(row, target)


async def get_my_attendance_for_event(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    user: User,
) -> MyAttendanceResponse:
    event = await get_event_or_404(session, event_id)

    allowed = await can_user_view_event(session, event=event, user=user)
    if not allowed:
        # Keep event privacy by returning not found semantics.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.user_id == user.id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return MyAttendanceResponse(
            event_id=event_id,
            user_id=user.id,
            status=None,
            recorded=False,
        )

    return MyAttendanceResponse(
        event_id=event_id,
        user_id=user.id,
        status=row.status,
        recorded=True,
    )

