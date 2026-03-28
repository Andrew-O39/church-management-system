from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.models.enums import (
    NotificationAudienceType,
    NotificationCategory,
    NotificationChannel,
    NotificationRecipientStatus,
)


class NotificationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    category: NotificationCategory
    delivery_channel: NotificationChannel = NotificationChannel.IN_APP
    audience_type: NotificationAudienceType
    user_ids: list[uuid.UUID] | None = None
    ministry_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None

    @field_validator("title", "body")
    @classmethod
    def strip_text(cls, v: str) -> str:
        s = v.strip()
        return s

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("body must not be empty")
        return v


class NotificationRecipientRow(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: NotificationRecipientStatus
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationListItem(BaseModel):
    id: uuid.UUID
    title: str
    category: NotificationCategory
    delivery_channel: NotificationChannel
    audience_type: NotificationAudienceType
    related_event_id: uuid.UUID | None
    related_ministry_id: uuid.UUID | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    sent_at: datetime | None
    recipient_count: int

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationListItem]
    total: int
    page: int
    page_size: int


class NotificationDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    category: NotificationCategory
    delivery_channel: NotificationChannel
    audience_type: NotificationAudienceType
    related_event_id: uuid.UUID | None
    related_ministry_id: uuid.UUID | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
    recipients: list[NotificationRecipientRow]

    model_config = {"from_attributes": True}


class MyNotificationItem(BaseModel):
    notification_id: uuid.UUID
    title: str
    body: str
    category: NotificationCategory
    delivery_channel: NotificationChannel
    related_event_id: uuid.UUID | None
    related_ministry_id: uuid.UUID | None
    sent_at: datetime | None
    created_at: datetime
    recipient_status: NotificationRecipientStatus
    read_at: datetime | None

    model_config = {"from_attributes": True}


class MyNotificationsResponse(BaseModel):
    items: list[MyNotificationItem]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    notification_id: uuid.UUID
    status: NotificationRecipientStatus
    read_at: datetime | None


class MarkAllReadResponse(BaseModel):
    updated: int
