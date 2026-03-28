from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.church_event import ChurchEvent
from app.db.models.church_member import ChurchMember
from app.db.models.enums import ChurchMembershipStatus, Gender
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.modules.auth import service as auth_service
from app.modules.church_registry.person_display import (
    contact_email,
    linked_account_fields,
    normalize_full_name_key,
)
from app.modules.church_registry.schemas import (
    ChurchMemberCreate,
    ChurchMemberDetailResponse,
    ChurchMemberListItem,
    ChurchMemberListResponse,
    ChurchMemberPatch,
    ChurchMemberStatsResponse,
    EligibleChurchMemberListItem,
)


def build_full_name(*, first_name: str, middle_name: str | None, last_name: str) -> str:
    parts = [first_name.strip()]
    if middle_name and middle_name.strip():
        parts.append(middle_name.strip())
    parts.append(last_name.strip())
    return " ".join(parts)


def split_full_name_to_parts(full_name: str) -> tuple[str, str | None, str]:
    parts = full_name.strip().split()
    if not parts:
        return "Member", None, "Unknown"
    if len(parts) == 1:
        return parts[0], None, parts[0]
    if len(parts) == 2:
        return parts[0], None, parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]


async def create_member_for_registered_user(session: AsyncSession, user: User) -> ChurchMember:
    """Create a registry row for a newly registered app user and attach profile hints."""
    await session.refresh(user, attribute_names=["member_profile"])
    first, middle, last = split_full_name_to_parts(user.full_name)
    profile = user.member_profile
    built_full = build_full_name(first_name=first, middle_name=middle, last_name=last)
    await _ensure_no_duplicate_name_and_dob(
        session,
        full_name=built_full,
        date_of_birth=profile.date_of_birth if profile else None,
    )
    cm = ChurchMember(
        first_name=first,
        middle_name=middle,
        last_name=last,
        full_name=built_full,
        gender=Gender.UNKNOWN,
        phone=profile.phone_number if profile else None,
        date_of_birth=profile.date_of_birth if profile else None,
        marital_status=profile.marital_status if profile else None,
        email=None,
        membership_status=ChurchMembershipStatus.ACTIVE,
        is_active=True,
        is_baptized=bool(profile and profile.baptism_date),
        baptism_date=profile.baptism_date if profile else None,
        is_confirmed=bool(profile and profile.confirmation_date),
        confirmation_date=profile.confirmation_date if profile else None,
        joined_at=datetime.now(timezone.utc),
    )
    session.add(cm)
    await session.flush()
    return cm


def _to_list_item(cm: ChurchMember) -> ChurchMemberListItem:
    lu = cm.linked_user
    uid, ufn, uem = linked_account_fields(lu)
    return ChurchMemberListItem(
        id=cm.id,
        church_member_id=cm.id,
        full_name=cm.full_name,
        first_name=cm.first_name,
        last_name=cm.last_name,
        email=contact_email(church_member=cm, linked_user=lu),
        phone=cm.phone,
        membership_status=cm.membership_status,
        is_active=cm.is_active,
        is_deceased=cm.is_deceased,
        linked_user_id=uid,
        user_id=uid,
        user_full_name=ufn,
        user_email=uem,
        joined_at=cm.joined_at,
    )


def church_member_to_detail(cm: ChurchMember) -> ChurchMemberDetailResponse:
    lu = cm.linked_user
    uid, ufn, uem = linked_account_fields(lu)
    return ChurchMemberDetailResponse(
        id=cm.id,
        church_member_id=cm.id,
        first_name=cm.first_name,
        middle_name=cm.middle_name,
        last_name=cm.last_name,
        full_name=cm.full_name,
        gender=cm.gender,
        date_of_birth=cm.date_of_birth,
        phone=cm.phone,
        email=cm.email,
        address=cm.address,
        nationality=cm.nationality,
        occupation=cm.occupation,
        marital_status=cm.marital_status,
        preferred_language=cm.preferred_language,
        registration_number=cm.registration_number,
        membership_status=cm.membership_status,
        joined_at=cm.joined_at,
        is_active=cm.is_active,
        is_baptized=cm.is_baptized,
        baptism_date=cm.baptism_date,
        baptism_place=cm.baptism_place,
        is_communicant=cm.is_communicant,
        first_communion_date=cm.first_communion_date,
        first_communion_place=cm.first_communion_place,
        is_confirmed=cm.is_confirmed,
        confirmation_date=cm.confirmation_date,
        confirmation_place=cm.confirmation_place,
        is_married=cm.is_married,
        marriage_date=cm.marriage_date,
        marriage_place=cm.marriage_place,
        spouse_name=cm.spouse_name,
        father_name=cm.father_name,
        mother_name=cm.mother_name,
        emergency_contact_name=cm.emergency_contact_name,
        emergency_contact_phone=cm.emergency_contact_phone,
        is_deceased=cm.is_deceased,
        date_of_death=cm.date_of_death,
        funeral_date=cm.funeral_date,
        burial_place=cm.burial_place,
        cause_of_death=cm.cause_of_death,
        notes=cm.notes,
        linked_user_id=uid,
        user_id=uid,
        user_full_name=ufn,
        user_email=uem,
        created_at=cm.created_at,
        updated_at=cm.updated_at,
    )


async def get_my_church_member_profile(
    session: AsyncSession,
    *,
    user: User,
) -> ChurchMemberDetailResponse:
    if user.member_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No church member record is linked to this account",
        )
    cm = await get_church_member_or_404(session, user.member_id)
    return church_member_to_detail(cm)


async def _ensure_no_duplicate_name_and_dob(
    session: AsyncSession,
    *,
    full_name: str,
    date_of_birth: date | None,
    exclude_member_id: uuid.UUID | None = None,
) -> None:
    """Soft duplicate rule: same normalized full name and the same non-null date_of_birth.

    If date_of_birth is unknown (NULL), we do not block — many roster rows share a display
    name without a recorded DOB (e.g. default registration names).
    """
    if date_of_birth is None:
        return
    key = normalize_full_name_key(full_name)
    stmt = select(ChurchMember).where(ChurchMember.date_of_birth == date_of_birth)
    if exclude_member_id is not None:
        stmt = stmt.where(ChurchMember.id != exclude_member_id)
    rows = (await session.execute(stmt)).scalars().all()
    for r in rows:
        if normalize_full_name_key(r.full_name) != key:
            continue
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A church member with the same name and date of birth already exists",
        )


async def get_church_member_or_404(session: AsyncSession, member_id: uuid.UUID) -> ChurchMember:
    stmt = (
        select(ChurchMember)
        .where(ChurchMember.id == member_id)
        .options(joinedload(ChurchMember.linked_user))
    )
    cm = (await session.execute(stmt)).unique().scalar_one_or_none()
    if cm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Church member not found")
    return cm


def _church_member_filter_exprs(
    *,
    search: str | None,
    membership_status: ChurchMembershipStatus | None,
    is_active: bool | None,
    is_deceased: bool | None,
) -> list:
    exprs: list = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        exprs.append(
            ChurchMember.full_name.ilike(term)
            | ChurchMember.email.ilike(term)
            | ChurchMember.registration_number.ilike(term),
        )
    if membership_status is not None:
        exprs.append(ChurchMember.membership_status == membership_status)
    if is_active is not None:
        exprs.append(ChurchMember.is_active.is_(is_active))
    if is_deceased is not None:
        exprs.append(ChurchMember.is_deceased.is_(is_deceased))
    return exprs


async def list_church_members(
    session: AsyncSession,
    *,
    search: str | None,
    membership_status: ChurchMembershipStatus | None,
    is_active: bool | None,
    is_deceased: bool | None,
    page: int,
    page_size: int,
) -> ChurchMemberListResponse:
    exprs = _church_member_filter_exprs(
        search=search,
        membership_status=membership_status,
        is_active=is_active,
        is_deceased=is_deceased,
    )
    count_stmt = select(func.count()).select_from(ChurchMember)
    if exprs:
        count_stmt = count_stmt.where(and_(*exprs))
    total = int((await session.execute(count_stmt)).scalar_one())

    stmt = select(ChurchMember).options(joinedload(ChurchMember.linked_user))
    if exprs:
        stmt = stmt.where(and_(*exprs))
    stmt = (
        stmt.order_by(ChurchMember.full_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list((await session.execute(stmt)).unique().scalars().all())
    return ChurchMemberListResponse(
        items=[_to_list_item(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def create_church_member(session: AsyncSession, body: ChurchMemberCreate) -> ChurchMemberDetailResponse:
    fn = body.first_name.strip()
    ln = body.last_name.strip()
    mn = body.middle_name.strip() if body.middle_name else None
    full = build_full_name(first_name=fn, middle_name=mn, last_name=ln)
    await _ensure_no_duplicate_name_and_dob(
        session,
        full_name=full,
        date_of_birth=body.date_of_birth,
    )
    cm = ChurchMember(
        first_name=fn,
        middle_name=mn,
        last_name=ln,
        full_name=full,
        gender=body.gender,
        date_of_birth=body.date_of_birth,
        phone=body.phone.strip() if body.phone else None,
        email=body.email.strip().lower() if body.email else None,
        address=body.address,
        nationality=body.nationality.strip() if body.nationality else None,
        occupation=body.occupation.strip() if body.occupation else None,
        marital_status=body.marital_status,
        preferred_language=body.preferred_language.strip() if body.preferred_language else None,
        registration_number=body.registration_number.strip() if body.registration_number else None,
        membership_status=body.membership_status,
        is_active=body.is_active,
        joined_at=body.joined_at or datetime.now(timezone.utc),
        is_baptized=body.is_baptized,
        baptism_date=body.baptism_date,
        baptism_place=body.baptism_place.strip() if body.baptism_place else None,
        is_communicant=body.is_communicant,
        first_communion_date=body.first_communion_date,
        first_communion_place=body.first_communion_place.strip() if body.first_communion_place else None,
        is_confirmed=body.is_confirmed,
        confirmation_date=body.confirmation_date,
        confirmation_place=body.confirmation_place.strip() if body.confirmation_place else None,
        is_married=body.is_married,
        marriage_date=body.marriage_date,
        marriage_place=body.marriage_place.strip() if body.marriage_place else None,
        spouse_name=body.spouse_name.strip() if body.spouse_name else None,
        father_name=body.father_name.strip() if body.father_name else None,
        mother_name=body.mother_name.strip() if body.mother_name else None,
        emergency_contact_name=body.emergency_contact_name.strip()
        if body.emergency_contact_name
        else None,
        emergency_contact_phone=body.emergency_contact_phone.strip()
        if body.emergency_contact_phone
        else None,
        is_deceased=body.is_deceased,
        date_of_death=body.date_of_death,
        funeral_date=body.funeral_date,
        burial_place=body.burial_place.strip() if body.burial_place else None,
        cause_of_death=body.cause_of_death.strip() if body.cause_of_death else None,
        notes=body.notes.strip() if body.notes else None,
    )
    session.add(cm)
    await session.commit()
    await session.refresh(cm)
    stmt = (
        select(ChurchMember)
        .where(ChurchMember.id == cm.id)
        .options(joinedload(ChurchMember.linked_user))
    )
    cm = (await session.execute(stmt)).unique().scalar_one()
    return church_member_to_detail(cm)


async def patch_church_member(
    session: AsyncSession,
    *,
    cm: ChurchMember,
    body: ChurchMemberPatch,
) -> ChurchMemberDetailResponse:
    data = body.model_dump(exclude_unset=True)
    for key, val in data.items():
        setattr(cm, key, val)
    if "first_name" in data or "middle_name" in data or "last_name" in data:
        cm.full_name = build_full_name(
            first_name=cm.first_name,
            middle_name=cm.middle_name,
            last_name=cm.last_name,
        )
    if cm.is_deceased or cm.membership_status == ChurchMembershipStatus.DECEASED:
        cm.is_deceased = True
        cm.membership_status = ChurchMembershipStatus.DECEASED
    await session.flush()
    await _ensure_no_duplicate_name_and_dob(
        session,
        full_name=cm.full_name,
        date_of_birth=cm.date_of_birth,
        exclude_member_id=cm.id,
    )
    await session.commit()
    stmt = (
        select(ChurchMember)
        .where(ChurchMember.id == cm.id)
        .options(joinedload(ChurchMember.linked_user))
    )
    cm2 = (await session.execute(stmt)).unique().scalar_one()
    return church_member_to_detail(cm2)


async def link_user_to_member(
    session: AsyncSession,
    *,
    cm: ChurchMember,
    user_id: uuid.UUID,
) -> ChurchMemberDetailResponse:
    u = await auth_service.get_user_by_id(session, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if u.member_id is not None and u.member_id != cm.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already linked to another church member",
        )
    existing = await session.execute(select(User.id).where(User.member_id == cm.id))
    if existing.scalar_one_or_none() is not None:
        cur = await session.execute(select(User).where(User.member_id == cm.id))
        other = cur.scalar_one()
        if other.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another user is already linked to this church member",
            )
    u.member_id = cm.id
    await session.commit()
    await session.refresh(u)
    stmt = (
        select(ChurchMember)
        .where(ChurchMember.id == cm.id)
        .options(joinedload(ChurchMember.linked_user))
    )
    cm2 = (await session.execute(stmt)).unique().scalar_one()
    detail = church_member_to_detail(cm2)
    # joinedload occasionally leaves linked_user unset on the same request/session edge;
    # patch response must still show the link we just committed.
    if detail.linked_user_id is None and u.member_id == cm2.id:
        return detail.model_copy(
            update={
                "linked_user_id": u.id,
                "user_id": u.id,
                "user_full_name": u.full_name,
                "user_email": u.email,
            },
        )
    return detail


def _age_bucket(dob: date | None) -> str:
    if dob is None:
        return "unknown"
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 13:
        return "child"
    if age < 18:
        return "youth"
    if age < 65:
        return "adult"
    return "senior"


async def church_member_stats(session: AsyncSession) -> ChurchMemberStatsResponse:
    total = int(
        (await session.execute(select(func.count()).select_from(ChurchMember))).scalar_one()
    )
    active_members = int(
        (
            await session.execute(
                select(func.count())
                .select_from(ChurchMember)
                .where(
                    ChurchMember.is_active.is_(True),
                    ChurchMember.is_deceased.is_(False),
                ),
            )
        ).scalar_one()
    )
    deceased_members = int(
        (
            await session.execute(
                select(func.count()).select_from(ChurchMember).where(ChurchMember.is_deceased.is_(True)),
            )
        ).scalar_one()
    )
    with_accounts = int(
        (
            await session.execute(
                select(func.count()).select_from(ChurchMember).join(User, User.member_id == ChurchMember.id),
            )
        ).scalar_one()
    )

    gender_q = await session.execute(
        select(ChurchMember.gender, func.count()).group_by(ChurchMember.gender),
    )
    gender_distribution = {g.value: int(c) for g, c in gender_q.all()}

    dob_rows = (await session.execute(select(ChurchMember.date_of_birth))).all()
    age_groups: dict[str, int] = {"child": 0, "youth": 0, "adult": 0, "senior": 0, "unknown": 0}
    for (dob,) in dob_rows:
        age_groups[_age_bucket(dob)] += 1

    return ChurchMemberStatsResponse(
        total_members=total,
        active_members=active_members,
        deceased_members=deceased_members,
        gender_distribution=gender_distribution,
        age_groups=age_groups,
        members_with_accounts=with_accounts,
        members_without_accounts=total - with_accounts,
    )


async def _is_active_ministry_member_of_church_member(
    session: AsyncSession,
    *,
    church_member_id: uuid.UUID,
    ministry_id: uuid.UUID,
) -> bool:
    q = (
        select(1)
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.church_member_id == church_member_id,
            MinistryMembership.ministry_id == ministry_id,
            MinistryMembership.is_active.is_(True),
        )
        .exists()
    )
    return bool((await session.execute(select(q))).scalar_one())


async def is_church_member_eligible_for_event(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    cm: ChurchMember,
) -> bool:
    if cm.is_deceased or cm.membership_status in (
        ChurchMembershipStatus.DECEASED,
        ChurchMembershipStatus.TRANSFERRED,
    ):
        return False
    if not cm.is_active or cm.membership_status not in (
        ChurchMembershipStatus.ACTIVE,
        ChurchMembershipStatus.VISITOR,
    ):
        return False
    if event.ministry_id is None:
        return True
    return await _is_active_ministry_member_of_church_member(
        session,
        church_member_id=cm.id,
        ministry_id=event.ministry_id,
    )


async def list_eligible_church_members_for_event(
    session: AsyncSession,
    *,
    event: ChurchEvent,
) -> list[EligibleChurchMemberListItem]:
    stmt: Select[tuple[ChurchMember]] = select(ChurchMember).where(
        ChurchMember.is_active.is_(True),
        ChurchMember.is_deceased.is_(False),
        ChurchMember.membership_status.in_(
            [ChurchMembershipStatus.ACTIVE, ChurchMembershipStatus.VISITOR],
        ),
    )
    if event.ministry_id is not None:
        mm_exists = (
            select(1)
            .select_from(MinistryMembership)
            .where(
                MinistryMembership.church_member_id == ChurchMember.id,
                MinistryMembership.ministry_id == event.ministry_id,
                MinistryMembership.is_active.is_(True),
            )
            .exists()
        )
        stmt = stmt.where(mm_exists)
    stmt = stmt.order_by(ChurchMember.full_name.asc()).options(
        joinedload(ChurchMember.linked_user),
    )
    rows = list((await session.execute(stmt)).unique().scalars().all())
    return [
        EligibleChurchMemberListItem(
            id=r.id,
            full_name=r.full_name,
            email=contact_email(church_member=r, linked_user=r.linked_user),
            phone=r.phone,
        )
        for r in rows
    ]
