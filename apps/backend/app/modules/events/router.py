from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import EventType, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.events import service as events_service
from app.modules.audit_logs.actions import EVENTS_CREATE, EVENTS_UPDATE
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
from app.modules.events.schemas import (
    EventCreate,
    EventDetailResponse,
    EventMemberViewResponse,
    EventListResponse,
    EventPatch,
    MyEventsResponse,
)

router = APIRouter(prefix="/events", tags=["events"])

_MAX_PAGE_SIZE = 100


@router.get("/me", response_model=MyEventsResponse)
async def list_my_events(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MyEventsResponse:
    return await events_service.list_my_visible_events_response(session, user)


@router.get(
    "/",
    response_model=EventListResponse,
)
async def list_events_admin(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    is_active: bool | None = Query(default=None),
    event_type: EventType | None = Query(default=None),
    ministry_id: uuid.UUID | None = Query(default=None),
    start_from: datetime | None = Query(default=None),
    start_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> EventListResponse:
    return await events_service.list_events_admin_response(
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


@router.post("/", response_model=EventDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventDetailResponse:
    out = await events_service.create_event_response(session, creator=admin, body=body)
    await record_audit_event(
        action=EVENTS_CREATE,
        summary=f"Event created: {out.title}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event",
        target_id=str(out.event_id),
        metadata={"title": out.title},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventDetailResponse:
    event = await events_service.get_event_or_404(session, event_id)
    return events_service.event_detail_response(event)


@router.patch("/{event_id}", response_model=EventDetailResponse)
async def patch_event(
    event_id: uuid.UUID,
    body: EventPatch,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventDetailResponse:
    event = await events_service.get_event_or_404(session, event_id)
    out = await events_service.patch_event_response(session, event=event, admin=admin, body=body)
    fields = sorted(body.model_dump(exclude_unset=True).keys())
    await record_audit_event(
        action=EVENTS_UPDATE,
        summary=f"Event updated: {out.title}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event",
        target_id=str(out.event_id),
        metadata={"fields_changed": fields},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def deactivate_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    event = await events_service.get_event_or_404(session, event_id)
    await events_service.deactivate_event(session, event=event)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{event_id}/view", response_model=EventMemberViewResponse)
async def view_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> EventMemberViewResponse:
    return await events_service.get_member_event_view(session, event_id=event_id, user=user)

