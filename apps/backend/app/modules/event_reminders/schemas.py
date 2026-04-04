from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models.enums import EventReminderAudienceType, NotificationChannel


class EventReminderRuleCreate(BaseModel):
    audience_type: EventReminderAudienceType
    channels: list[NotificationChannel] = Field(..., min_length=1)
    offset_minutes_before: int = Field(..., gt=0)
    title_override: str | None = Field(default=None, max_length=500)
    body_override: str | None = None
    is_active: bool = True

    @field_validator("title_override")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("body_override")
    @classmethod
    def strip_body(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class EventReminderRulePatch(BaseModel):
    audience_type: EventReminderAudienceType | None = None
    channels: list[NotificationChannel] | None = Field(default=None, min_length=1)
    offset_minutes_before: int | None = Field(default=None, gt=0)
    title_override: str | None = Field(default=None, max_length=500)
    body_override: str | None = None
    is_active: bool | None = None

    @field_validator("title_override")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("body_override")
    @classmethod
    def strip_body(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class EventReminderRuleResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    title_override: str | None
    body_override: str | None
    audience_type: EventReminderAudienceType
    channels: list[str]
    offset_minutes_before: int
    is_active: bool
    last_run_at: datetime | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventReminderRuleListResponse(BaseModel):
    items: list[EventReminderRuleResponse]


class RunDueRemindersResponse(BaseModel):
    """Summary from POST .../run-due (manual or future cron)."""

    rules_considered: int
    reminders_sent: int
    skipped_not_due: int
    skipped_already_sent: int
    skipped_invalid: int
    failed: int
    failure_messages: list[str] = []
