from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import NotificationCategory, NotificationChannel, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.notifications import service as notifications_service
from app.modules.notifications.schemas import (
    MarkAllReadResponse,
    MarkReadResponse,
    MyNotificationsResponse,
    NotificationCreateRequest,
    NotificationDetailResponse,
    NotificationListResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

_MAX_PAGE_SIZE = 100


@router.get("/me/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> UnreadCountResponse:
    return await notifications_service.unread_count(session, user=user)


@router.get("/me", response_model=MyNotificationsResponse)
async def list_my_notifications(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> MyNotificationsResponse:
    return await notifications_service.list_my_notifications(
        session,
        user=user,
        page=page,
        page_size=page_size,
    )


@router.patch("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MarkAllReadResponse:
    return await notifications_service.mark_all_read(session, user=user)


@router.patch("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_one_notification_read(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
    notification_id: uuid.UUID,
) -> MarkReadResponse:
    return await notifications_service.mark_notification_read(
        session,
        user=user,
        notification_id=notification_id,
    )


@router.post(
    "/",
    response_model=NotificationDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    body: NotificationCreateRequest,
) -> NotificationDetailResponse:
    return await notifications_service.create_and_send_notification(session, admin=admin, body=body)


@router.get("/", response_model=NotificationListResponse)
async def list_notifications_admin(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    category: NotificationCategory | None = Query(default=None),
    channel: NotificationChannel | None = Query(
        default=None,
        description="Filter notifications that include this channel",
    ),
    related_event_id: uuid.UUID | None = Query(default=None),
    related_ministry_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> NotificationListResponse:
    return await notifications_service.list_notifications_admin(
        session,
        category=category,
        related_event_id=related_event_id,
        related_ministry_id=related_ministry_id,
        channel=channel,
        page=page,
        page_size=page_size,
    )


@router.get("/{notification_id}", response_model=NotificationDetailResponse)
async def get_notification_admin(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    notification_id: uuid.UUID,
) -> NotificationDetailResponse:
    return await notifications_service.get_notification_admin(session, notification_id=notification_id)
