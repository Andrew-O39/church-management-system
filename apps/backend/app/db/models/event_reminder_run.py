from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import EventReminderRunStatus

if TYPE_CHECKING:
    from app.db.models.church_event import ChurchEvent
    from app.db.models.event_reminder_rule import EventReminderRule
    from app.db.models.notification import Notification


class EventReminderRun(Base):
    """One execution attempt for a (rule, scheduled_fire_time) pair — idempotency + audit."""

    __tablename__ = "event_reminder_runs"
    __table_args__ = (
        UniqueConstraint(
            "reminder_rule_id",
            "scheduled_for",
            name="uq_event_reminder_run_rule_scheduled",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    reminder_rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event_reminder_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[EventReminderRunStatus] = mapped_column(
        Enum(
            EventReminderRunStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        default=EventReminderRunStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)

    created_notification_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("notifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reminder_rule: Mapped["EventReminderRule"] = relationship(back_populates="runs")
    event: Mapped["ChurchEvent"] = relationship()
    created_notification: Mapped["Notification | None"] = relationship()
