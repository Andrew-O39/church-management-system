"""Event reminder rules and run log for scheduled notifications (Step 14).

Revision ID: step14_001
Revises: step12_001
Create Date: 2026-03-28

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step14_001"
down_revision: Union[str, None] = "step12_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_reminder_rules",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title_override", sa.String(length=500), nullable=True),
        sa.Column("body_override", sa.Text(), nullable=True),
        sa.Column("audience_type", sa.String(length=32), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("offset_minutes_before", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["event_id"], ["church_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "offset_minutes_before",
            "audience_type",
            name="uq_event_reminder_event_offset_audience",
        ),
    )
    op.create_index("ix_event_reminder_rules_event_id", "event_reminder_rules", ["event_id"])
    op.create_index("ix_event_reminder_rules_created_by_user_id", "event_reminder_rules", ["created_by_user_id"])

    op.create_table(
        "event_reminder_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reminder_rule_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_notification_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_notification_id"],
            ["notifications.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["church_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reminder_rule_id"], ["event_reminder_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reminder_rule_id",
            "scheduled_for",
            name="uq_event_reminder_run_rule_scheduled",
        ),
    )
    op.create_index("ix_event_reminder_runs_reminder_rule_id", "event_reminder_runs", ["reminder_rule_id"])
    op.create_index("ix_event_reminder_runs_event_id", "event_reminder_runs", ["event_id"])
    op.create_index(
        "ix_event_reminder_runs_created_notification_id",
        "event_reminder_runs",
        ["created_notification_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_event_reminder_runs_created_notification_id", table_name="event_reminder_runs")
    op.drop_index("ix_event_reminder_runs_event_id", table_name="event_reminder_runs")
    op.drop_index("ix_event_reminder_runs_reminder_rule_id", table_name="event_reminder_runs")
    op.drop_table("event_reminder_runs")

    op.drop_index("ix_event_reminder_rules_created_by_user_id", table_name="event_reminder_rules")
    op.drop_index("ix_event_reminder_rules_event_id", table_name="event_reminder_rules")
    op.drop_table("event_reminder_rules")
