from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.enums import AttendanceStatus


class AttendanceRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    user_full_name: str
    user_email: str
    status: AttendanceStatus
    recorded_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AttendanceCreateInput(BaseModel):
    user_id: uuid.UUID
    status: AttendanceStatus


class AttendancePatchInput(BaseModel):
    status: AttendanceStatus


class EventAttendanceListResponse(BaseModel):
    items: list[AttendanceRow]


class MyAttendanceResponse(BaseModel):
    event_id: uuid.UUID
    user_id: uuid.UUID
    status: AttendanceStatus | None
    recorded: bool

