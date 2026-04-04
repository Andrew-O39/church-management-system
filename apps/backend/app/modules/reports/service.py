from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.church_event import ChurchEvent
from app.db.models.enums import (
    NotificationChannel,
    NotificationDeliveryAttemptStatus,
    NotificationRecipientStatus,
)
from app.db.models.event_attendance import EventAttendance
from app.db.models.ministry_group import MinistryGroup
from app.db.models.notification import Notification
from app.db.models.notification_delivery_attempt import NotificationDeliveryAttempt
from app.db.models.notification_recipient import NotificationRecipient
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.modules.reports.schemas import (
    AttendanceEventRow,
    AttendanceReportResponse,
    DashboardSummaryResponse,
    NotificationInsightsResponse,
    VolunteerLeaderRow,
    VolunteerReportResponse,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_dashboard_summary(session: AsyncSession) -> DashboardSummaryResponse:
    now = _utcnow()
    week_end = now + timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    total_users = await session.scalar(select(func.count()).select_from(User)) or 0

    # Active users: distinct app users with any operational touch in the last 30 days.
    q_att = select(EventAttendance.user_id.label("uid")).where(EventAttendance.updated_at >= cutoff_30d)
    q_vol = select(VolunteerAssignment.user_id.label("uid")).where(
        VolunteerAssignment.updated_at >= cutoff_30d
    )
    q_nr = select(NotificationRecipient.user_id.label("uid")).where(
        or_(
            NotificationRecipient.created_at >= cutoff_30d,
            NotificationRecipient.updated_at >= cutoff_30d,
        )
    )
    union_sub = union_all(q_att, q_vol, q_nr).subquery()
    distinct_users = select(union_sub.c.uid).distinct().subquery()
    active_users_last_30_days = await session.scalar(
        select(func.count()).select_from(distinct_users)
    ) or 0

    total_ministries = await session.scalar(select(func.count()).select_from(MinistryGroup)) or 0
    active_ministries = await session.scalar(
        select(func.count()).select_from(MinistryGroup).where(MinistryGroup.is_active.is_(True))
    ) or 0

    upcoming_events_count = await session.scalar(
        select(func.count())
        .select_from(ChurchEvent)
        .where(
            ChurchEvent.is_active.is_(True),
            ChurchEvent.start_at > now,
        )
    ) or 0

    events_this_week = await session.scalar(
        select(func.count())
        .select_from(ChurchEvent)
        .where(
            ChurchEvent.is_active.is_(True),
            ChurchEvent.start_at >= now,
            ChurchEvent.start_at <= week_end,
        )
    ) or 0

    volunteers_assigned_upcoming = await session.scalar(
        select(func.count(VolunteerAssignment.id))
        .select_from(VolunteerAssignment)
        .join(ChurchEvent, VolunteerAssignment.event_id == ChurchEvent.id)
        .where(
            ChurchEvent.is_active.is_(True),
            ChurchEvent.start_at > now,
        )
    ) or 0

    unread_notifications_total = await session.scalar(
        select(func.count())
        .select_from(NotificationRecipient)
        .where(NotificationRecipient.status == NotificationRecipientStatus.DELIVERED)
    ) or 0

    return DashboardSummaryResponse(
        total_users=int(total_users),
        active_users_last_30_days=int(active_users_last_30_days),
        total_ministries=int(total_ministries),
        active_ministries=int(active_ministries),
        upcoming_events_count=int(upcoming_events_count),
        events_this_week=int(events_this_week),
        volunteers_assigned_upcoming=int(volunteers_assigned_upcoming),
        unread_notifications_total=int(unread_notifications_total),
    )


async def get_attendance_report(
    session: AsyncSession,
    *,
    limit: int = 50,
) -> AttendanceReportResponse:
    stmt = (
        select(
            ChurchEvent.id.label("event_id"),
            ChurchEvent.title.label("event_title"),
            ChurchEvent.start_at.label("start_at"),
            func.count(EventAttendance.id).label("attendance_count"),
        )
        .join(EventAttendance, EventAttendance.event_id == ChurchEvent.id)
        .group_by(ChurchEvent.id, ChurchEvent.title, ChurchEvent.start_at)
        .order_by(ChurchEvent.start_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    items = [
        AttendanceEventRow(
            event_id=r.event_id,
            event_title=r.event_title,
            start_at=r.start_at,
            attendance_count=int(r.attendance_count),
        )
        for r in rows
    ]
    return AttendanceReportResponse(items=items)


async def get_volunteer_report(
    session: AsyncSession,
    *,
    limit: int = 20,
) -> VolunteerReportResponse:
    assignment_cnt = func.count(VolunteerAssignment.id)
    stmt = (
        select(
            User.id.label("user_id"),
            User.full_name.label("full_name"),
            assignment_cnt.label("assignments_count"),
        )
        .join(VolunteerAssignment, VolunteerAssignment.user_id == User.id)
        .group_by(User.id, User.full_name)
        .order_by(assignment_cnt.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    items = [
        VolunteerLeaderRow(
            user_id=r.user_id,
            full_name=r.full_name,
            assignments_count=int(r.assignments_count),
        )
        for r in rows
    ]
    return VolunteerReportResponse(items=items)


async def get_notification_insights(session: AsyncSession) -> NotificationInsightsResponse:
    total_notifications_sent = await session.scalar(
        select(func.count()).select_from(Notification).where(Notification.sent_at.isnot(None))
    ) or 0

    total_recipients = await session.scalar(select(func.count()).select_from(NotificationRecipient)) or 0

    in_app_delivered = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(
            NotificationDeliveryAttempt.channel == NotificationChannel.IN_APP,
            NotificationDeliveryAttempt.status.in_(
                (
                    NotificationDeliveryAttemptStatus.SENT,
                    NotificationDeliveryAttemptStatus.DELIVERED,
                )
            ),
        )
    ) or 0

    in_app_failed = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(
            NotificationDeliveryAttempt.channel == NotificationChannel.IN_APP,
            NotificationDeliveryAttempt.status == NotificationDeliveryAttemptStatus.FAILED,
        )
    ) or 0

    sms_attempted = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(NotificationDeliveryAttempt.channel == NotificationChannel.SMS)
    ) or 0

    sms_failed = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(
            NotificationDeliveryAttempt.channel == NotificationChannel.SMS,
            NotificationDeliveryAttempt.status == NotificationDeliveryAttemptStatus.FAILED,
        )
    ) or 0

    whatsapp_attempted = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(NotificationDeliveryAttempt.channel == NotificationChannel.WHATSAPP)
    ) or 0

    whatsapp_failed = await session.scalar(
        select(func.count())
        .select_from(NotificationDeliveryAttempt)
        .where(
            NotificationDeliveryAttempt.channel == NotificationChannel.WHATSAPP,
            NotificationDeliveryAttempt.status == NotificationDeliveryAttemptStatus.FAILED,
        )
    ) or 0

    return NotificationInsightsResponse(
        total_notifications_sent=int(total_notifications_sent),
        total_recipients=int(total_recipients),
        in_app_delivered=int(in_app_delivered),
        in_app_failed=int(in_app_failed),
        sms_attempted=int(sms_attempted),
        sms_failed=int(sms_failed),
        whatsapp_attempted=int(whatsapp_attempted),
        whatsapp_failed=int(whatsapp_failed),
    )
