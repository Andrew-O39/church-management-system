from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.settings import settings
from app.db.models.church_event import ChurchEvent
from app.db.models.enums import (
    EventReminderAudienceType,
    EventReminderRunStatus,
    NotificationAudienceType,
    NotificationCategory,
    NotificationChannel,
)
from app.db.models.event_reminder_rule import EventReminderRule
from app.db.models.event_reminder_run import EventReminderRun
from app.db.models.user import User
from app.modules.auth import service as auth_service
from app.modules.events import service as events_service
from app.modules.notifications import service as notifications_service
from app.modules.notifications.schemas import NotificationCreateRequest
from app.modules.event_reminders.schemas import (
    EventReminderRuleCreate,
    EventReminderRuleListResponse,
    EventReminderRulePatch,
    EventReminderRuleResponse,
    RunDueRemindersResponse,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    """Query params may be naive; DB datetimes are tz-aware — normalize for comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _offset_human_label(minutes: int) -> str:
    if minutes <= 0:
        return f"{minutes} minutes"
    if minutes % 10080 == 0 and minutes > 0:
        w = minutes // 10080
        return f"{w} week" + ("s" if w != 1 else "")
    if minutes % 1440 == 0 and minutes > 0:
        d = minutes // 1440
        return f"{d} day" + ("s" if d != 1 else "")
    if minutes % 60 == 0 and minutes > 0:
        h = minutes // 60
        return f"{h} hour" + ("s" if h != 1 else "")
    return f"{minutes} minutes"


def _default_title_body(event: ChurchEvent, offset_minutes: int) -> tuple[str, str]:
    label = _offset_human_label(offset_minutes)
    title = f"Reminder: {event.title} starts in {label}"
    body = (
        f"{event.title} begins at {event.start_at.isoformat()}. "
        f"Location: {event.location}."
    )
    return title, body


def _notification_request_for_rule(
    rule: EventReminderRule,
    event: ChurchEvent,
) -> NotificationCreateRequest:
    title, body = _default_title_body(event, rule.offset_minutes_before)
    if rule.title_override:
        title = rule.title_override
    if rule.body_override:
        body = rule.body_override

    try:
        chans = [NotificationChannel(c) for c in rule.channels]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel in reminder rule: {e}",
        ) from e

    if rule.audience_type == EventReminderAudienceType.EVENT_VOLUNTEERS:
        return NotificationCreateRequest(
            title=title,
            body=body,
            category=NotificationCategory.EVENT,
            channels=chans,
            audience_type=NotificationAudienceType.EVENT_VOLUNTEERS,
            event_id=event.id,
        )

    if event.ministry_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ministry_members reminders require the event to be linked to a ministry",
        )
    return NotificationCreateRequest(
        title=title,
        body=body,
        category=NotificationCategory.MINISTRY,
        channels=chans,
        audience_type=NotificationAudienceType.MINISTRY_MEMBERS,
        ministry_id=event.ministry_id,
    )


def _rule_to_response(rule: EventReminderRule) -> EventReminderRuleResponse:
    return EventReminderRuleResponse(
        id=rule.id,
        event_id=rule.event_id,
        title_override=rule.title_override,
        body_override=rule.body_override,
        audience_type=rule.audience_type,
        channels=list(rule.channels),
        offset_minutes_before=rule.offset_minutes_before,
        is_active=rule.is_active,
        last_run_at=rule.last_run_at,
        created_by_user_id=rule.created_by_user_id,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


async def list_rules_for_event(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
) -> EventReminderRuleListResponse:
    await events_service.get_event_or_404(session, event_id)
    stmt = (
        select(EventReminderRule)
        .where(EventReminderRule.event_id == event_id)
        .order_by(EventReminderRule.offset_minutes_before.asc(), EventReminderRule.created_at.asc())
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return EventReminderRuleListResponse(items=[_rule_to_response(r) for r in rows])


async def create_rule(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    admin: User,
    body: EventReminderRuleCreate,
) -> EventReminderRuleResponse:
    event = await events_service.get_event_or_404(session, event_id)
    if body.audience_type == EventReminderAudienceType.MINISTRY_MEMBERS and event.ministry_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ministry_members audience requires the event to have a ministry",
        )
    channels_sorted = sorted(body.channels, key=lambda c: c.value)
    channel_values = [c.value for c in channels_sorted]
    rule = EventReminderRule(
        event_id=event_id,
        title_override=body.title_override,
        body_override=body.body_override,
        audience_type=body.audience_type,
        channels=channel_values,
        offset_minutes_before=body.offset_minutes_before,
        is_active=body.is_active,
        created_by_user_id=admin.id,
    )
    session.add(rule)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A reminder with this offset and audience already exists for this event",
        ) from e
    await session.refresh(rule)
    return _rule_to_response(rule)


async def update_rule(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
    body: EventReminderRulePatch,
) -> EventReminderRuleResponse:
    event = await events_service.get_event_or_404(session, event_id)
    rule = await session.get(EventReminderRule, rule_id)
    if rule is None or rule.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder rule not found")

    if body.audience_type is not None:
        rule.audience_type = body.audience_type
    if body.channels is not None:
        channels_sorted = sorted(body.channels, key=lambda c: c.value)
        rule.channels = [c.value for c in channels_sorted]
    if body.offset_minutes_before is not None:
        rule.offset_minutes_before = body.offset_minutes_before
    if body.title_override is not None:
        rule.title_override = body.title_override
    if body.body_override is not None:
        rule.body_override = body.body_override
    if body.is_active is not None:
        rule.is_active = body.is_active

    eff_audience = rule.audience_type
    if eff_audience == EventReminderAudienceType.MINISTRY_MEMBERS and event.ministry_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ministry_members audience requires the event to have a ministry",
        )

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A reminder with this offset and audience already exists for this event",
        ) from e
    await session.refresh(rule)
    return _rule_to_response(rule)


async def delete_rule(
    session: AsyncSession,
    *,
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
) -> None:
    await events_service.get_event_or_404(session, event_id)
    rule = await session.get(EventReminderRule, rule_id)
    if rule is None or rule.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder rule not found")
    await session.delete(rule)
    await session.commit()


async def run_due_reminders(
    session: AsyncSession,
    *,
    now: datetime | None = None,
) -> RunDueRemindersResponse:
    """Evaluate active rules against event start times; send notifications via existing pipeline.

    Idempotency: a successful send is recorded as ``EventReminderRun`` with status SUCCESS for
    ``(reminder_rule_id, scheduled_for)`` where ``scheduled_for = event.start_at - offset``.
    Concurrent workers: the first INSERT of a pending run wins; others hit IntegrityError and skip.
    """
    now = _ensure_utc(now) if now is not None else _now()
    skipped_not_due = 0
    skipped_already_sent = 0
    skipped_invalid = 0
    reminders_sent = 0
    failed = 0
    failure_messages: list[str] = []

    stmt = (
        select(EventReminderRule)
        .join(ChurchEvent, ChurchEvent.id == EventReminderRule.event_id)
        .where(
            EventReminderRule.is_active.is_(True),
            ChurchEvent.is_active.is_(True),
            ChurchEvent.start_at > now,
        )
        .options(selectinload(EventReminderRule.event))
        .limit(settings.REMINDER_JOB_BATCH_SIZE)
    )
    rules = list((await session.execute(stmt)).scalars().unique().all())

    due: list[tuple[EventReminderRule, ChurchEvent, datetime]] = []
    for rule in rules:
        ev = rule.event
        start_at = _ensure_utc(ev.start_at)
        scheduled_for = _ensure_utc(start_at - timedelta(minutes=rule.offset_minutes_before))
        if scheduled_for > now:
            skipped_not_due += 1
            continue
        if now >= start_at:
            skipped_not_due += 1
            continue
        due.append((rule, ev, scheduled_for))

    rules_considered = len(due)

    for rule, event, scheduled_for in due:
        try:
            req = _notification_request_for_rule(rule, event)
        except HTTPException as e:
            skipped_invalid += 1
            detail = e.detail
            if isinstance(detail, str):
                failure_messages.append(f"rule {rule.id}: {detail}")
            else:
                failure_messages.append(f"rule {rule.id}: invalid configuration")
            continue

        existing_success = await session.scalar(
            select(EventReminderRun).where(
                EventReminderRun.reminder_rule_id == rule.id,
                EventReminderRun.scheduled_for == scheduled_for,
                EventReminderRun.status == EventReminderRunStatus.SUCCESS,
            )
        )
        if existing_success is not None:
            skipped_already_sent += 1
            continue

        admin = await auth_service.get_user_by_id(session, rule.created_by_user_id)
        if admin is None or not admin.is_active:
            skipped_invalid += 1
            failure_messages.append(f"rule {rule.id}: created_by user missing or inactive")
            continue

        run_row = EventReminderRun(
            reminder_rule_id=rule.id,
            event_id=event.id,
            scheduled_for=scheduled_for,
            status=EventReminderRunStatus.PENDING,
        )
        session.add(run_row)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            skipped_already_sent += 1
            continue

        try:
            detail = await notifications_service.create_and_send_notification(
                session,
                admin=admin,
                body=req,
                commit=False,
            )
        except HTTPException as e:
            await session.rollback()
            failed += 1
            msg = e.detail if isinstance(e.detail, str) else str(e.detail)
            failure_messages.append(f"rule {rule.id}: {msg}")
            continue

        run_row.status = EventReminderRunStatus.SUCCESS
        run_row.executed_at = _now()
        run_row.created_notification_id = detail.id
        rule.last_run_at = _now()
        await session.commit()
        reminders_sent += 1

    return RunDueRemindersResponse(
        rules_considered=rules_considered,
        reminders_sent=reminders_sent,
        skipped_not_due=skipped_not_due,
        skipped_already_sent=skipped_already_sent,
        skipped_invalid=skipped_invalid,
        failed=failed,
        failure_messages=failure_messages[:50],
    )
