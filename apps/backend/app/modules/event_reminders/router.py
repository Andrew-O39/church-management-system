from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.db.models.event_reminder_rule import EventReminderRule
from app.modules.auth.deps import require_roles
from app.modules.audit_logs.actions import (
    EVENT_REMINDER_RULE_CREATE,
    EVENT_REMINDER_RULE_DELETE,
    EVENT_REMINDER_RULE_UPDATE,
)
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
from app.modules.events import service as events_service
from app.modules.event_reminders import service as event_reminders_service
from app.modules.event_reminders.schemas import (
    EventReminderRuleCreate,
    EventReminderRuleListResponse,
    EventReminderRulePatch,
    EventReminderRuleResponse,
)

router = APIRouter(prefix="/events", tags=["event-reminders"])


@router.get("/{event_id}/reminders", response_model=EventReminderRuleListResponse)
async def list_event_reminders(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventReminderRuleListResponse:
    return await event_reminders_service.list_rules_for_event(session, event_id=event_id)


@router.post(
    "/{event_id}/reminders",
    response_model=EventReminderRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_reminder(
    event_id: uuid.UUID,
    body: EventReminderRuleCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventReminderRuleResponse:
    out = await event_reminders_service.create_rule(session, event_id=event_id, admin=admin, body=body)
    event = await events_service.get_event_or_404(session, event_id)
    await record_audit_event(
        action=EVENT_REMINDER_RULE_CREATE,
        summary=f"Event reminder rule created for {event.title}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event_reminder_rule",
        target_id=str(out.id),
        metadata={
            "event_title": event.title,
            "offset_minutes_before": out.offset_minutes_before,
            "audience_type": out.audience_type.value,
        },
        ip_address=client_ip_from_request(request),
    )
    return out


@router.patch("/{event_id}/reminders/{rule_id}", response_model=EventReminderRuleResponse)
async def patch_event_reminder(
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
    body: EventReminderRulePatch,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventReminderRuleResponse:
    out = await event_reminders_service.update_rule(
        session,
        event_id=event_id,
        rule_id=rule_id,
        body=body,
    )
    event = await events_service.get_event_or_404(session, event_id)
    await record_audit_event(
        action=EVENT_REMINDER_RULE_UPDATE,
        summary=f"Event reminder rule updated for {event.title}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event_reminder_rule",
        target_id=str(out.id),
        metadata={"fields_changed": sorted(body.model_dump(exclude_unset=True).keys())},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.delete(
    "/{event_id}/reminders/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_event_reminder(
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    event = await events_service.get_event_or_404(session, event_id)
    rule = await session.get(EventReminderRule, rule_id)
    if rule is None or rule.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder rule not found")
    await record_audit_event(
        action=EVENT_REMINDER_RULE_DELETE,
        summary=f"Event reminder rule deleted for {event.title}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="event_reminder_rule",
        target_id=str(rule_id),
        metadata={
            "event_title": event.title,
            "offset_minutes_before": rule.offset_minutes_before,
        },
        ip_address=client_ip_from_request(request),
    )
    await event_reminders_service.delete_rule(session, event_id=event_id, rule_id=rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
