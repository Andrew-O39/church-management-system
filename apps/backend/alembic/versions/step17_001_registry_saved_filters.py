"""registry saved filter presets (admin-owned parish registry productivity)

Revision ID: step17_001
Revises: step16_002
Create Date: 2026-04-10

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step17_001"
down_revision: Union[str, None] = "step16_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "registry_saved_filters",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_registry_saved_filters_created_by_user_id",
        "registry_saved_filters",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_registry_saved_filters_created_by_user_id", table_name="registry_saved_filters")
    op.drop_table("registry_saved_filters")
