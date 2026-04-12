from __future__ import annotations

import uuid
from typing import Annotated

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import NotificationCategory, NotificationChannel, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.event_reminders.schemas import RunDueRemindersResponse
from app.modules.event_reminders import service as event_reminders_service
from app.modules.notifications import service as notifications_service
from app.modules.audit_logs.actions import NOTIFICATION_RUN_DUE_REMINDERS, NOTIFICATION_SEND
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
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


@router.post("/jobs/run-reminders", response_model=RunDueRemindersResponse)
async def run_due_reminders_job(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    request: Request,
    as_of: datetime | None = Query(
        default=None,
        description="Simulate wall-clock time (UTC) for tests and manual verification; omit in production cron.",
    ),
) -> RunDueRemindersResponse:
    """Process due event reminder rules (manual trigger for dev/ops; same entrypoint as future cron)."""
    out = await event_reminders_service.run_due_reminders(session, now=as_of)
    await record_audit_event(
        action=NOTIFICATION_RUN_DUE_REMINDERS,
        summary="Ran due event reminders job",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="notification_job",
        metadata={
            "rules_considered": out.rules_considered,
            "reminders_sent": out.reminders_sent,
            "skipped_not_due": out.skipped_not_due,
            "skipped_already_sent": out.skipped_already_sent,
            "skipped_invalid": out.skipped_invalid,
            "failed": out.failed,
            "as_of_set": as_of is not None,
        },
        ip_address=client_ip_from_request(request),
    )
    return out


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
    request: Request,
    body: NotificationCreateRequest,
) -> NotificationDetailResponse:
    out = await notifications_service.create_and_send_notification(session, admin=admin, body=body)
    await record_audit_event(
        action=NOTIFICATION_SEND,
        summary=f"Notification sent: {body.title[:120]}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="notification",
        target_id=str(out.id),
        metadata={
            "category": body.category.value,
            "audience_type": body.audience_type.value,
            "channels": [c.value for c in body.channels],
        },
        ip_address=client_ip_from_request(request),
    )
    return out


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
