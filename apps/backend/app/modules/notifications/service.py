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
    NotificationDeliveryAttemptStatus,
    NotificationRecipientStatus,
)
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.notification import Notification
from app.db.models.notification_delivery_attempt import NotificationDeliveryAttempt
from app.db.models.notification_recipient import NotificationRecipient
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.modules.auth import service as auth_service
from app.modules.events import service as events_service
from app.modules.ministries import service as ministries_service
from app.modules.notifications.phone import sms_phone_from_user_profile
from app.modules.notifications.providers.sms import send_sms_twilio
from app.modules.notifications.providers.whatsapp import send_whatsapp_twilio
from app.modules.notifications.schemas import (
    DeliveryAttemptRow,
    DeliverySummary,
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
_SMS_BODY_MAX = 1500


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sms_body_text(title: str, body: str) -> str:
    text = f"{title}\n\n{body}".strip()
    return text[:_SMS_BODY_MAX]


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


def _recipient_row_from_orm(r: NotificationRecipient) -> NotificationRecipientRow:
    attempts = sorted(r.delivery_attempts, key=lambda a: (a.channel.value, a.created_at))
    user_full_name: str | None = None
    user_email: str | None = None
    if r.user is not None:
        user_full_name = r.user.full_name
        user_email = r.user.email
    return NotificationRecipientRow(
        id=r.id,
        user_id=r.user_id,
        user_full_name=user_full_name,
        user_email=user_email,
        status=r.status,
        read_at=r.read_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
        delivery_attempts=[DeliveryAttemptRow.model_validate(a) for a in attempts],
    )


def notification_detail_response(
    n: Notification,
    *,
    delivery_summary: DeliverySummary | None = None,
) -> NotificationDetailResponse:
    recs = sorted(n.recipients, key=lambda r: r.created_at)
    return NotificationDetailResponse(
        id=n.id,
        title=n.title,
        body=n.body,
        category=n.category,
        channels=list(n.channels),
        audience_type=n.audience_type,
        related_event_id=n.related_event_id,
        related_ministry_id=n.related_ministry_id,
        created_by_user_id=n.created_by_user_id,
        created_at=n.created_at,
        updated_at=n.updated_at,
        sent_at=n.sent_at,
        delivery_summary=delivery_summary,
        recipients=[_recipient_row_from_orm(r) for r in recs],
    )


async def create_and_send_notification(
    session: AsyncSession,
    *,
    admin: User,
    body: NotificationCreateRequest,
) -> NotificationDetailResponse:
    channels_sorted = sorted(body.channels, key=lambda c: c.value)
    channel_values = [c.value for c in channels_sorted]
    in_app = NotificationChannel.IN_APP in body.channels
    sms_ch = NotificationChannel.SMS in body.channels
    wa_ch = NotificationChannel.WHATSAPP in body.channels

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

    stmt_users = (
        select(User)
        .where(User.id.in_(recipient_ids))
        .options(selectinload(User.member_profile))
    )
    users = list((await session.execute(stmt_users)).unique().scalars().all())
    users_by_id = {u.id: u for u in users}

    related_event_id: uuid.UUID | None = None
    related_ministry_id: uuid.UUID | None = None
    if body.audience_type == NotificationAudienceType.MINISTRY_MEMBERS:
        related_ministry_id = body.ministry_id
    elif body.audience_type == NotificationAudienceType.EVENT_VOLUNTEERS:
        related_event_id = body.event_id

    external_needs_phone = (sms_ch or wa_ch) and not in_app
    if external_needs_phone:
        if not any(sms_phone_from_user_profile(users_by_id[uid]) for uid in recipient_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No recipients have a phone number on their app profile for the selected external channel(s).",
            )

    if in_app:
        reachable = True
    else:
        reachable = any(sms_phone_from_user_profile(users_by_id[uid]) for uid in recipient_ids)
    if not reachable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients can be reached with the selected channels.",
        )

    now = _now()
    n = Notification(
        title=body.title,
        body=body.body,
        category=body.category,
        channels=channel_values,
        audience_type=body.audience_type,
        related_event_id=related_event_id,
        related_ministry_id=related_ministry_id,
        created_by_user_id=admin.id,
        sent_at=now,
    )
    session.add(n)
    await session.flush()

    sms_skipped_no_phone = 0
    sms_attempted = 0
    sms_sent = 0
    sms_failed = 0
    wa_skipped_no_phone = 0
    wa_attempted = 0
    wa_sent = 0
    wa_failed = 0
    sms_payload = _sms_body_text(body.title, body.body)
    wa_payload = _sms_body_text(body.title, body.body)
    pending_sms: list[tuple[NotificationDeliveryAttempt, str]] = []
    pending_wa: list[tuple[NotificationDeliveryAttempt, str]] = []

    for uid in recipient_ids:
        u = users_by_id[uid]
        rec_status = (
            NotificationRecipientStatus.DELIVERED
            if in_app
            else NotificationRecipientStatus.EXTERNAL_ONLY
        )
        rec = NotificationRecipient(
            notification_id=n.id,
            user_id=uid,
            status=rec_status,
        )
        session.add(rec)
        await session.flush()

        if in_app:
            session.add(
                NotificationDeliveryAttempt(
                    notification_recipient_id=rec.id,
                    channel=NotificationChannel.IN_APP,
                    status=NotificationDeliveryAttemptStatus.DELIVERED,
                )
            )

        if sms_ch:
            phone = sms_phone_from_user_profile(u)
            if not phone:
                sms_skipped_no_phone += 1
                session.add(
                    NotificationDeliveryAttempt(
                        notification_recipient_id=rec.id,
                        channel=NotificationChannel.SMS,
                        status=NotificationDeliveryAttemptStatus.FAILED,
                        error_detail="No phone number on app profile",
                    )
                )
            else:
                sms_attempted += 1
                att = NotificationDeliveryAttempt(
                    notification_recipient_id=rec.id,
                    channel=NotificationChannel.SMS,
                    status=NotificationDeliveryAttemptStatus.PENDING,
                )
                session.add(att)
                await session.flush()
                pending_sms.append((att, phone))

        if wa_ch:
            wa_phone = sms_phone_from_user_profile(u)
            if not wa_phone:
                wa_skipped_no_phone += 1
                session.add(
                    NotificationDeliveryAttempt(
                        notification_recipient_id=rec.id,
                        channel=NotificationChannel.WHATSAPP,
                        status=NotificationDeliveryAttemptStatus.FAILED,
                        error_detail="No phone number on app profile",
                    )
                )
            else:
                wa_attempted += 1
                wa_att = NotificationDeliveryAttempt(
                    notification_recipient_id=rec.id,
                    channel=NotificationChannel.WHATSAPP,
                    status=NotificationDeliveryAttemptStatus.PENDING,
                )
                session.add(wa_att)
                await session.flush()
                pending_wa.append((wa_att, wa_phone))

    for att, phone in pending_sms:
        result = await send_sms_twilio(to_e164=phone, body=sms_payload)
        if result.ok:
            att.status = NotificationDeliveryAttemptStatus.SENT
            att.provider_message_id = result.provider_message_id
            sms_sent += 1
        else:
            att.status = NotificationDeliveryAttemptStatus.FAILED
            att.error_detail = result.error_message
            sms_failed += 1

    for att, phone in pending_wa:
        result = await send_whatsapp_twilio(to_e164=phone, body=wa_payload)
        if result.ok:
            att.status = NotificationDeliveryAttemptStatus.SENT
            att.provider_message_id = result.provider_message_id
            wa_sent += 1
        else:
            att.status = NotificationDeliveryAttemptStatus.FAILED
            att.error_detail = result.error_message
            wa_failed += 1

    await session.commit()

    summary = DeliverySummary(
        audience_resolved_count=len(recipient_ids),
        channels=channel_values,
        in_app_recipient_count=len(recipient_ids) if in_app else 0,
        sms_skipped_no_phone=sms_skipped_no_phone,
        sms_attempted=sms_attempted,
        sms_sent=sms_sent,
        sms_failed=sms_failed,
        whatsapp_skipped_no_phone=wa_skipped_no_phone,
        whatsapp_attempted=wa_attempted,
        whatsapp_sent=wa_sent,
        whatsapp_failed=wa_failed,
    )

    stmt = (
        select(Notification)
        .where(Notification.id == n.id)
        .options(
            selectinload(Notification.recipients).selectinload(NotificationRecipient.user),
            selectinload(Notification.recipients).selectinload(
                NotificationRecipient.delivery_attempts,
            ),
        )
    )
    n2 = (await session.execute(stmt)).scalar_one()
    return notification_detail_response(n2, delivery_summary=summary)


async def _build_summary_from_notification(
    session: AsyncSession,
    n: Notification,
) -> DeliverySummary | None:
    if not n.recipients:
        return None
    channel_values = list(n.channels)
    in_app = NotificationChannel.IN_APP.value in channel_values
    stmt = (
        select(NotificationDeliveryAttempt)
        .join(NotificationRecipient)
        .where(NotificationRecipient.notification_id == n.id)
    )
    attempts = list((await session.execute(stmt)).scalars().all())
    sms_all = [a for a in attempts if a.channel == NotificationChannel.SMS]
    sms_skipped = sum(
        1
        for a in sms_all
        if a.status == NotificationDeliveryAttemptStatus.FAILED
        and (a.error_detail or "").startswith("No phone number")
    )
    sms_attempted = len(sms_all) - sms_skipped
    sms_sent = sum(
        1
        for a in sms_all
        if a.status
        in (
            NotificationDeliveryAttemptStatus.SENT,
            NotificationDeliveryAttemptStatus.DELIVERED,
        )
    )
    sms_failed = sum(
        1
        for a in sms_all
        if a.status == NotificationDeliveryAttemptStatus.FAILED
        and not (a.error_detail or "").startswith("No phone number")
    )
    wa_all = [a for a in attempts if a.channel == NotificationChannel.WHATSAPP]
    wa_skipped = sum(
        1
        for a in wa_all
        if a.status == NotificationDeliveryAttemptStatus.FAILED
        and (a.error_detail or "").startswith("No phone number")
    )
    wa_attempted = len(wa_all) - wa_skipped
    wa_sent = sum(
        1
        for a in wa_all
        if a.status
        in (
            NotificationDeliveryAttemptStatus.SENT,
            NotificationDeliveryAttemptStatus.DELIVERED,
        )
    )
    wa_failed = sum(
        1
        for a in wa_all
        if a.status == NotificationDeliveryAttemptStatus.FAILED
        and not (a.error_detail or "").startswith("No phone number")
    )
    return DeliverySummary(
        audience_resolved_count=len(n.recipients),
        channels=channel_values,
        in_app_recipient_count=len(n.recipients) if in_app else 0,
        sms_skipped_no_phone=sms_skipped,
        sms_attempted=sms_attempted,
        sms_sent=sms_sent,
        sms_failed=sms_failed,
        whatsapp_skipped_no_phone=wa_skipped,
        whatsapp_attempted=wa_attempted,
        whatsapp_sent=wa_sent,
        whatsapp_failed=wa_failed,
    )


async def list_notifications_admin(
    session: AsyncSession,
    *,
    category: NotificationCategory | None,
    related_event_id: uuid.UUID | None,
    related_ministry_id: uuid.UUID | None,
    channel: NotificationChannel | None,
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
    if channel is not None:
        count_stmt = count_stmt.where(Notification.channels.contains([channel.value]))
        list_stmt = list_stmt.where(Notification.channels.contains([channel.value]))

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
            channels=list(r.channels),
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
        .options(
            selectinload(Notification.recipients).selectinload(NotificationRecipient.user),
            selectinload(Notification.recipients).selectinload(
                NotificationRecipient.delivery_attempts,
            ),
        )
    )
    n = (await session.execute(stmt)).scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    summary = await _build_summary_from_notification(session, n)
    return notification_detail_response(n, delivery_summary=summary)


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
        .where(
            NotificationRecipient.user_id == user.id,
            NotificationRecipient.status.in_(
                (
                    NotificationRecipientStatus.DELIVERED,
                    NotificationRecipientStatus.READ,
                ),
            ),
        )
    )
    total = int((await session.execute(count_stmt)).scalar_one())

    stmt = (
        select(NotificationRecipient, Notification)
        .join(Notification, Notification.id == NotificationRecipient.notification_id)
        .where(
            NotificationRecipient.user_id == user.id,
            NotificationRecipient.status.in_(
                (
                    NotificationRecipientStatus.DELIVERED,
                    NotificationRecipientStatus.READ,
                ),
            ),
        )
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
                channels=list(n.channels),
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
    if rec.status == NotificationRecipientStatus.EXTERNAL_ONLY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not in inbox",
        )
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
