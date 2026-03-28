from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import UserRole

if TYPE_CHECKING:
    from app.db.models.church_member import ChurchMember
    from app.db.models.member_profile import MemberProfile
    from app.db.models.ministry_group import MinistryGroup
    from app.db.models.ministry_membership import MinistryMembership
    from app.db.models.notification import Notification
    from app.db.models.notification_recipient import NotificationRecipient


class User(Base):
    """Application login account (email/password).

    This is the identity people use to sign in and use the app (events, volunteering, profile).
    It is conceptually separate from the official parish registry (``ChurchMember``): the product
    does not require users to have a parish record or vice versa.

    ``member_id`` is optional legacy linkage to a parish registry row (maintenance / optional
    admin tooling). Operational features use ``User.id`` directly (ministries, attendance, etc.).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=UserRole.MEMBER,
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_members.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
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

    church_member: Mapped["ChurchMember | None"] = relationship(
        "ChurchMember",
        back_populates="linked_user",
        foreign_keys=[member_id],
    )
    member_profile: Mapped["MemberProfile"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    led_ministries: Mapped[list["MinistryGroup"]] = relationship(
        back_populates="leader",
        foreign_keys="MinistryGroup.leader_user_id",
    )
    ministry_memberships: Mapped[list["MinistryMembership"]] = relationship(
        back_populates="user",
        foreign_keys="MinistryMembership.user_id",
        cascade="all, delete-orphan",
    )
    sent_notifications: Mapped[list["Notification"]] = relationship(
        back_populates="created_by",
        foreign_keys="Notification.created_by_user_id",
    )
    notification_recipients: Mapped[list["NotificationRecipient"]] = relationship(
        back_populates="user",
        foreign_keys="NotificationRecipient.user_id",
    )
