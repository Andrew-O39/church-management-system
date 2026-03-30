from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import NotificationChannel, NotificationDeliveryAttemptStatus

if TYPE_CHECKING:
    from app.db.models.notification_recipient import NotificationRecipient


class NotificationDeliveryAttempt(Base):
    """One row per (recipient, channel) for external + in_app delivery tracking."""

    __tablename__ = "notification_delivery_attempts"
    __table_args__ = (
        UniqueConstraint(
            "notification_recipient_id",
            "channel",
            name="uq_notification_delivery_recipient_channel",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    notification_recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("notification_recipients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[NotificationDeliveryAttemptStatus] = mapped_column(
        Enum(
            NotificationDeliveryAttemptStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
        index=True,
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    recipient: Mapped["NotificationRecipient"] = relationship(
        back_populates="delivery_attempts",
    )
