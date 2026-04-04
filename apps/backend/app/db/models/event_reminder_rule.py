from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import EventReminderAudienceType

if TYPE_CHECKING:
    from app.db.models.church_event import ChurchEvent
    from app.db.models.event_reminder_run import EventReminderRun
    from app.db.models.user import User


class EventReminderRule(Base):
    """Admin-defined schedule for sending a notification before an event starts."""

    __tablename__ = "event_reminder_rules"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "offset_minutes_before",
            "audience_type",
            name="uq_event_reminder_event_offset_audience",
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

    title_override: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_override: Mapped[str | None] = mapped_column(Text(), nullable=True)

    audience_type: Mapped[EventReminderAudienceType] = mapped_column(
        Enum(
            EventReminderAudienceType,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
    )

    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    offset_minutes_before: Mapped[int] = mapped_column(Integer, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
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

    event: Mapped["ChurchEvent"] = relationship(back_populates="reminder_rules")
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    runs: Mapped[list["EventReminderRun"]] = relationship(
        back_populates="reminder_rule",
        cascade="all, delete-orphan",
    )
