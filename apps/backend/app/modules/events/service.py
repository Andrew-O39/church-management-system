from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import EventVisibility, EventType, UserRole
from app.db.models.church_event import ChurchEvent
from app.db.models.ministry_group import MinistryGroup
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.modules.events.schemas import (
    EventCreate,
    EventDetailResponse,
    EventListItem,
    EventMemberViewResponse,
    EventPatch,
)


def _require_end_after_start(start_at, end_at) -> None:
    if end_at < start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_at must be after or equal to start_at",
        )


def _event_to_list_item(event: ChurchEvent) -> EventListItem:
    return EventListItem(
        event_id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        start_at=event.start_at,
        end_at=event.end_at,
        location=event.location,
        is_active=event.is_active,
        visibility=event.visibility,
        ministry_id=event.ministry_id,
        ministry_name=event.ministry.name if event.ministry is not None else None,
    )


def _event_to_detail(event: ChurchEvent) -> EventDetailResponse:
    return EventDetailResponse(
        event_id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        start_at=event.start_at,
        end_at=event.end_at,
        location=event.location,
        is_active=event.is_active,
        visibility=event.visibility,
        ministry_id=event.ministry_id,
        ministry_name=event.ministry.name if event.ministry is not None else None,
        created_by_user_id=event.created_by_user_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def event_detail_response(event: ChurchEvent) -> EventDetailResponse:
    # Public wrapper for router-level usage.
    return _event_to_detail(event)


def _event_to_member_view(event: ChurchEvent) -> EventMemberViewResponse:
    return EventMemberViewResponse(
        event_id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        start_at=event.start_at,
        end_at=event.end_at,
        location=event.location,
        is_active=event.is_active,
        visibility=event.visibility,
        ministry_id=event.ministry_id,
        ministry_name=event.ministry.name if event.ministry is not None else None,
    )


async def get_event_or_404(session: AsyncSession, event_id: uuid.UUID) -> ChurchEvent:
    stmt = select(ChurchEvent).where(ChurchEvent.id == event_id).options(selectinload(ChurchEvent.ministry))
    res = await session.execute(stmt)
    ev = res.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return ev


async def assert_ministry_active_if_needed(
    *,
    ministry: MinistryGroup | None,
    resulting_is_active: bool,
) -> None:
    if ministry is None:
        return
    if ministry.is_active and resulting_is_active:
        return
    if not ministry.is_active and resulting_is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot make an event active for an inactive ministry",
        )


async def list_events_admin(
    session: AsyncSession,
    *,
    search: str | None,
    is_active: bool | None,
    event_type: EventType | None,
    ministry_id: uuid.UUID | None,
    start_from,
    start_to,
    page: int,
    page_size: int,
) -> tuple[list[ChurchEvent], int]:
    stmt = select(ChurchEvent).options(selectinload(ChurchEvent.ministry))

    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(ChurchEvent.title.ilike(term))
    if is_active is not None:
        stmt = stmt.where(ChurchEvent.is_active.is_(is_active))
    if event_type is not None:
        stmt = stmt.where(ChurchEvent.event_type == event_type)
    if ministry_id is not None:
        stmt = stmt.where(ChurchEvent.ministry_id == ministry_id)
    if start_from is not None:
        stmt = stmt.where(ChurchEvent.start_at >= start_from)
    if start_to is not None:
        stmt = stmt.where(ChurchEvent.start_at <= start_to)

    count_base = stmt.subquery()
    count_q = await session.execute(select(func.count()).select_from(count_base))
    total = int(count_q.scalar_one())

    stmt = (
        stmt.order_by(ChurchEvent.start_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    return rows, total


async def list_events_admin_response(
    session: AsyncSession,
    *,
    search: str | None,
    is_active: bool | None,
    event_type: EventType | None,
    ministry_id: uuid.UUID | None,
    start_from,
    start_to,
    page: int,
    page_size: int,
):
    rows, total = await list_events_admin(
        session,
        search=search,
        is_active=is_active,
        event_type=event_type,
        ministry_id=ministry_id,
        start_from=start_from,
        start_to=start_to,
        page=page,
        page_size=page_size,
    )
    items = [_event_to_list_item(e) for e in rows]
    from app.modules.events.schemas import EventListResponse

    return EventListResponse(items=items, total=total, page=page, page_size=page_size)


async def create_event(session: AsyncSession, *, creator: User, body: EventCreate) -> ChurchEvent:
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title is required")
    _require_end_after_start(body.start_at, body.end_at)

    ministry: MinistryGroup | None = None
    if body.ministry_id is not None:
        stmt = select(MinistryGroup).where(MinistryGroup.id == body.ministry_id)
        ministry = (await session.execute(stmt)).scalar_one_or_none()
        if ministry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministry not found")

    await assert_ministry_active_if_needed(ministry=ministry, resulting_is_active=body.is_active)

    ev = ChurchEvent(
        title=title,
        description=body.description.strip() if body.description else None,
        event_type=body.event_type,
        start_at=body.start_at,
        end_at=body.end_at,
        location=body.location.strip(),
        is_active=body.is_active,
        visibility=body.visibility,
        ministry_id=body.ministry_id,
        created_by_user_id=creator.id,
    )
    session.add(ev)
    await session.commit()
    await session.refresh(ev)
    await session.refresh(ev, attribute_names=["ministry"])
    return ev


async def create_event_response(session: AsyncSession, *, creator: User, body: EventCreate) -> EventDetailResponse:
    ev = await create_event(session, creator=creator, body=body)
    # `create_event` refreshes `ministry` lazily so we can convert directly.
    return _event_to_detail(ev)


async def patch_event(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    body: EventPatch,
    admin: User,
) -> ChurchEvent:
    data = body.model_dump(exclude_unset=True)

    resulting_start_at = data.get("start_at", event.start_at)
    resulting_end_at = data.get("end_at", event.end_at)
    _require_end_after_start(resulting_start_at, resulting_end_at)

    resulting_is_active = data.get("is_active", event.is_active)

    ministry: MinistryGroup | None = None
    resulting_ministry_id = data.get("ministry_id", event.ministry_id)
    if resulting_ministry_id is not None:
        stmt = select(MinistryGroup).where(MinistryGroup.id == resulting_ministry_id)
        ministry = (await session.execute(stmt)).scalar_one_or_none()
        if ministry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministry not found")

    await assert_ministry_active_if_needed(ministry=ministry, resulting_is_active=resulting_is_active)

    if "title" in data and data["title"] is not None:
        title = str(data["title"]).strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title is required")
        event.title = title
    if "description" in data:
        event.description = data["description"].strip() if data["description"] is not None else None
    if "event_type" in data and data["event_type"] is not None:
        event.event_type = data["event_type"]
    if "start_at" in data and data["start_at"] is not None:
        event.start_at = data["start_at"]
    if "end_at" in data and data["end_at"] is not None:
        event.end_at = data["end_at"]
    if "location" in data and data["location"] is not None:
        event.location = str(data["location"]).strip()
    if "is_active" in data and data["is_active"] is not None:
        event.is_active = bool(data["is_active"])
    if "visibility" in data and data["visibility"] is not None:
        event.visibility = data["visibility"]
    if "ministry_id" in data:
        event.ministry_id = data["ministry_id"]

    await session.commit()
    await session.refresh(event)
    return event


async def patch_event_response(
    session: AsyncSession,
    *,
    event: ChurchEvent,
    admin: User,
    body: EventPatch,
) -> EventDetailResponse:
    ev = await patch_event(session, event=event, body=body, admin=admin)
    await session.refresh(ev, attribute_names=["ministry"])
    return _event_to_detail(ev)


async def deactivate_event(session: AsyncSession, *, event: ChurchEvent) -> None:
    event.is_active = False
    await session.commit()


async def list_my_visible_events_response(session: AsyncSession, user: User):
    from app.modules.events.schemas import MyEventsResponse

    items = await list_my_visible_events(session, user)
    return MyEventsResponse(items=items)


async def list_my_visible_events(session: AsyncSession, user: User) -> list[EventListItem]:
    stmt = (
        select(ChurchEvent)
        .options(selectinload(ChurchEvent.ministry))
        .where(ChurchEvent.is_active.is_(True))
    )

    if user.role == UserRole.ADMIN:
        rows = list(
            (await session.execute(stmt.order_by(ChurchEvent.start_at.asc())))
            .scalars()
            .unique()
            .all()
        )
        return [_event_to_list_item(e) for e in rows]

    # Visible to authenticated non-admins:
    # - church-wide public or internal events
    # - ministry-linked events where user has an active membership
    membership_exists = (
        select(1)
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.ministry_id == ChurchEvent.ministry_id,
            MinistryMembership.user_id == user.id,
            MinistryMembership.is_active.is_(True),
        )
        .exists()
    )

    stmt = stmt.where(
        or_(
            and_(
                ChurchEvent.ministry_id.is_(None),
                ChurchEvent.visibility.in_(
                    [EventVisibility.PUBLIC, EventVisibility.INTERNAL]
                ),
            ),
            and_(ChurchEvent.ministry_id.is_not(None), membership_exists),
        )
    )

    rows = list(
        (await session.execute(stmt.order_by(ChurchEvent.start_at.asc())))
        .scalars()
        .unique()
        .all()
    )
    return [_event_to_list_item(e) for e in rows]

async def get_member_event_view(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    user: User,
) -> EventMemberViewResponse:
    event = await get_event_or_404(session, event_id)

    if not event.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if user.role == UserRole.ADMIN:
        return _event_to_member_view(event)

    if event.ministry_id is None:
        if event.visibility not in {
            EventVisibility.PUBLIC,
            EventVisibility.INTERNAL,
        }:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return _event_to_member_view(event)

    # Ministry-linked events are visible only to users with active membership.
    membership_exists = (
        select(1)
        .select_from(MinistryMembership)
        .where(
            MinistryMembership.ministry_id == event.ministry_id,
            MinistryMembership.user_id == user.id,
            MinistryMembership.is_active.is_(True),
        )
        .exists()
    )
    res = await session.execute(select(membership_exists))
    if not res.scalar_one():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    return _event_to_member_view(event)

