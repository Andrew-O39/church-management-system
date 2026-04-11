from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import date, datetime, time, timezone
from typing import Any, Sequence

from sqlalchemy import and_, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.church_event import ChurchEvent
from app.db.models.church_member import ChurchMember
from app.db.models.enums import ChurchMembershipStatus, Gender, RegistryAgeGroup, UserRole
from app.db.models.event_attendance import EventAttendance
from app.db.models.member_profile import MemberProfile
from app.db.models.ministry_group import MinistryGroup
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.db.models.volunteer_role import VolunteerRole
from app.modules.church_profile.service import get_church_profile
from app.modules.church_registry.registry_age import stats_reference_date
from app.modules.church_registry.service import church_member_registry_filter_exprs
from app.modules.exports.schemas import PrintExportPayload


def _utc_start(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _utc_end(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if hasattr(v, "value"):  # enum
        return str(v.value)
    return str(v)


def rows_to_csv_bytes(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for r in rows:
        writer.writerow([_cell(c) for c in r])
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def _event_filters(
    *,
    event_id: uuid.UUID | None,
    date_from: date | None,
    date_to: date | None,
    ministry_id: uuid.UUID | None,
):
    parts = [ChurchEvent.is_active.is_(True)]
    if event_id is not None:
        parts.append(ChurchEvent.id == event_id)
    df = _utc_start(date_from)
    dt = _utc_end(date_to)
    if df is not None:
        parts.append(ChurchEvent.start_at >= df)
    if dt is not None:
        parts.append(ChurchEvent.start_at <= dt)
    if ministry_id is not None:
        parts.append(ChurchEvent.ministry_id == ministry_id)
    return and_(*parts) if parts else true()


async def build_attendance_export(
    session: AsyncSession,
    *,
    event_id: uuid.UUID | None,
    date_from: date | None,
    date_to: date | None,
    ministry_id: uuid.UUID | None,
) -> tuple[list[str], list[list[Any]]]:
    ef = _event_filters(
        event_id=event_id, date_from=date_from, date_to=date_to, ministry_id=ministry_id
    )
    stmt = (
        select(
            ChurchEvent.title,
            ChurchEvent.start_at,
            User.full_name,
            User.email,
            MemberProfile.phone_number,
            EventAttendance.status,
            EventAttendance.updated_at,
        )
        .select_from(EventAttendance)
        .join(ChurchEvent, EventAttendance.event_id == ChurchEvent.id)
        .join(User, EventAttendance.user_id == User.id)
        .outerjoin(MemberProfile, MemberProfile.user_id == User.id)
        .where(ef)
        .order_by(ChurchEvent.start_at.desc(), User.full_name.asc())
    )
    result = await session.execute(stmt)
    raw = result.all()
    columns = [
        "Event title",
        "Event start (UTC)",
        "Attendee name",
        "Login email",
        "Profile phone",
        "Attendance status",
        "Record updated (UTC)",
    ]
    rows = [list(t) for t in raw]
    return columns, rows


async def build_volunteers_export(
    session: AsyncSession,
    *,
    event_id: uuid.UUID | None,
    date_from: date | None,
    date_to: date | None,
    ministry_id: uuid.UUID | None,
) -> tuple[list[str], list[list[Any]]]:
    ef = _event_filters(
        event_id=event_id, date_from=date_from, date_to=date_to, ministry_id=ministry_id
    )
    stmt = (
        select(
            ChurchEvent.title,
            ChurchEvent.start_at,
            User.full_name,
            User.email,
            MemberProfile.phone_number,
            VolunteerRole.name,
            VolunteerAssignment.notes,
        )
        .select_from(VolunteerAssignment)
        .join(ChurchEvent, VolunteerAssignment.event_id == ChurchEvent.id)
        .join(User, VolunteerAssignment.user_id == User.id)
        .outerjoin(MemberProfile, MemberProfile.user_id == User.id)
        .join(VolunteerRole, VolunteerAssignment.role_id == VolunteerRole.id)
        .where(ef)
        .order_by(ChurchEvent.start_at.desc(), User.full_name.asc())
    )
    result = await session.execute(stmt)
    raw = result.all()
    columns = [
        "Event title",
        "Event start (UTC)",
        "Volunteer name",
        "Login email",
        "Profile phone",
        "Role",
        "Notes",
    ]
    rows = [list(t) for t in raw]
    return columns, rows


async def _ministry_names_for_users(
    session: AsyncSession, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}
    stmt = (
        select(MinistryMembership.user_id, MinistryGroup.name)
        .join(MinistryGroup, MinistryMembership.ministry_id == MinistryGroup.id)
        .where(
            MinistryMembership.user_id.in_(user_ids),
            MinistryMembership.is_active.is_(True),
        )
        .order_by(MinistryGroup.name.asc())
    )
    result = await session.execute(stmt)
    out: dict[uuid.UUID, list[str]] = {}
    for uid, name in result.all():
        out.setdefault(uid, []).append(name)
    return {k: "; ".join(v) for k, v in out.items()}


async def build_app_users_export(
    session: AsyncSession,
    *,
    is_active: bool | None,
    role: UserRole | None,
    ministry_id: uuid.UUID | None,
) -> tuple[list[str], list[list[Any]]]:
    mm_count_sq = (
        select(func.count(MinistryMembership.id))
        .where(
            MinistryMembership.user_id == User.id,
            MinistryMembership.is_active.is_(True),
        )
        .scalar_subquery()
    )
    stmt = select(User, MemberProfile, mm_count_sq.label("ministry_count")).outerjoin(
        MemberProfile, MemberProfile.user_id == User.id
    )
    if ministry_id is not None:
        stmt = stmt.join(
            MinistryMembership,
            and_(
                MinistryMembership.user_id == User.id,
                MinistryMembership.ministry_id == ministry_id,
                MinistryMembership.is_active.is_(True),
            ),
        )
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if role is not None:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.full_name.asc())
    result = await session.execute(stmt)
    raw = result.all()
    user_ids = [row[0].id for row in raw]
    names_map = await _ministry_names_for_users(session, user_ids)
    columns = [
        "Full name",
        "Login email",
        "Profile phone",
        "Contact email",
        "Role",
        "Account active",
        "Created at (UTC)",
        "Ministry count",
        "Ministry names",
    ]
    rows: list[list[Any]] = []
    for user, profile, mcount in raw:
        rows.append(
            [
                user.full_name,
                user.email,
                profile.phone_number if profile else None,
                profile.contact_email if profile else None,
                user.role,
                user.is_active,
                user.created_at,
                int(mcount or 0),
                names_map.get(user.id, ""),
            ]
        )
    return columns, rows


async def build_parish_registry_export(
    session: AsyncSession,
    *,
    search: str | None = None,
    membership_status: ChurchMembershipStatus | None,
    is_deceased: bool | None,
    gender: Gender | None,
    is_baptized: bool | None,
    is_confirmed: bool | None,
    is_communicant: bool | None,
    is_active: bool | None = None,
    is_married: bool | None = None,
    age_group: RegistryAgeGroup | None = None,
    joined_from: date | None = None,
    joined_to: date | None = None,
    deceased_from: date | None = None,
    deceased_to: date | None = None,
    baptism_date_from: date | None = None,
    baptism_date_to: date | None = None,
    confirmation_date_from: date | None = None,
    confirmation_date_to: date | None = None,
    first_communion_date_from: date | None = None,
    first_communion_date_to: date | None = None,
    marriage_date_from: date | None = None,
    marriage_date_to: date | None = None,
    date_of_birth_from: date | None = None,
    date_of_birth_to: date | None = None,
) -> tuple[list[str], list[list[Any]]]:
    exprs = church_member_registry_filter_exprs(
        search=search,
        membership_status=membership_status,
        is_active=is_active,
        is_deceased=is_deceased,
        gender=gender,
        is_baptized=is_baptized,
        is_confirmed=is_confirmed,
        is_communicant=is_communicant,
        is_married=is_married,
        age_group=age_group,
        age_ref=stats_reference_date(),
        joined_from=joined_from,
        joined_to=joined_to,
        deceased_from=deceased_from,
        deceased_to=deceased_to,
        baptism_date_from=baptism_date_from,
        baptism_date_to=baptism_date_to,
        confirmation_date_from=confirmation_date_from,
        confirmation_date_to=confirmation_date_to,
        first_communion_date_from=first_communion_date_from,
        first_communion_date_to=first_communion_date_to,
        marriage_date_from=marriage_date_from,
        marriage_date_to=marriage_date_to,
        date_of_birth_from=date_of_birth_from,
        date_of_birth_to=date_of_birth_to,
    )
    stmt = select(ChurchMember).where(and_(*exprs)).order_by(ChurchMember.full_name.asc())
    members = (await session.scalars(stmt)).all()
    # Notes omitted from export (sensitive / pastoral).
    columns = [
        "Registration number",
        "First name",
        "Middle name",
        "Last name",
        "Full name",
        "Gender",
        "Date of birth",
        "Phone",
        "Email",
        "Address",
        "Membership status",
        "Joined at (UTC)",
        "Registry row active",
        "Baptized",
        "Baptism date",
        "Communicant",
        "First communion date",
        "Confirmed",
        "Confirmation date",
        "Married",
        "Marriage date",
        "Deceased",
        "Date of death",
    ]
    rows: list[list[Any]] = []
    for cm in members:
        rows.append(
            [
                cm.registration_number,
                cm.first_name,
                cm.middle_name,
                cm.last_name,
                cm.full_name,
                cm.gender,
                cm.date_of_birth,
                cm.phone,
                cm.email,
                cm.address,
                cm.membership_status,
                cm.joined_at,
                cm.is_active,
                cm.is_baptized,
                cm.baptism_date,
                cm.is_communicant,
                cm.first_communion_date,
                cm.is_confirmed,
                cm.confirmation_date,
                cm.is_married,
                cm.marriage_date,
                cm.is_deceased,
                cm.date_of_death,
            ]
        )
    return columns, rows


def _slugify_church_name(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def build_export_csv_filename(*, base_slug: str, church_name: str | None) -> str:
    """e.g. ``shepherd-parish-attendance-2026-04-04.csv`` when church_name is set."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = ""
    if church_name and church_name.strip():
        slug = _slugify_church_name(church_name)
        if slug:
            prefix = slug + "-"
    return f"{prefix}{base_slug}-{day}.csv"


async def resolve_csv_filename(session: AsyncSession, *, base_slug: str) -> str:
    cp = await get_church_profile(session)
    raw = (cp.church_name or "").strip()
    return build_export_csv_filename(base_slug=base_slug, church_name=raw or None)


async def build_print_export_payload(
    session: AsyncSession,
    *,
    title: str,
    subtitle: str | None,
    columns: list[str],
    rows: list[list[Any]],
    filters_summary: str | None = None,
) -> PrintExportPayload:
    cp = await get_church_profile(session)
    cn = (cp.church_name or "").strip() or None
    addr = (cp.address or "").strip() or None if cp.address else None
    phone = (cp.phone or "").strip() or None if cp.phone else None
    em = (cp.email or "").strip() or None if cp.email else None
    now = datetime.now(timezone.utc)
    str_rows: list[list[str | None]] = []
    for r in rows:
        str_rows.append([None if c is None else _cell(c) for c in r])
    return PrintExportPayload(
        title=title,
        subtitle=subtitle,
        columns=columns,
        rows=str_rows,
        generated_at=now,
        church_name=cn,
        address=addr,
        phone=phone,
        email=em,
        filters_summary=filters_summary,
    )
