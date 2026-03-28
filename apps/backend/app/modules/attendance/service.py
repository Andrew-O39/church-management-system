from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models.church_event import ChurchEvent
from app.db.models.church_member import ChurchMember
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
from app.modules.church_registry import service as registry_service
from app.modules.church_registry.person_display import contact_email, linked_account_fields


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


async def _is_active_member_of_ministry_church_member(
    session: AsyncSession,
    *,
    church_member_id: uuid.UUID,
    ministry_id: uuid.UUID,
) -> bool:
    exists_q = (
        select(1)
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.church_member_id == church_member_id,
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

    if event.ministry_id is None:
        return event.visibility in {EventVisibility.PUBLIC, EventVisibility.INTERNAL}

    if user.member_id is None:
        return False

    return await _is_active_member_of_ministry_church_member(
        session,
        church_member_id=user.member_id,
        ministry_id=event.ministry_id,
    )


async def is_church_member_eligible_for_attendance(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    cm: ChurchMember,
) -> bool:
    return await registry_service.is_church_member_eligible_for_event(session, event=event, cm=cm)


def _to_row(att: EventAttendance, cm: ChurchMember) -> AttendanceRow:
    lu = cm.linked_user if cm.linked_user is not None else None
    uid, ufn, uem = linked_account_fields(lu)
    return AttendanceRow(
        id=att.id,
        event_id=att.event_id,
        church_member_id=att.church_member_id,
        member_full_name=cm.full_name,
        member_email=cm.email,
        contact_email=contact_email(church_member=cm, linked_user=lu),
        linked_user_id=uid,
        user_id=uid,
        user_full_name=ufn,
        user_email=uem,
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

    stmt = (
        select(EventAttendance)
        .where(EventAttendance.event_id == event_id)
        .options(
            selectinload(EventAttendance.church_member).joinedload(ChurchMember.linked_user),
        )
    )
    rows = list((await session.execute(stmt)).scalars().all())

    out: list[AttendanceRow] = []
    for row in rows:
        cm = row.church_member
        if cm is None:
            continue
        out.append(_to_row(row, cm))

    out.sort(key=lambda r: (r.member_full_name.lower(), str(r.church_member_id)))
    return EventAttendanceListResponse(items=out)


async def _resolve_create_church_member(
    session: AsyncSession,
    body: AttendanceCreateInput,
) -> ChurchMember:
    if body.church_member_id is not None:
        return await registry_service.get_church_member_or_404(session, body.church_member_id)
    assert body.user_id is not None
    u = await auth_service.get_user_by_id(session, body.user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if u.member_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a church member record",
        )
    return await registry_service.get_church_member_or_404(session, u.member_id)


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

    cm = await _resolve_create_church_member(session, body)

    if not await is_church_member_eligible_for_attendance(session, event=event, cm=cm):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Church member is not eligible for attendance on this event",
        )

    existing_stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.church_member_id == cm.id,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this member and event; use PATCH",
        )

    row = EventAttendance(
        event_id=event_id,
        church_member_id=cm.id,
        status=body.status,
        recorded_by_user_id=admin_user_id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    await session.refresh(row, attribute_names=["church_member"])
    await session.refresh(row.church_member, attribute_names=["linked_user"])
    return _to_row(row, row.church_member)


async def patch_event_attendance(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    church_member_id: uuid.UUID,
    body: AttendancePatchInput,
    admin_user_id: uuid.UUID,
) -> AttendanceRow:
    event = await get_event_or_404(session, event_id)
    if not event.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update attendance for inactive event",
        )

    cm = await registry_service.get_church_member_or_404(session, church_member_id)

    if not await is_church_member_eligible_for_attendance(session, event=event, cm=cm):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Church member is not eligible for attendance on this event",
        )

    stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.church_member_id == church_member_id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found")

    row.status = body.status
    row.recorded_by_user_id = admin_user_id
    await session.commit()
    await session.refresh(row)
    await session.refresh(row, attribute_names=["church_member"])
    await session.refresh(row.church_member, attribute_names=["linked_user"])
    return _to_row(row, row.church_member)


async def get_my_attendance_for_event(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    user: User,
) -> MyAttendanceResponse:
    event = await get_event_or_404(session, event_id)

    allowed = await can_user_view_event(session, event=event, user=user)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if user.member_id is None:
        return MyAttendanceResponse(
            event_id=event_id,
            user_id=user.id,
            church_member_id=None,
            status=None,
            recorded=False,
        )

    stmt = select(EventAttendance).where(
        EventAttendance.event_id == event_id,
        EventAttendance.church_member_id == user.member_id,
    )
    att_row = (await session.execute(stmt)).scalar_one_or_none()
    if att_row is None:
        return MyAttendanceResponse(
            event_id=event_id,
            user_id=user.id,
            church_member_id=user.member_id,
            status=None,
            recorded=False,
        )

    return MyAttendanceResponse(
        event_id=event_id,
        user_id=user.id,
        church_member_id=user.member_id,
        status=att_row.status,
        recorded=True,
    )
