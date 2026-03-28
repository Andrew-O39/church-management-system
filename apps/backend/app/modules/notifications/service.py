from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.enums import (
    NotificationAudienceType,
    NotificationCategory,
    NotificationChannel,
    NotificationRecipientStatus,
)
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.notification import Notification
from app.db.models.notification_recipient import NotificationRecipient
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.modules.auth import service as auth_service
from app.modules.events import service as events_service
from app.modules.ministries import service as ministries_service
from app.modules.notifications.schemas import (
    MarkAllReadResponse,
    MarkReadResponse,
    MyNotificationItem,
    MyNotificationsResponse,
    NotificationCreateRequest,
    NotificationDetailResponse,
    NotificationListItem,
    NotificationListResponse,
    NotificationRecipientRow,
    UnreadCountResponse,
)

_MAX_PAGE_SIZE = 100


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _resolve_recipient_user_ids(
    session: AsyncSession,
    *,
    audience_type: NotificationAudienceType,
    user_ids: list[uuid.UUID] | None,
    ministry_id: uuid.UUID | None,
    event_id: uuid.UUID | None,
) -> list[uuid.UUID]:
    if audience_type == NotificationAudienceType.DIRECT_USERS:
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_ids is required for direct_users audience",
            )
        unique = list(dict.fromkeys(user_ids))
        resolved: list[uuid.UUID] = []
        for uid in unique:
            u = await auth_service.get_user_by_id(session, uid)
            if u is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {uid}",
                )
            if not u.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User is not active: {uid}",
                )
            resolved.append(uid)
        return resolved

    if audience_type == NotificationAudienceType.MINISTRY_MEMBERS:
        if ministry_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ministry_id is required for ministry_members audience",
            )
        m = await ministries_service.get_ministry(session, ministry_id)
        if m is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ministry not found")
        stmt = select(MinistryMembership.user_id).where(
            MinistryMembership.ministry_id == ministry_id,
            MinistryMembership.is_active.is_(True),
        )
        rows = (await session.execute(stmt)).scalars().all()
        return list(dict.fromkeys(rows))

    if audience_type == NotificationAudienceType.EVENT_VOLUNTEERS:
        if event_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="event_id is required for event_volunteers audience",
            )
        await events_service.get_event_or_404(session, event_id)
        stmt = select(VolunteerAssignment.user_id).where(VolunteerAssignment.event_id == event_id)
        rows = (await session.execute(stmt)).scalars().all()
        return list(dict.fromkeys(rows))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported audience_type",
    )


async def create_and_send_notification(
    session: AsyncSession,
    *,
    admin: User,
    body: NotificationCreateRequest,
) -> NotificationDetailResponse:
    if body.delivery_channel != NotificationChannel.IN_APP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only in_app delivery is supported in this release",
        )

    recipient_ids = await _resolve_recipient_user_ids(
        session,
        audience_type=body.audience_type,
        user_ids=body.user_ids,
        ministry_id=body.ministry_id,
        event_id=body.event_id,
    )
    if not recipient_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients resolved for this audience",
        )

    related_event_id: uuid.UUID | None = None
    related_ministry_id: uuid.UUID | None = None
    if body.audience_type == NotificationAudienceType.MINISTRY_MEMBERS:
        related_ministry_id = body.ministry_id
    elif body.audience_type == NotificationAudienceType.EVENT_VOLUNTEERS:
        related_event_id = body.event_id

    now = _now()
    n = Notification(
        title=body.title,
        body=body.body,
        category=body.category,
        delivery_channel=body.delivery_channel,
        audience_type=body.audience_type,
        related_event_id=related_event_id,
        related_ministry_id=related_ministry_id,
        created_by_user_id=admin.id,
        sent_at=now,
    )
    session.add(n)
    await session.flush()

    for uid in recipient_ids:
        session.add(
            NotificationRecipient(
                notification_id=n.id,
                user_id=uid,
                status=NotificationRecipientStatus.DELIVERED,
            )
        )

    await session.commit()
    await session.refresh(n)

    stmt = (
        select(Notification)
        .where(Notification.id == n.id)
        .options(selectinload(Notification.recipients))
    )
    n2 = (await session.execute(stmt)).scalar_one()
    return notification_detail_response(n2)


def notification_detail_response(n: Notification) -> NotificationDetailResponse:
    recs = sorted(n.recipients, key=lambda r: r.created_at)
    return NotificationDetailResponse(
        id=n.id,
        title=n.title,
        body=n.body,
        category=n.category,
        delivery_channel=n.delivery_channel,
        audience_type=n.audience_type,
        related_event_id=n.related_event_id,
        related_ministry_id=n.related_ministry_id,
        created_by_user_id=n.created_by_user_id,
        created_at=n.created_at,
        updated_at=n.updated_at,
        sent_at=n.sent_at,
        recipients=[NotificationRecipientRow.model_validate(r) for r in recs],
    )


async def list_notifications_admin(
    session: AsyncSession,
    *,
    category: NotificationCategory | None,
    related_event_id: uuid.UUID | None,
    related_ministry_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> NotificationListResponse:
    count_stmt = select(func.count()).select_from(Notification)
    list_stmt = select(Notification)
    if category is not None:
        count_stmt = count_stmt.where(Notification.category == category)
        list_stmt = list_stmt.where(Notification.category == category)
    if related_event_id is not None:
        count_stmt = count_stmt.where(Notification.related_event_id == related_event_id)
        list_stmt = list_stmt.where(Notification.related_event_id == related_event_id)
    if related_ministry_id is not None:
        count_stmt = count_stmt.where(Notification.related_ministry_id == related_ministry_id)
        list_stmt = list_stmt.where(Notification.related_ministry_id == related_ministry_id)

    total = int((await session.execute(count_stmt)).scalar_one())

    stmt = (
        list_stmt.options(selectinload(Notification.recipients))
        .order_by(Notification.sent_at.desc().nulls_last(), Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list((await session.execute(stmt)).scalars().unique().all())
    items = [
        NotificationListItem(
            id=r.id,
            title=r.title,
            category=r.category,
            delivery_channel=r.delivery_channel,
            audience_type=r.audience_type,
            related_event_id=r.related_event_id,
            related_ministry_id=r.related_ministry_id,
            created_by_user_id=r.created_by_user_id,
            created_at=r.created_at,
            sent_at=r.sent_at,
            recipient_count=len(r.recipients),
        )
        for r in rows
    ]
    return NotificationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_notification_admin(
    session: AsyncSession,
    *,
    notification_id: uuid.UUID,
) -> NotificationDetailResponse:
    stmt = (
        select(Notification)
        .where(Notification.id == notification_id)
        .options(selectinload(Notification.recipients))
    )
    n = (await session.execute(stmt)).scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification_detail_response(n)


async def list_my_notifications(
    session: AsyncSession,
    *,
    user: User,
    page: int,
    page_size: int,
) -> MyNotificationsResponse:
    count_stmt = (
        select(func.count())
        .select_from(NotificationRecipient)
        .join(Notification, NotificationRecipient.notification_id == Notification.id)
        .where(NotificationRecipient.user_id == user.id)
    )
    total = int((await session.execute(count_stmt)).scalar_one())

    stmt = (
        select(NotificationRecipient, Notification)
        .join(Notification, NotificationRecipient.notification_id == Notification.id)
        .where(NotificationRecipient.user_id == user.id)
        .order_by(Notification.sent_at.desc().nulls_last(), Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    rows = result.all()
    items: list[MyNotificationItem] = []
    for rec, n in rows:
        items.append(
            MyNotificationItem(
                notification_id=n.id,
                title=n.title,
                body=n.body,
                category=n.category,
                delivery_channel=n.delivery_channel,
                related_event_id=n.related_event_id,
                related_ministry_id=n.related_ministry_id,
                sent_at=n.sent_at,
                created_at=n.created_at,
                recipient_status=rec.status,
                read_at=rec.read_at,
            )
        )
    return MyNotificationsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def unread_count(session: AsyncSession, *, user: User) -> UnreadCountResponse:
    stmt = (
        select(func.count())
        .select_from(NotificationRecipient)
        .where(
            NotificationRecipient.user_id == user.id,
            NotificationRecipient.status == NotificationRecipientStatus.DELIVERED,
        )
    )
    n = int((await session.execute(stmt)).scalar_one())
    return UnreadCountResponse(unread_count=n)


async def mark_notification_read(
    session: AsyncSession,
    *,
    user: User,
    notification_id: uuid.UUID,
) -> MarkReadResponse:
    stmt = select(NotificationRecipient).where(
        NotificationRecipient.notification_id == notification_id,
        NotificationRecipient.user_id == user.id,
    )
    rec = (await session.execute(stmt)).scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if rec.status != NotificationRecipientStatus.READ:
        rec.status = NotificationRecipientStatus.READ
        rec.read_at = _now()
        await session.commit()
        await session.refresh(rec)
    return MarkReadResponse(
        notification_id=notification_id,
        status=rec.status,
        read_at=rec.read_at,
    )


async def mark_all_read(session: AsyncSession, *, user: User) -> MarkAllReadResponse:
    stmt = select(NotificationRecipient).where(
        NotificationRecipient.user_id == user.id,
        NotificationRecipient.status == NotificationRecipientStatus.DELIVERED,
    )
    rows = list((await session.execute(stmt)).scalars().all())
    now = _now()
    for r in rows:
        r.status = NotificationRecipientStatus.READ
        r.read_at = now
    await session.commit()
    return MarkAllReadResponse(updated=len(rows))
