"""Church / parish organization profile singleton (Step 16.1).

Revision ID: step16_001
Revises: step14_001
Create Date: 2026-03-28

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step16_001"
down_revision: Union[str, None] = "step14_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "church_profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("church_name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=120), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("church_profiles")
