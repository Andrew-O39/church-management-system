from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChurchProfileResponse(BaseModel):
    """Single organization profile; `id` is null until the first successful PUT."""

    id: uuid.UUID | None = None
    church_name: str = ""
    short_name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChurchProfileUpdateRequest(BaseModel):
    church_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=120)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=320)

    model_config = {"extra": "forbid"}
