from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import MaritalStatus, PreferredChannel

if TYPE_CHECKING:
    from app.db.models.user import User


class MemberProfile(Base):
    """
    Parish-facing profile data (1:1 with User).

    contact_email is optional: User.email is the canonical login + primary contact.
    contact_email supports cases where the parish directory should list a different address.
    """

    __tablename__ = "member_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    phone_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marital_status: Mapped[Optional[MaritalStatus]] = mapped_column(
        Enum(
            MaritalStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=True,
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    baptism_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    join_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferred_channel: Mapped[PreferredChannel] = mapped_column(
        Enum(
            PreferredChannel,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=PreferredChannel.WHATSAPP,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="member_profile")
