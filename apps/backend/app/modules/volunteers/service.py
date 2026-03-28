from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models.church_event import ChurchEvent
from app.db.models.church_member import ChurchMember
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.db.models.volunteer_role import VolunteerRole
from app.modules.attendance import service as attendance_service
from app.modules.auth import service as auth_service
from app.modules.church_registry import service as registry_service
from app.modules.church_registry.person_display import linked_account_fields
from app.modules.volunteers.schemas import (
    EventVolunteerListResponse,
    MyEventVolunteerAssignmentsResponse,
    MyVolunteerAssignmentItem,
    MyVolunteerAssignmentsResponse,
    VolunteerAssignmentCreate,
    VolunteerAssignmentPatch,
    VolunteerAssignmentRow,
    VolunteerRoleCreate,
    VolunteerRoleDetailResponse,
    VolunteerRoleListItem,
    VolunteerRoleListResponse,
    VolunteerRolePatch,
)

_MAX_PAGE_SIZE = 100


def normalize_role_name_key(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def display_role_name(name: str) -> str:
    s = name.strip()
    return re.sub(r"\s+", " ", s)


def role_fits_event(*, role: VolunteerRole, event: ChurchEvent) -> bool:
    if role.ministry_id is None:
        return True
    return event.ministry_id is not None and role.ministry_id == event.ministry_id


def assert_role_fits_event(*, role: VolunteerRole, event: ChurchEvent) -> None:
    if not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volunteer role is inactive",
        )
    if role.ministry_id is not None:
        if event.ministry_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ministry-scoped volunteer role cannot be used on a church-wide event",
            )
        if role.ministry_id != event.ministry_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volunteer role ministry does not match this event's ministry",
            )


def volunteer_role_to_detail(role: VolunteerRole) -> VolunteerRoleDetailResponse:
    return VolunteerRoleDetailResponse.model_validate(_role_to_list_item(role).model_dump())


def _role_to_list_item(role: VolunteerRole) -> VolunteerRoleListItem:
    ministry_name = role.ministry.name if role.ministry is not None else None
    return VolunteerRoleListItem(
        id=role.id,
        name=role.name,
        description=role.description,
        ministry_id=role.ministry_id,
        ministry_name=ministry_name,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def _volunteer_role_filters(
    stmt: Select,
    *,
    search: str | None,
    is_active: bool | None,
    ministry_id: uuid.UUID | None,
) -> Select:
    if search:
        k = f"%{search.strip().lower()}%"
        stmt = stmt.where(VolunteerRole.name_key.ilike(k))
    if is_active is not None:
        stmt = stmt.where(VolunteerRole.is_active.is_(is_active))
    if ministry_id is not None:
        stmt = stmt.where(VolunteerRole.ministry_id == ministry_id)
    return stmt


async def list_volunteer_roles_admin(
    session: AsyncSession,
    *,
    search: str | None,
    is_active: bool | None,
    ministry_id: uuid.UUID | None,
    for_event_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> VolunteerRoleListResponse:
    psize = min(page_size, _MAX_PAGE_SIZE)
    offset = (page - 1) * psize

    if for_event_id is None:
        count_stmt = select(func.count()).select_from(VolunteerRole)
        count_stmt = _volunteer_role_filters(
            count_stmt, search=search, is_active=is_active, ministry_id=ministry_id
        )
        total = int((await session.execute(count_stmt)).scalar_one())

        page_stmt = select(VolunteerRole).options(selectinload(VolunteerRole.ministry))
        page_stmt = _volunteer_role_filters(
            page_stmt, search=search, is_active=is_active, ministry_id=ministry_id
        )
        page_stmt = page_stmt.order_by(VolunteerRole.name_key).offset(offset).limit(psize)
        rows = list((await session.execute(page_stmt)).scalars().unique().all())
        items = [_role_to_list_item(r) for r in rows]
        return VolunteerRoleListResponse(
            items=items,
            total=total,
            page=page,
            page_size=psize,
        )

    event = await attendance_service.get_event_or_404(session, for_event_id)
    page_stmt = select(VolunteerRole).options(selectinload(VolunteerRole.ministry))
    page_stmt = _volunteer_role_filters(
        page_stmt, search=search, is_active=is_active, ministry_id=ministry_id
    )
    page_stmt = page_stmt.order_by(VolunteerRole.name_key)
    all_roles = list((await session.execute(page_stmt)).scalars().unique().all())
    filtered = [r for r in all_roles if role_fits_event(role=r, event=event)]
    total = len(filtered)
    page_items = filtered[offset : offset + psize]
    items = [_role_to_list_item(r) for r in page_items]
    return VolunteerRoleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=psize,
    )


async def get_volunteer_role_or_404(
    session: AsyncSession,
    role_id: uuid.UUID,
) -> VolunteerRole:
    stmt = (
        select(VolunteerRole)
        .where(VolunteerRole.id == role_id)
        .options(selectinload(VolunteerRole.ministry))
    )
    r = (await session.execute(stmt)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer role not found")
    return r


async def create_volunteer_role(
    session: AsyncSession,
    *,
    body: VolunteerRoleCreate,
) -> VolunteerRoleDetailResponse:
    name = display_role_name(body.name)
    key = normalize_role_name_key(body.name)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volunteer role name is required",
        )
    role = VolunteerRole(
        name=name,
        name_key=key,
        description=body.description,
        ministry_id=body.ministry_id,
        is_active=body.is_active,
    )
    session.add(role)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A volunteer role with this name already exists",
        ) from None
    await session.refresh(role)
    stmt = (
        select(VolunteerRole)
        .where(VolunteerRole.id == role.id)
        .options(selectinload(VolunteerRole.ministry))
    )
    role = (await session.execute(stmt)).scalar_one()
    return volunteer_role_to_detail(role)


async def patch_volunteer_role(
    session: AsyncSession,
    *,
    role: VolunteerRole,
    body: VolunteerRolePatch,
) -> VolunteerRoleDetailResponse:
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        role.name = display_role_name(data["name"])
        role.name_key = normalize_role_name_key(data["name"])
        if not role.name_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volunteer role name is required",
            )
    if "description" in data:
        role.description = data["description"]
    if "ministry_id" in data:
        role.ministry_id = data["ministry_id"]
    if "is_active" in data and data["is_active"] is not None:
        role.is_active = data["is_active"]

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A volunteer role with this name already exists",
        ) from None

    stmt = (
        select(VolunteerRole)
        .where(VolunteerRole.id == role.id)
        .options(selectinload(VolunteerRole.ministry))
    )
    role = (await session.execute(stmt)).scalar_one()
    return volunteer_role_to_detail(role)


def _to_assignment_row(va: VolunteerAssignment) -> VolunteerAssignmentRow:
    cm = va.church_member
    role = va.role
    if cm is None or role is None:
        raise RuntimeError("VolunteerAssignment missing church_member or role")
    lu = cm.linked_user if cm.linked_user is not None else None
    uid, ufn, uem = linked_account_fields(lu)
    return VolunteerAssignmentRow(
        id=va.id,
        event_id=va.event_id,
        church_member_id=va.church_member_id,
        member_full_name=cm.full_name,
        member_email=cm.email,
        linked_user_id=uid,
        linked_user_email=uem,
        user_id=uid,
        user_full_name=ufn,
        user_email=uem,
        role_id=va.role_id,
        role_name=role.name,
        notes=va.notes,
        assigned_by_user_id=va.assigned_by_user_id,
        created_at=va.created_at,
        updated_at=va.updated_at,
    )


async def list_event_volunteers_admin(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
) -> EventVolunteerListResponse:
    await attendance_service.get_event_or_404(session, event_id)
    stmt = (
        select(VolunteerAssignment)
        .where(VolunteerAssignment.event_id == event_id)
        .options(
            selectinload(VolunteerAssignment.church_member).joinedload(ChurchMember.linked_user),
            selectinload(VolunteerAssignment.role),
        )
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    items = [_to_assignment_row(r) for r in rows]
    return EventVolunteerListResponse(items=items)


async def get_assignment_for_event_or_404(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> VolunteerAssignment:
    stmt = (
        select(VolunteerAssignment)
        .where(
            VolunteerAssignment.id == assignment_id,
            VolunteerAssignment.event_id == event_id,
        )
        .options(
            selectinload(VolunteerAssignment.church_member).joinedload(ChurchMember.linked_user),
            selectinload(VolunteerAssignment.role),
            selectinload(VolunteerAssignment.event),
        )
    )
    va = (await session.execute(stmt)).scalar_one_or_none()
    if va is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer assignment not found",
        )
    return va


async def _resolve_assignment_church_member(
    session: AsyncSession,
    body: VolunteerAssignmentCreate,
) -> ChurchMember:
    if body.church_member_id is not None:
        return await registry_service.get_church_member_or_404(session, body.church_member_id)
    assert body.user_id is not None
    target = await auth_service.get_user_by_id(session, body.user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive users cannot be assigned",
        )
    if target.member_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to a church member record",
        )
    return await registry_service.get_church_member_or_404(session, target.member_id)


async def create_volunteer_assignment(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    body: VolunteerAssignmentCreate,
    admin_user_id: uuid.UUID,
) -> VolunteerAssignmentRow:
    event = await attendance_service.get_event_or_404(session, event_id)
    if not event.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add volunteer assignments to an inactive event",
        )

    cm = await _resolve_assignment_church_member(session, body)

    if not await registry_service.is_church_member_eligible_for_event(session, event=event, cm=cm):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Church member is not eligible for volunteer assignments on this event",
        )

    role = await get_volunteer_role_or_404(session, body.role_id)
    assert_role_fits_event(role=role, event=event)

    va = VolunteerAssignment(
        event_id=event_id,
        church_member_id=cm.id,
        role_id=body.role_id,
        notes=body.notes,
        assigned_by_user_id=admin_user_id,
    )
    session.add(va)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This church member is already assigned to this role for this event",
        ) from None

    await session.refresh(va)
    stmt = (
        select(VolunteerAssignment)
        .where(VolunteerAssignment.id == va.id)
        .options(
            selectinload(VolunteerAssignment.church_member).joinedload(ChurchMember.linked_user),
            selectinload(VolunteerAssignment.role),
        )
    )
    va = (await session.execute(stmt)).scalar_one()
    return _to_assignment_row(va)


async def patch_volunteer_assignment(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: VolunteerAssignmentPatch,
    admin_user_id: uuid.UUID,
) -> VolunteerAssignmentRow:
    va = await get_assignment_for_event_or_404(session, event_id=event_id, assignment_id=assignment_id)
    event = va.event
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    if "role_id" in data and data["role_id"] is not None:
        role = await get_volunteer_role_or_404(session, data["role_id"])
        assert_role_fits_event(role=role, event=event)
        va.role_id = data["role_id"]

    if "notes" in data:
        va.notes = data["notes"]

    va.assigned_by_user_id = admin_user_id

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This church member is already assigned to this role for this event",
        ) from None

    stmt = (
        select(VolunteerAssignment)
        .where(VolunteerAssignment.id == va.id)
        .options(
            selectinload(VolunteerAssignment.church_member).joinedload(ChurchMember.linked_user),
            selectinload(VolunteerAssignment.role),
        )
    )
    va = (await session.execute(stmt)).scalar_one()
    return _to_assignment_row(va)


async def delete_volunteer_assignment(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> None:
    va = await get_assignment_for_event_or_404(session, event_id=event_id, assignment_id=assignment_id)
    await session.delete(va)
    await session.commit()


async def list_my_volunteer_assignments(
    session: AsyncSession,
    *,
    user: User,
) -> MyVolunteerAssignmentsResponse:
    if user.member_id is None:
        return MyVolunteerAssignmentsResponse(items=[])
    stmt = (
        select(VolunteerAssignment)
        .where(VolunteerAssignment.church_member_id == user.member_id)
        .options(
            selectinload(VolunteerAssignment.role),
            selectinload(VolunteerAssignment.event).selectinload(ChurchEvent.ministry),
        )
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    items: list[MyVolunteerAssignmentItem] = []
    for va in rows:
        ev = va.event
        if ev is None or va.role is None:
            continue
        if not await attendance_service.can_user_view_event(session, event=ev, user=user):
            continue
        items.append(
            MyVolunteerAssignmentItem(
                assignment_id=va.id,
                event_id=ev.id,
                event_title=ev.title,
                start_at=ev.start_at,
                end_at=ev.end_at,
                location=ev.location,
                role_id=va.role_id,
                role_name=va.role.name,
                notes=va.notes,
            )
        )
    items.sort(key=lambda x: x.start_at, reverse=True)
    return MyVolunteerAssignmentsResponse(items=items)


async def list_my_event_volunteer_assignments(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    user: User,
) -> MyEventVolunteerAssignmentsResponse:
    event = await attendance_service.get_event_or_404(session, event_id)
    if not await attendance_service.can_user_view_event(session, event=event, user=user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if user.member_id is None:
        return MyEventVolunteerAssignmentsResponse(items=[])

    stmt = (
        select(VolunteerAssignment)
        .where(
            VolunteerAssignment.event_id == event_id,
            VolunteerAssignment.church_member_id == user.member_id,
        )
        .options(
            selectinload(VolunteerAssignment.church_member).joinedload(ChurchMember.linked_user),
            selectinload(VolunteerAssignment.role),
        )
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    return MyEventVolunteerAssignmentsResponse(items=[_to_assignment_row(r) for r in rows])
