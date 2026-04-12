"""audit_logs.actor_display_name for friendlier audit UI

Revision ID: step20_001
Revises: step19_001
Create Date: 2026-04-11

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step20_001"
down_revision: Union[str, None] = "step19_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("actor_display_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "actor_display_name")
