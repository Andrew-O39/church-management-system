"""ministry_groups and ministry_memberships

Revision ID: step6_001
Revises: step2_001
Create Date: 2026-03-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step6_001"
down_revision: Union[str, None] = "step2_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ministry_groups",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("leader_user_id", sa.Uuid(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["leader_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ministry_groups_leader_user_id",
        "ministry_groups",
        ["leader_user_id"],
        unique=False,
    )
    op.create_index("ix_ministry_groups_name_key", "ministry_groups", ["name_key"], unique=True)

    op.create_table(
        "ministry_memberships",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ministry_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "role_in_ministry",
            sa.String(length=32),
            server_default=sa.text("'member'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["ministry_id"], ["ministry_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ministry_id",
            "user_id",
            name="uq_ministry_membership_ministry_user",
        ),
    )
    op.create_index(
        "ix_ministry_memberships_ministry_id",
        "ministry_memberships",
        ["ministry_id"],
        unique=False,
    )
    op.create_index(
        "ix_ministry_memberships_user_id",
        "ministry_memberships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ministry_memberships_user_id", table_name="ministry_memberships")
    op.drop_index("ix_ministry_memberships_ministry_id", table_name="ministry_memberships")
    op.drop_table("ministry_memberships")
    op.drop_index("ix_ministry_groups_name_key", table_name="ministry_groups")
    op.drop_index("ix_ministry_groups_leader_user_id", table_name="ministry_groups")
    op.drop_table("ministry_groups")
