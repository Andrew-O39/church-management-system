from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.db.models.enums import MinistryRoleInMinistry


class MinistryListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    leader_user_id: uuid.UUID | None
    active_member_count: int
    created_at: datetime
    updated_at: datetime


class MinistryMemberRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: uuid.UUID
    church_member_id: uuid.UUID
    full_name: str
    email: str | None
    linked_user_id: uuid.UUID | None
    user_id: uuid.UUID | None
    user_full_name: str | None
    user_email: str | None
    role_in_ministry: MinistryRoleInMinistry
    is_active: bool
    joined_at: datetime


class MinistryDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    leader_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    members: list[MinistryMemberRow]


class MinistryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    is_active: bool = True
    leader_user_id: uuid.UUID | None = None


class MinistryPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    is_active: bool | None = None
    leader_user_id: uuid.UUID | None = None


class MinistryMembershipCreate(BaseModel):
    """Identify the parishioner via registry id, app user id, or email."""

    church_member_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    email: EmailStr | None = None
    role_in_ministry: MinistryRoleInMinistry = MinistryRoleInMinistry.MEMBER

    @model_validator(mode="after")
    def require_one_pointer(self) -> MinistryMembershipCreate:
        n = sum(
            1
            for x in (self.church_member_id, self.user_id, self.email)
            if x is not None
        )
        if n != 1:
            raise ValueError("Provide exactly one of church_member_id, user_id, or email")
        return self


class MinistryMembershipPatch(BaseModel):
    role_in_ministry: MinistryRoleInMinistry | None = None
    is_active: bool | None = None


class MinistryListResponse(BaseModel):
    items: list[MinistryListItem]
    total: int
    page: int
    page_size: int


class MyMinistryItem(BaseModel):
    ministry_id: uuid.UUID
    name: str
    description: str | None
    ministry_is_active: bool
    membership_id: uuid.UUID
    role_in_ministry: MinistryRoleInMinistry
    membership_is_active: bool
    joined_at: datetime


class MyMinistriesResponse(BaseModel):
    items: list[MyMinistryItem]
