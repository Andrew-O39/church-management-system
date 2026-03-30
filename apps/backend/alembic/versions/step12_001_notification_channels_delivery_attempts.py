"""Multi-channel notifications + per-recipient delivery attempts (Step 12).

Revision ID: step12_001
Revises: step11_001
Create Date: 2026-03-28

- Replaces ``notifications.delivery_channel`` with ``notifications.channels`` (JSON array of strings).
- Adds ``notification_delivery_attempts`` for per-channel provider status, message ids, and errors.
- Backfills one ``in_app`` ``delivered`` attempt per existing ``notification_recipient`` (Step 11 was in-app only).

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step12_001"
down_revision: Union[str, None] = "step11_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("channels", sa.JSON(), nullable=True),
    )
    op.execute(
        """
        UPDATE notifications
        SET channels = json_build_array(delivery_channel::text)::json
        """
    )
    op.alter_column("notifications", "channels", nullable=False)
    op.drop_index("ix_notifications_delivery_channel", table_name="notifications")
    op.drop_column("notifications", "delivery_channel")

    op.create_table(
        "notification_delivery_attempts",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("notification_recipient_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["notification_recipient_id"],
            ["notification_recipients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "notification_recipient_id",
            "channel",
            name="uq_notification_delivery_recipient_channel",
        ),
    )
    op.create_index(
        "ix_notification_delivery_attempts_recipient_id",
        "notification_delivery_attempts",
        ["notification_recipient_id"],
    )
    op.create_index(
        "ix_notification_delivery_attempts_channel",
        "notification_delivery_attempts",
        ["channel"],
    )
    op.create_index(
        "ix_notification_delivery_attempts_status",
        "notification_delivery_attempts",
        ["status"],
    )

    op.execute(
        """
        INSERT INTO notification_delivery_attempts (
            notification_recipient_id, channel, status, provider_message_id, error_detail
        )
        SELECT id, 'in_app', 'delivered', NULL, NULL
        FROM notification_recipients
        """
    )


def downgrade() -> None:
    op.drop_index("ix_notification_delivery_attempts_status", table_name="notification_delivery_attempts")
    op.drop_index("ix_notification_delivery_attempts_channel", table_name="notification_delivery_attempts")
    op.drop_index(
        "ix_notification_delivery_attempts_recipient_id",
        table_name="notification_delivery_attempts",
    )
    op.drop_table("notification_delivery_attempts")

    op.add_column(
        "notifications",
        sa.Column("delivery_channel", sa.String(length=32), nullable=True),
    )
    op.execute(
        """
        UPDATE notifications
        SET delivery_channel = COALESCE(channels->>0, 'in_app')
        """
    )
    op.alter_column("notifications", "delivery_channel", nullable=False)
    op.drop_column("notifications", "channels")
    op.create_index("ix_notifications_delivery_channel", "notifications", ["delivery_channel"])
