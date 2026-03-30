from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import (
    NotificationAudienceType,
    NotificationCategory,
)

if TYPE_CHECKING:
    from app.db.models.church_event import ChurchEvent
    from app.db.models.ministry_group import MinistryGroup
    from app.db.models.notification_recipient import NotificationRecipient
    from app.db.models.user import User


class Notification(Base):
    """Broadcast message metadata; recipients are ``NotificationRecipient`` rows."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)

    category: Mapped[NotificationCategory] = mapped_column(
        Enum(
            NotificationCategory,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        index=True,
    )
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    audience_type: Mapped[NotificationAudienceType] = mapped_column(
        Enum(
            NotificationAudienceType,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
    )

    related_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("church_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_ministry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ministry_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    related_event: Mapped["ChurchEvent | None"] = relationship(
        foreign_keys=[related_event_id],
    )
    related_ministry: Mapped["MinistryGroup | None"] = relationship(
        foreign_keys=[related_ministry_id],
    )
    created_by: Mapped["User"] = relationship(
        foreign_keys=[created_by_user_id],
        back_populates="sent_notifications",
    )
    recipients: Mapped[list["NotificationRecipient"]] = relationship(
        back_populates="notification",
        cascade="all, delete-orphan",
    )
