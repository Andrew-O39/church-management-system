from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ChurchMembershipStatus, Gender, MaritalStatus

if TYPE_CHECKING:
    from app.db.models.user import User


class ChurchMember(Base):
    """Official parish registry record (sacraments, membership status, deceased, etc.).

    Maintained for parish administration; it is not the same thing as an app login. People may
    appear here without an app account, and app users are not assumed to have a matching row.

    Operational modules (ministries, events, attendance, volunteers) use :class:`~app.db.models.user.User`
    identity; registry linkage via ``User.member_id`` is optional and administrative only.
    """

    __tablename__ = "church_members"
    __table_args__ = (
        UniqueConstraint("registration_number", name="uq_church_members_registration_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    #: When True, row appears in the parish-office registry. False = legacy shadow rows from old app coupling.
    is_parish_office_record: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, native_enum=False, values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=Gender.UNKNOWN,
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marital_status: Mapped[MaritalStatus | None] = mapped_column(
        Enum(
            MaritalStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=True,
    )
    preferred_language: Mapped[str | None] = mapped_column(String(64), nullable=True)

    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    membership_status: Mapped[ChurchMembershipStatus] = mapped_column(
        Enum(
            ChurchMembershipStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=ChurchMembershipStatus.ACTIVE,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    is_baptized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    baptism_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    baptism_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_communicant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_communion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_communion_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmation_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_married: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    marriage_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    marriage_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    spouse_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    father_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_deceased: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_of_death: Mapped[date | None] = mapped_column(Date, nullable=True)
    funeral_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    burial_place: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cause_of_death: Mapped[str | None] = mapped_column(String(255), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    linked_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="church_member",
        primaryjoin="ChurchMember.id == User.member_id",
        foreign_keys="User.member_id",
        uselist=False,
    )
