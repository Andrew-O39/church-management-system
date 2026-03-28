"""volunteer roles and event assignments

Revision ID: step9_001
Revises: step8_001
Create Date: 2026-03-27

Indexes: volunteer_roles.ministry_id, volunteer_assignments.event_id / user_id / role_id /
assigned_by_user_id support typical filters and joins. Unique name_key prevents duplicate
role definitions under normalization. Unique (event_id, user_id, role_id) enforces one
row per person per role per event.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step9_001"
down_revision: Union[str, None] = "step8_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "volunteer_roles",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ministry_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.ForeignKeyConstraint(["ministry_id"], ["ministry_groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_key", name="uq_volunteer_roles_name_key"),
    )
    op.create_index("ix_volunteer_roles_ministry_id", "volunteer_roles", ["ministry_id"])
    op.create_index("ix_volunteer_roles_is_active", "volunteer_roles", ["is_active"])

    op.create_table(
        "volunteer_assignments",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["role_id"], ["volunteer_roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "user_id",
            "role_id",
            name="uq_volunteer_assignment_event_user_role",
        ),
    )
    op.create_index(
        "ix_volunteer_assignments_event_id",
        "volunteer_assignments",
        ["event_id"],
    )
    op.create_index(
        "ix_volunteer_assignments_user_id",
        "volunteer_assignments",
        ["user_id"],
    )
    op.create_index(
        "ix_volunteer_assignments_role_id",
        "volunteer_assignments",
        ["role_id"],
    )
    op.create_index(
        "ix_volunteer_assignments_assigned_by_user_id",
        "volunteer_assignments",
        ["assigned_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_volunteer_assignments_assigned_by_user_id", table_name="volunteer_assignments")
    op.drop_index("ix_volunteer_assignments_role_id", table_name="volunteer_assignments")
    op.drop_index("ix_volunteer_assignments_user_id", table_name="volunteer_assignments")
    op.drop_index("ix_volunteer_assignments_event_id", table_name="volunteer_assignments")
    op.drop_table("volunteer_assignments")
    op.drop_index("ix_volunteer_roles_is_active", table_name="volunteer_roles")
    op.drop_index("ix_volunteer_roles_ministry_id", table_name="volunteer_roles")
    op.drop_table("volunteer_roles")
