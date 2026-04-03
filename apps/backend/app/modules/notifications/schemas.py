from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.models.enums import (
    NotificationAudienceType,
    NotificationCategory,
    NotificationChannel,
    NotificationDeliveryAttemptStatus,
    NotificationRecipientStatus,
)


class NotificationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    category: NotificationCategory
    channels: list[NotificationChannel] = Field(
        ...,
        min_length=1,
        description="At least one channel; combine in_app and sms for multi-channel sends.",
    )
    audience_type: NotificationAudienceType
    user_ids: list[uuid.UUID] | None = None
    ministry_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def dedupe_channels(self) -> NotificationCreateRequest:
        seen: set[str] = set()
        uniq: list[NotificationChannel] = []
        for c in self.channels:
            if c.value in seen:
                continue
            seen.add(c.value)
            uniq.append(c)
        if not uniq:
            raise ValueError("channels must not be empty after deduplication")
        object.__setattr__(self, "channels", uniq)
        return self

    @field_validator("title", "body")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

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


class DeliveryAttemptRow(BaseModel):
    id: uuid.UUID
    channel: NotificationChannel
    status: NotificationDeliveryAttemptStatus
    provider_message_id: str | None
    error_detail: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationRecipientRow(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_full_name: str | None = None
    user_email: str | None = None
    status: NotificationRecipientStatus
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime
    delivery_attempts: list[DeliveryAttemptRow]


class DeliverySummary(BaseModel):
    audience_resolved_count: int
    channels: list[str]
    in_app_recipient_count: int
    sms_skipped_no_phone: int
    sms_attempted: int
    sms_sent: int
    sms_failed: int
    whatsapp_skipped_no_phone: int
    whatsapp_attempted: int
    whatsapp_sent: int
    whatsapp_failed: int


class NotificationListItem(BaseModel):
    id: uuid.UUID
    title: str
    category: NotificationCategory
    channels: list[str]
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
    channels: list[str]
    audience_type: NotificationAudienceType
    related_event_id: uuid.UUID | None
    related_ministry_id: uuid.UUID | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
    delivery_summary: DeliverySummary | None
    recipients: list[NotificationRecipientRow]


class MyNotificationItem(BaseModel):
    notification_id: uuid.UUID
    title: str
    body: str
    category: NotificationCategory
    channels: list[str]
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
