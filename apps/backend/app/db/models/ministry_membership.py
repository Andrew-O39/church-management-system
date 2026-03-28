from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Uuid, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import MinistryRoleInMinistry

if TYPE_CHECKING:
    from app.db.models.church_member import ChurchMember
    from app.db.models.ministry_group import MinistryGroup


class MinistryMembership(Base):
    """
    One row per (ministry, church_member). Tracks parishioners in a ministry, with or without login.
    """

    __tablename__ = "ministry_memberships"
    __table_args__ = (
        UniqueConstraint("ministry_id", "church_member_id", name="uq_ministry_membership_ministry_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ministry_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ministry_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    church_member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    role_in_ministry: Mapped[MinistryRoleInMinistry] = mapped_column(
        Enum(
            MinistryRoleInMinistry,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=MinistryRoleInMinistry.MEMBER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    ministry: Mapped["MinistryGroup"] = relationship(back_populates="memberships")
    church_member: Mapped["ChurchMember"] = relationship(
        back_populates="ministry_memberships",
        foreign_keys=[church_member_id],
    )
