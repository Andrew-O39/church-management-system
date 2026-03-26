from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Uuid, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import MinistryRoleInMinistry

if TYPE_CHECKING:
    from app.db.models.ministry_group import MinistryGroup
    from app.db.models.user import User


class MinistryMembership(Base):
    """
    One row per (ministry, user). Uniqueness is enforced on (ministry_id, user_id).
    Leaving a ministry sets is_active=False; re-joining reactivates the same row.
    """

    __tablename__ = "ministry_memberships"
    __table_args__ = (
        UniqueConstraint("ministry_id", "user_id", name="uq_ministry_membership_ministry_user"),
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
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
    user: Mapped["User"] = relationship(back_populates="ministry_memberships")
