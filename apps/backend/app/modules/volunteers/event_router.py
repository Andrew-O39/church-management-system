from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.audit_logs.actions import (
    VOLUNTEER_ASSIGNMENT_CREATE,
    VOLUNTEER_ASSIGNMENT_DELETE,
    VOLUNTEER_ASSIGNMENT_UPDATE,
)
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
from app.modules.events import service as events_service
from app.modules.volunteers import service as volunteers_service
from app.modules.volunteers.schemas import (
    EventVolunteerListResponse,
    MyEventVolunteerAssignmentsResponse,
    VolunteerAssignmentCreate,
    VolunteerAssignmentPatch,
    VolunteerAssignmentRow,
)

router = APIRouter(prefix="/events", tags=["volunteers"])


@router.get(
    "/{event_id}/volunteers/me",
    response_model=MyEventVolunteerAssignmentsResponse,
)
async def list_my_event_volunteer_assignments(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MyEventVolunteerAssignmentsResponse:
    return await volunteers_service.list_my_event_volunteer_assignments(
        session,
        event_id=event_id,
        user=user,
    )


@router.get(
    "/{event_id}/volunteers",
    response_model=EventVolunteerListResponse,
)
async def list_event_volunteers(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> EventVolunteerListResponse:
    return await volunteers_service.list_event_volunteers_admin(session, event_id=event_id)


@router.post(
    "/{event_id}/volunteers",
    response_model=VolunteerAssignmentRow,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_volunteer_assignment(
    event_id: uuid.UUID,
    body: VolunteerAssignmentCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerAssignmentRow:
    event = await events_service.get_event_or_404(session, event_id)
    out = await volunteers_service.create_volunteer_assignment(
        session,
        event_id=event_id,
        body=body,
        admin_user_id=admin.id,
    )
    who = out.member_full_name or out.user_full_name or "Volunteer"
    await record_audit_event(
        action=VOLUNTEER_ASSIGNMENT_CREATE,
        summary=f"Volunteer assigned: {event.title} — {who} ({out.role_name})",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="volunteer_assignment",
        target_id=str(out.id),
        metadata={"event_title": event.title, "role_name": out.role_name},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.patch(
    "/{event_id}/volunteers/{assignment_id}",
    response_model=VolunteerAssignmentRow,
)
async def patch_event_volunteer_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: VolunteerAssignmentPatch,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerAssignmentRow:
    event = await events_service.get_event_or_404(session, event_id)
    out = await volunteers_service.patch_volunteer_assignment(
        session,
        event_id=event_id,
        assignment_id=assignment_id,
        body=body,
        admin_user_id=admin.id,
    )
    who = out.member_full_name or out.user_full_name or "Volunteer"
    await record_audit_event(
        action=VOLUNTEER_ASSIGNMENT_UPDATE,
        summary=f"Volunteer assignment updated: {event.title} — {who}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="volunteer_assignment",
        target_id=str(out.id),
        metadata={"fields_changed": sorted(body.model_dump(exclude_unset=True).keys())},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.delete(
    "/{event_id}/volunteers/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_event_volunteer_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    event = await events_service.get_event_or_404(session, event_id)
    va = await volunteers_service.get_assignment_for_event_or_404(
        session,
        event_id=event_id,
        assignment_id=assignment_id,
    )
    who = va.volunteer_user.full_name if va.volunteer_user else "Volunteer"
    role_name = va.role.name if va.role else "Role"
    await record_audit_event(
        action=VOLUNTEER_ASSIGNMENT_DELETE,
        summary=f"Volunteer assignment removed: {event.title} — {who} ({role_name})",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="volunteer_assignment",
        target_id=str(assignment_id),
        metadata={"event_title": event.title},
        ip_address=client_ip_from_request(request),
    )
    await volunteers_service.delete_volunteer_assignment(
        session,
        event_id=event_id,
        assignment_id=assignment_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
