"""church registry: church_members + user link; ministry/attendance/volunteer use church_member_id

Revision ID: step10_001
Revises: step9_001
Create Date: 2026-03-27

"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "step10_001"
down_revision: Union[str, None] = "step9_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "church_members",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("middle_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("full_name", sa.String(length=512), nullable=False),
        sa.Column(
            "gender",
            sa.String(length=32),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("nationality", sa.String(length=120), nullable=True),
        sa.Column("occupation", sa.String(length=255), nullable=True),
        sa.Column("marital_status", sa.String(length=32), nullable=True),
        sa.Column("preferred_language", sa.String(length=64), nullable=True),
        sa.Column("registration_number", sa.String(length=64), nullable=True),
        sa.Column(
            "membership_status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_baptized", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("baptism_date", sa.Date(), nullable=True),
        sa.Column("baptism_place", sa.String(length=255), nullable=True),
        sa.Column("is_communicant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_communion_date", sa.Date(), nullable=True),
        sa.Column("first_communion_place", sa.String(length=255), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confirmation_date", sa.Date(), nullable=True),
        sa.Column("confirmation_place", sa.String(length=255), nullable=True),
        sa.Column("is_married", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("marriage_date", sa.Date(), nullable=True),
        sa.Column("marriage_place", sa.String(length=255), nullable=True),
        sa.Column("spouse_name", sa.String(length=255), nullable=True),
        sa.Column("father_name", sa.String(length=255), nullable=True),
        sa.Column("mother_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=64), nullable=True),
        sa.Column("is_deceased", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("date_of_death", sa.Date(), nullable=True),
        sa.Column("funeral_date", sa.Date(), nullable=True),
        sa.Column("burial_place", sa.String(length=255), nullable=True),
        sa.Column("cause_of_death", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
    op.create_index("ix_church_members_full_name", "church_members", ["full_name"])
    op.create_index("ix_church_members_email", "church_members", ["email"])
    op.create_index("ix_church_members_registration_number", "church_members", ["registration_number"])

    op.add_column(
        "users",
        sa.Column("member_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_users_member_id", "users", ["member_id"], unique=True)
    op.create_foreign_key("fk_users_member_id_church_members", "users", "church_members", ["member_id"], ["id"], ondelete="SET NULL")

    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id, full_name FROM users")).fetchall()
    for uid, full_name in users:
        parts = (full_name or "").strip().split()
        if not parts:
            first, middle, last = "Member", None, "Unknown"
        elif len(parts) == 1:
            first, middle, last = parts[0], None, parts[0]
        elif len(parts) == 2:
            first, middle, last = parts[0], None, parts[1]
        else:
            first, middle, last = parts[0], " ".join(parts[1:-1]), parts[-1]
        mid = uuid.uuid4()
        full = " ".join(p for p in [first, middle, last] if p)
        conn.execute(
            sa.text(
                """
                INSERT INTO church_members (
                  id, first_name, middle_name, last_name, full_name, gender,
                  membership_status, is_active, joined_at, is_baptized, is_communicant,
                  is_confirmed, is_married, is_deceased, created_at, updated_at
                ) VALUES (
                  :id, :fn, :mn, :ln, :full, 'unknown', 'active', true, now(),
                  false, false, false, false, false, now(), now()
                )
                """
            ),
            {"id": mid, "fn": first, "mn": middle, "ln": last, "full": full},
        )
        conn.execute(
            sa.text("UPDATE users SET member_id = :mid WHERE id = :uid"),
            {"mid": mid, "uid": uid},
        )

    op.add_column(
        "ministry_memberships",
        sa.Column("church_member_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_ministry_memberships_church_member_id", "ministry_memberships", ["church_member_id"])

    conn.execute(
        sa.text(
            """
            UPDATE ministry_memberships mm
            SET church_member_id = u.member_id
            FROM users u
            WHERE mm.user_id = u.id
            """
        )
    )
    op.drop_constraint("uq_ministry_membership_ministry_user", "ministry_memberships", type_="unique")
    op.drop_index("ix_ministry_memberships_user_id", table_name="ministry_memberships")
    op.drop_constraint("ministry_memberships_user_id_fkey", "ministry_memberships", type_="foreignkey")
    op.alter_column("ministry_memberships", "church_member_id", nullable=False)
    op.create_foreign_key(
        "ministry_memberships_church_member_id_fkey",
        "ministry_memberships",
        "church_members",
        ["church_member_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_ministry_membership_ministry_member",
        "ministry_memberships",
        ["ministry_id", "church_member_id"],
    )
    op.drop_column("ministry_memberships", "user_id")

    op.add_column(
        "event_attendance",
        sa.Column("church_member_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_event_attendance_church_member_id", "event_attendance", ["church_member_id"])
    conn.execute(
        sa.text(
            """
            UPDATE event_attendance ea
            SET church_member_id = u.member_id
            FROM users u
            WHERE ea.user_id = u.id
            """
        )
    )
    op.drop_constraint("uq_event_attendance_event_user", "event_attendance", type_="unique")
    op.drop_index("ix_event_attendance_user_id", table_name="event_attendance")
    op.drop_constraint("event_attendance_user_id_fkey", "event_attendance", type_="foreignkey")
    op.alter_column("event_attendance", "church_member_id", nullable=False)
    op.create_foreign_key(
        "event_attendance_church_member_id_fkey",
        "event_attendance",
        "church_members",
        ["church_member_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_event_attendance_event_member",
        "event_attendance",
        ["event_id", "church_member_id"],
    )
    op.drop_column("event_attendance", "user_id")

    op.add_column(
        "volunteer_assignments",
        sa.Column("church_member_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index("ix_volunteer_assignments_church_member_id", "volunteer_assignments", ["church_member_id"])
    conn.execute(
        sa.text(
            """
            UPDATE volunteer_assignments va
            SET church_member_id = u.member_id
            FROM users u
            WHERE va.user_id = u.id
            """
        )
    )
    op.drop_constraint("uq_volunteer_assignment_event_user_role", "volunteer_assignments", type_="unique")
    op.drop_index("ix_volunteer_assignments_user_id", table_name="volunteer_assignments")
    op.drop_constraint("volunteer_assignments_user_id_fkey", "volunteer_assignments", type_="foreignkey")
    op.alter_column("volunteer_assignments", "church_member_id", nullable=False)
    op.create_foreign_key(
        "volunteer_assignments_church_member_id_fkey",
        "volunteer_assignments",
        "church_members",
        ["church_member_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_volunteer_assignment_event_member_role",
        "volunteer_assignments",
        ["event_id", "church_member_id", "role_id"],
    )
    op.drop_column("volunteer_assignments", "user_id")


def downgrade() -> None:
    """Cannot reverse the Step 10 backfill: parish rows were created from users.

    Restoring the pre-registry schema would require dropping church_members while
    ministry/attendance/volunteer rows reference church_member_id. Use a DB backup
    or rebuild from an empty database instead of alembic downgrade for this revision.
    """
    raise RuntimeError(
        "step10_001 downgrade is not supported after church registry backfill; "
        "restore from backup or recreate the database.",
    )
