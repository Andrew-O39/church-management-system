"""church events: church_events and optional ministry linkage

Revision ID: step7_001
Revises: step6_001
Create Date: 2026-03-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "step7_001"
down_revision: Union[str, None] = "step6_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "church_events",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default=sa.text("'other'")),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default=sa.text("'public'")),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ministry_id", sa.Uuid(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ministry_id"], ["ministry_groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_at >= start_at", name="ck_church_events_end_after_start"),
    )

    op.create_index("ix_church_events_is_active", "church_events", ["is_active"], unique=False)
    op.create_index(
        "ix_church_events_event_type", "church_events", ["event_type"], unique=False
    )
    op.create_index(
        "ix_church_events_ministry_id", "church_events", ["ministry_id"], unique=False
    )
    op.create_index(
        "ix_church_events_start_at", "church_events", ["start_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_church_events_start_at", table_name="church_events")
    op.drop_index("ix_church_events_ministry_id", table_name="church_events")
    op.drop_index("ix_church_events_event_type", table_name="church_events")
    op.drop_index("ix_church_events_is_active", table_name="church_events")
    op.drop_table("church_events")

