from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import EventType, EventVisibility


class EventListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    title: str
    description: str | None
    event_type: EventType
    start_at: datetime
    end_at: datetime
    location: str
    is_active: bool
    visibility: EventVisibility
    ministry_id: uuid.UUID | None
    ministry_name: str | None


class EventDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    title: str
    description: str | None
    event_type: EventType
    start_at: datetime
    end_at: datetime
    location: str
    is_active: bool
    visibility: EventVisibility
    ministry_id: uuid.UUID | None
    ministry_name: str | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    event_type: EventType = EventType.OTHER
    start_at: datetime
    end_at: datetime
    location: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    visibility: EventVisibility = EventVisibility.PUBLIC
    ministry_id: uuid.UUID | None = None


class EventPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    event_type: EventType | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    location: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    visibility: EventVisibility | None = None
    ministry_id: uuid.UUID | None = None


class EventListResponse(BaseModel):
    items: list[EventListItem]
    total: int
    page: int
    page_size: int


class MyEventsResponse(BaseModel):
    items: list[EventListItem]


class EventMemberViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    title: str
    description: str | None
    event_type: EventType
    start_at: datetime
    end_at: datetime
    location: str
    is_active: bool
    visibility: EventVisibility
    ministry_id: uuid.UUID | None
    ministry_name: str | None

