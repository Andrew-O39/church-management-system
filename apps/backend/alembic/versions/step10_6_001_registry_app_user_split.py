"""Parish registry flag + operational tables use user_id again (hard separation).

Revision ID: step10_6_001
Revises: step10_5_001
Create Date: 2026-03-28

- Adds ``church_members.is_parish_office_record`` and backfills: rows that still look like
  Step-10 migration stubs (linked to a user, no parish-office fields filled) are marked
  ``false`` so they drop out of the parish registry list without deleting data.
- Restores ``user_id`` on ministry_memberships, event_attendance, volunteer_assignments
  (Step 10 had moved these to ``church_member_id``).

Downgrade is intentionally unsupported (data shape + backfill are not trivially reversible).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step10_6_001"
down_revision: Union[str, None] = "step10_5_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "church_members",
        sa.Column(
            "is_parish_office_record",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    # Legacy auto/migration stubs: exclude from parish registry list (see service filter).
    op.execute(
        """
        UPDATE church_members cm
        SET is_parish_office_record = false
        FROM users u
        WHERE u.member_id = cm.id
          AND cm.registration_number IS NULL
          AND (cm.email IS NULL OR btrim(cm.email) = '')
          AND (cm.phone IS NULL OR btrim(cm.phone) = '')
          AND cm.is_baptized = false
          AND cm.is_confirmed = false
          AND cm.is_communicant = false
        """
    )
    op.alter_column(
        "church_members",
        "is_parish_office_record",
        server_default=None,
    )

    # --- ministry_memberships: church_member_id -> user_id ---
    op.add_column(
        "ministry_memberships",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_ministry_memberships_user_id", "ministry_memberships", ["user_id"])
    op.execute(
        """
        UPDATE ministry_memberships mm
        SET user_id = u.id
        FROM users u
        WHERE u.member_id = mm.church_member_id
        """
    )
    op.execute("DELETE FROM ministry_memberships WHERE user_id IS NULL")

    op.drop_constraint("uq_ministry_membership_ministry_member", "ministry_memberships", type_="unique")
    op.drop_constraint("ministry_memberships_church_member_id_fkey", "ministry_memberships", type_="foreignkey")
    op.drop_index("ix_ministry_memberships_church_member_id", table_name="ministry_memberships")
    op.drop_column("ministry_memberships", "church_member_id")

    op.alter_column("ministry_memberships", "user_id", nullable=False)
    op.create_foreign_key(
        "ministry_memberships_user_id_fkey",
        "ministry_memberships",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_ministry_membership_ministry_user",
        "ministry_memberships",
        ["ministry_id", "user_id"],
    )

    # --- event_attendance ---
    op.add_column(
        "event_attendance",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_event_attendance_user_id", "event_attendance", ["user_id"])
    op.execute(
        """
        UPDATE event_attendance ea
        SET user_id = u.id
        FROM users u
        WHERE u.member_id = ea.church_member_id
        """
    )
    op.execute("DELETE FROM event_attendance WHERE user_id IS NULL")

    op.drop_constraint("uq_event_attendance_event_member", "event_attendance", type_="unique")
    op.drop_constraint("event_attendance_church_member_id_fkey", "event_attendance", type_="foreignkey")
    op.drop_index("ix_event_attendance_church_member_id", table_name="event_attendance")
    op.drop_column("event_attendance", "church_member_id")

    op.alter_column("event_attendance", "user_id", nullable=False)
    op.create_foreign_key(
        "event_attendance_user_id_fkey",
        "event_attendance",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_event_attendance_event_user",
        "event_attendance",
        ["event_id", "user_id"],
    )

    # --- volunteer_assignments ---
    op.add_column(
        "volunteer_assignments",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_volunteer_assignments_user_id", "volunteer_assignments", ["user_id"])
    op.execute(
        """
        UPDATE volunteer_assignments va
        SET user_id = u.id
        FROM users u
        WHERE u.member_id = va.church_member_id
        """
    )
    op.execute("DELETE FROM volunteer_assignments WHERE user_id IS NULL")

    op.drop_constraint("uq_volunteer_assignment_event_member_role", "volunteer_assignments", type_="unique")
    op.drop_constraint("volunteer_assignments_church_member_id_fkey", "volunteer_assignments", type_="foreignkey")
    op.drop_index("ix_volunteer_assignments_church_member_id", table_name="volunteer_assignments")
    op.drop_column("volunteer_assignments", "church_member_id")

    op.alter_column("volunteer_assignments", "user_id", nullable=False)
    op.create_foreign_key(
        "volunteer_assignments_user_id_fkey",
        "volunteer_assignments",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_volunteer_assignment_event_user_role",
        "volunteer_assignments",
        ["event_id", "user_id", "role_id"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "step10_6_001 downgrade is not supported; restore from backup or recreate the database.",
    )
