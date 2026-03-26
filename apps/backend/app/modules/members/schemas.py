from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models.enums import MaritalStatus, PreferredChannel, UserRole


class MemberProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    phone_number: str | None
    contact_email: str | None
    address: str | None
    marital_status: MaritalStatus | None
    date_of_birth: date | None
    baptism_date: date | None
    confirmation_date: date | None
    join_date: date | None
    whatsapp_enabled: bool
    sms_enabled: bool
    preferred_channel: PreferredChannel
    created_at: datetime
    updated_at: datetime


class MemberListItem(BaseModel):
    """Row-oriented payload for directory tables."""

    model_config = ConfigDict(from_attributes=True)

    member_id: uuid.UUID = Field(description="User id (directory primary key)")
    full_name: str
    email: EmailStr
    is_active: bool
    role: UserRole
    phone_number: str | None = None
    contact_email: str | None = None
    join_date: date | None = None
    preferred_channel: PreferredChannel | None = None


class MemberListResponse(BaseModel):
    items: list[MemberListItem]
    total: int
    page: int
    page_size: int


class MemberDetailResponse(BaseModel):
    member_id: uuid.UUID
    full_name: str
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
    profile: MemberProfileOut


class MemberAdminPatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None
    role: UserRole | None = None
    phone_number: str | None = None
    contact_email: EmailStr | None = None
    address: str | None = None
    marital_status: MaritalStatus | None = None
    date_of_birth: date | None = None
    baptism_date: date | None = None
    confirmation_date: date | None = None
    join_date: date | None = None
    whatsapp_enabled: bool | None = None
    sms_enabled: bool | None = None
    preferred_channel: PreferredChannel | None = None


class MemberSelfPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=64)
    contact_email: EmailStr | None = None
    address: str | None = None
    whatsapp_enabled: bool | None = None
    sms_enabled: bool | None = None
    preferred_channel: PreferredChannel | None = None
