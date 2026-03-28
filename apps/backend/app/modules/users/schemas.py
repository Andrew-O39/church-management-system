from __future__ import annotations

import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import UserRole


class RegistryFilter(str, Enum):
    all = "all"
    unlinked = "unlinked"
    linked = "linked"


class UserSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    full_name: str
    email: str
    phone_number: str | None = None
    role: UserRole
    member_id: uuid.UUID | None = Field(
        default=None,
        description="ChurchMember id when this login is linked to a parish record",
    )
    linked_church_member_name: str | None = Field(
        default=None,
        description="Display name of the parish record when linked",
    )
    registry_link_status: Literal["unlinked", "linked_this_member", "linked_other_member"] | None = Field(
        default=None,
        description="Relative to for_member_id when provided",
    )


class UserSearchResponse(BaseModel):
    items: list[UserSearchItem]
    total: int
    page: int
    page_size: int
