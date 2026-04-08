"""enforce unique registration_number for church_members

Revision ID: step16_002
Revises: step16_001
Create Date: 2026-04-08
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "step16_002"
down_revision: Union[str, None] = "step16_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_church_members_registration_number",
        "church_members",
        ["registration_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_church_members_registration_number",
        "church_members",
        type_="unique",
    )
