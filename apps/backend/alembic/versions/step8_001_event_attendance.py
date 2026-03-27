"""event attendance records

Revision ID: step8_001
Revises: step7_001
Create Date: 2026-03-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "step8_001"
down_revision: Union[str, None] = "step7_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_attendance",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'present'"),
        ),
        sa.Column("recorded_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["event_id"], ["church_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_attendance_event_user"),
    )
    op.create_index(
        "ix_event_attendance_event_id",
        "event_attendance",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_attendance_user_id",
        "event_attendance",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_attendance_recorded_by_user_id",
        "event_attendance",
        ["recorded_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_event_attendance_status",
        "event_attendance",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_attendance_status", table_name="event_attendance")
    op.drop_index("ix_event_attendance_recorded_by_user_id", table_name="event_attendance")
    op.drop_index("ix_event_attendance_user_id", table_name="event_attendance")
    op.drop_index("ix_event_attendance_event_id", table_name="event_attendance")
    op.drop_table("event_attendance")

