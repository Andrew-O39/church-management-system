from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.church_event import ChurchEvent
    from app.db.models.church_member import ChurchMember
    from app.db.models.user import User
    from app.db.models.volunteer_role import VolunteerRole


class VolunteerAssignment(Base):
    __tablename__ = "volunteer_assignments"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "church_member_id",
            "role_id",
            name="uq_volunteer_assignment_event_member_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    church_member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("volunteer_roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    assigned_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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

    event: Mapped["ChurchEvent | None"] = relationship(
        foreign_keys=[event_id],
        lazy="selectin",
    )
    role: Mapped["VolunteerRole | None"] = relationship(
        foreign_keys=[role_id],
        lazy="selectin",
    )
    assigned_by: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_by_user_id],
        lazy="selectin",
    )
    church_member: Mapped["ChurchMember | None"] = relationship(
        foreign_keys=[church_member_id],
        lazy="selectin",
    )
