from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import (
    ChurchMembershipStatus,
    Gender,
    MaritalStatus,
)


class ChurchMemberListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    church_member_id: uuid.UUID
    full_name: str
    first_name: str
    last_name: str
    registration_number: str | None
    email: str | None
    phone: str | None
    membership_status: ChurchMembershipStatus
    is_active: bool
    is_deceased: bool
    linked_user_id: uuid.UUID | None
    user_id: uuid.UUID | None
    user_full_name: str | None
    user_email: str | None
    joined_at: datetime


class ChurchMemberListResponse(BaseModel):
    items: list[ChurchMemberListItem]
    total: int
    page: int
    page_size: int


class ChurchMemberDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    church_member_id: uuid.UUID
    first_name: str
    middle_name: str | None
    last_name: str
    full_name: str
    gender: Gender
    date_of_birth: date | None
    phone: str | None
    email: str | None
    address: str | None
    nationality: str | None
    occupation: str | None
    marital_status: MaritalStatus | None
    preferred_language: str | None
    registration_number: str | None
    membership_status: ChurchMembershipStatus
    joined_at: datetime
    is_active: bool
    is_baptized: bool
    baptism_date: date | None
    baptism_place: str | None
    is_communicant: bool
    first_communion_date: date | None
    first_communion_place: str | None
    is_confirmed: bool
    confirmation_date: date | None
    confirmation_place: str | None
    is_married: bool
    marriage_date: date | None
    marriage_place: str | None
    spouse_name: str | None
    father_name: str | None
    mother_name: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    is_deceased: bool
    date_of_death: date | None
    funeral_date: date | None
    burial_place: str | None
    cause_of_death: str | None
    notes: str | None
    linked_user_id: uuid.UUID | None
    user_id: uuid.UUID | None
    user_full_name: str | None
    user_email: str | None
    created_at: datetime
    updated_at: datetime


class ChurchMemberCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    gender: Gender = Gender.UNKNOWN
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None
    nationality: str | None = Field(default=None, max_length=120)
    occupation: str | None = Field(default=None, max_length=255)
    marital_status: MaritalStatus | None = None
    preferred_language: str | None = Field(default=None, max_length=64)
    registration_number: str | None = Field(default=None, max_length=64)
    membership_status: ChurchMembershipStatus = ChurchMembershipStatus.ACTIVE
    is_active: bool = True
    joined_at: datetime | None = None
    is_baptized: bool = False
    baptism_date: date | None = None
    baptism_place: str | None = Field(default=None, max_length=255)
    is_communicant: bool = False
    first_communion_date: date | None = None
    first_communion_place: str | None = Field(default=None, max_length=255)
    is_confirmed: bool = False
    confirmation_date: date | None = None
    confirmation_place: str | None = Field(default=None, max_length=255)
    is_married: bool = False
    marriage_date: date | None = None
    marriage_place: str | None = Field(default=None, max_length=255)
    spouse_name: str | None = Field(default=None, max_length=255)
    father_name: str | None = Field(default=None, max_length=255)
    mother_name: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=64)
    is_deceased: bool = False
    date_of_death: date | None = None
    funeral_date: date | None = None
    burial_place: str | None = Field(default=None, max_length=255)
    cause_of_death: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=50_000)


class ChurchMemberPatch(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    middle_name: str | None = None
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    gender: Gender | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    nationality: str | None = None
    occupation: str | None = None
    marital_status: MaritalStatus | None = None
    preferred_language: str | None = None
    registration_number: str | None = None
    membership_status: ChurchMembershipStatus | None = None
    is_active: bool | None = None
    joined_at: datetime | None = None
    is_baptized: bool | None = None
    baptism_date: date | None = None
    baptism_place: str | None = None
    is_communicant: bool | None = None
    first_communion_date: date | None = None
    first_communion_place: str | None = None
    is_confirmed: bool | None = None
    confirmation_date: date | None = None
    confirmation_place: str | None = None
    is_married: bool | None = None
    marriage_date: date | None = None
    marriage_place: str | None = None
    spouse_name: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    is_deceased: bool | None = None
    date_of_death: date | None = None
    funeral_date: date | None = None
    burial_place: str | None = None
    cause_of_death: str | None = None
    notes: str | None = None


class LinkUserBody(BaseModel):
    user_id: uuid.UUID


class ChurchMemberStatsResponse(BaseModel):
    total_members: int
    active_members: int
    inactive_members: int
    visitor_members: int
    transferred_members: int
    deceased_members: int
    male_members: int
    female_members: int
    children_members: int
    young_adult_members: int
    adult_members: int
    baptized_members: int
    confirmed_members: int
    communicant_members: int
    married_members: int
    single_members: int
    gender_distribution: dict[str, int]
    age_groups: dict[str, int]
    members_with_accounts: int
    members_without_accounts: int


class EligibleChurchMemberListItem(BaseModel):
    """Eligible **app user** for event attendance/volunteers (legacy name kept for API stability)."""

    id: uuid.UUID = Field(description="User id (subject for attendance and volunteer APIs).")
    full_name: str
    email: str | None
    phone: str | None
