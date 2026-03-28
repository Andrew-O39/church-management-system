from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class VolunteerRoleListItem(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    ministry_id: uuid.UUID | None
    ministry_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VolunteerRoleDetailResponse(VolunteerRoleListItem):
    pass


class VolunteerRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    ministry_id: uuid.UUID | None = None
    is_active: bool = True


class VolunteerRolePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    ministry_id: uuid.UUID | None = None
    is_active: bool | None = None


class VolunteerRoleListResponse(BaseModel):
    items: list[VolunteerRoleListItem]
    total: int
    page: int
    page_size: int


class VolunteerAssignmentRow(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    church_member_id: uuid.UUID
    member_full_name: str
    member_email: str | None
    linked_user_id: uuid.UUID | None
    linked_user_email: str | None
    user_id: uuid.UUID | None
    user_full_name: str | None
    user_email: str | None
    role_id: uuid.UUID
    role_name: str
    notes: str | None
    assigned_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class VolunteerAssignmentCreate(BaseModel):
    church_member_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    role_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=10_000)

    @model_validator(mode="after")
    def exactly_one_subject(self) -> VolunteerAssignmentCreate:
        if sum(1 for x in (self.church_member_id, self.user_id) if x is not None) != 1:
            raise ValueError("Provide exactly one of church_member_id or user_id")
        return self


class VolunteerAssignmentPatch(BaseModel):
    role_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=10_000)


class EventVolunteerListResponse(BaseModel):
    items: list[VolunteerAssignmentRow]


class MyVolunteerAssignmentItem(BaseModel):
    assignment_id: uuid.UUID
    event_id: uuid.UUID
    event_title: str
    start_at: datetime
    end_at: datetime
    location: str
    role_id: uuid.UUID
    role_name: str
    notes: str | None


class MyVolunteerAssignmentsResponse(BaseModel):
    items: list[MyVolunteerAssignmentItem]


class MyEventVolunteerAssignmentsResponse(BaseModel):
    items: list[VolunteerAssignmentRow]
