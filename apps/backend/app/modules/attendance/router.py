from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.attendance import service as attendance_service
from app.modules.attendance.schemas import (
    AttendanceCreateInput,
    AttendancePatchInput,
    AttendanceRow,
    EventAttendanceListResponse,
    MyAttendanceResponse,
)
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.audit_logs.actions import ATTENDANCE_CREATE, ATTENDANCE_UPDATE
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
from app.modules.events import service as events_service

router = APIRouter(prefix="/events", tags=["attendance"])


@router.get("/{event_id}/attendance", response_model=EventAttendanceListResponse)
async def list_event_attendance(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventAttendanceListResponse:
    return await attendance_service.list_event_attendance(session, event_id=event_id)


@router.post(
    "/{event_id}/attendance",
    response_model=AttendanceRow,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_attendance(
    event_id: uuid.UUID,
    body: AttendanceCreateInput,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> AttendanceRow:
    event = await events_service.get_event_or_404(session, event_id)
    out = await attendance_service.create_event_attendance(
        session,
        event_id=event_id,
        body=body,
        admin_user_id=admin.id,
    )
    who = out.member_full_name or out.user_full_name or "Member"
    await record_audit_event(
        action=ATTENDANCE_CREATE,
        summary=f"Attendance recorded: {event.title} — {who}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event_attendance",
        target_id=str(out.id),
        metadata={
            "event_title": event.title,
            "status": out.status.value,
        },
        ip_address=client_ip_from_request(request),
    )
    return out


@router.patch("/{event_id}/attendance/{user_id}", response_model=AttendanceRow)
async def patch_event_attendance(
    event_id: uuid.UUID,
    user_id: uuid.UUID,
    body: AttendancePatchInput,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> AttendanceRow:
    event = await events_service.get_event_or_404(session, event_id)
    out = await attendance_service.patch_event_attendance(
        session,
        event_id=event_id,
        user_id=user_id,
        body=body,
        admin_user_id=admin.id,
    )
    who = out.member_full_name or out.user_full_name or "Member"
    await record_audit_event(
        action=ATTENDANCE_UPDATE,
        summary=f"Attendance updated: {event.title} — {who}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event_attendance",
        target_id=str(out.id),
        metadata={
            "event_title": event.title,
            "status": out.status.value,
        },
        ip_address=client_ip_from_request(request),
    )
    return out


@router.get("/{event_id}/attendance/me", response_model=MyAttendanceResponse)
async def get_my_attendance(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MyAttendanceResponse:
    return await attendance_service.get_my_attendance_for_event(
        session,
        event_id=event_id,
        user=user,
    )

