"""Index church_members.membership_status (registry list/stats filters).

Revision ID: step10_5_001
Revises: step10_001
Create Date: 2026-03-28

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "step10_5_001"
down_revision: Union[str, None] = "step10_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_church_members_membership_status",
        "church_members",
        ["membership_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_church_members_membership_status", table_name="church_members")
