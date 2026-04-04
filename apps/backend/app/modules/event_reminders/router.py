from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
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
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventReminderRuleResponse:
    return await event_reminders_service.create_rule(session, event_id=event_id, admin=admin, body=body)


@router.patch("/{event_id}/reminders/{rule_id}", response_model=EventReminderRuleResponse)
async def patch_event_reminder(
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
    body: EventReminderRulePatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventReminderRuleResponse:
    return await event_reminders_service.update_rule(
        session,
        event_id=event_id,
        rule_id=rule_id,
        body=body,
    )


@router.delete(
    "/{event_id}/reminders/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_event_reminder(
    event_id: uuid.UUID,
    rule_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    await event_reminders_service.delete_rule(session, event_id=event_id, rule_id=rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
