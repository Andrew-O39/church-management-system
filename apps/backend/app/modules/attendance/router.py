from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
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
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> AttendanceRow:
    return await attendance_service.create_event_attendance(
        session,
        event_id=event_id,
        body=body,
        admin_user_id=admin.id,
    )


@router.patch("/{event_id}/attendance/{church_member_id}", response_model=AttendanceRow)
async def patch_event_attendance(
    event_id: uuid.UUID,
    church_member_id: uuid.UUID,
    body: AttendancePatchInput,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> AttendanceRow:
    return await attendance_service.patch_event_attendance(
        session,
        event_id=event_id,
        church_member_id=church_member_id,
        body=body,
        admin_user_id=admin.id,
    )


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

