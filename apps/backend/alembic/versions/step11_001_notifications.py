"""In-app notifications and per-user recipient rows (Step 11).

Revision ID: step11_001
Revises: step10_6_001
Create Date: 2026-03-28

Indexes:
- notifications: category, delivery_channel, related_event_id, related_ministry_id, created_by_user_id,
  sent_at — admin list filters and chronological ordering.
- notification_recipients: notification_id, user_id — join either direction.
- notification_recipients (user_id, status) — unread counts and inbox filtering by read state.
- Unique (notification_id, user_id) — one row per recipient per broadcast; dedup enforced in DB.

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step11_001"
down_revision: Union[str, None] = "step10_6_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("delivery_channel", sa.String(length=32), nullable=False),
        sa.Column("audience_type", sa.String(length=32), nullable=False),
        sa.Column("related_event_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("related_ministry_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
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
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["related_event_id"], ["church_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_ministry_id"], ["ministry_groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_category", "notifications", ["category"])
    op.create_index("ix_notifications_delivery_channel", "notifications", ["delivery_channel"])
    op.create_index("ix_notifications_related_event_id", "notifications", ["related_event_id"])
    op.create_index("ix_notifications_related_ministry_id", "notifications", ["related_ministry_id"])
    op.create_index("ix_notifications_created_by_user_id", "notifications", ["created_by_user_id"])
    op.create_index("ix_notifications_sent_at", "notifications", ["sent_at"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "notification_recipients",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("notification_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "notification_id",
            "user_id",
            name="uq_notification_recipient_notification_user",
        ),
    )
    op.create_index(
        "ix_notification_recipients_notification_id",
        "notification_recipients",
        ["notification_id"],
    )
    op.create_index("ix_notification_recipients_user_id", "notification_recipients", ["user_id"])
    op.create_index("ix_notification_recipients_status", "notification_recipients", ["status"])
    op.create_index(
        "ix_notification_recipients_user_id_status",
        "notification_recipients",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_recipients_user_id_status", table_name="notification_recipients")
    op.drop_index("ix_notification_recipients_status", table_name="notification_recipients")
    op.drop_index("ix_notification_recipients_user_id", table_name="notification_recipients")
    op.drop_index("ix_notification_recipients_notification_id", table_name="notification_recipients")
    op.drop_table("notification_recipients")

    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_sent_at", table_name="notifications")
    op.drop_index("ix_notifications_created_by_user_id", table_name="notifications")
    op.drop_index("ix_notifications_related_ministry_id", table_name="notifications")
    op.drop_index("ix_notifications_related_event_id", table_name="notifications")
    op.drop_index("ix_notifications_delivery_channel", table_name="notifications")
    op.drop_index("ix_notifications_category", table_name="notifications")
    op.drop_table("notifications")
