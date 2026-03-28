from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
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
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerAssignmentRow:
    return await volunteers_service.create_volunteer_assignment(
        session,
        event_id=event_id,
        body=body,
        admin_user_id=admin.id,
    )


@router.patch(
    "/{event_id}/volunteers/{assignment_id}",
    response_model=VolunteerAssignmentRow,
)
async def patch_event_volunteer_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: VolunteerAssignmentPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerAssignmentRow:
    return await volunteers_service.patch_volunteer_assignment(
        session,
        event_id=event_id,
        assignment_id=assignment_id,
        body=body,
        admin_user_id=admin.id,
    )


@router.delete(
    "/{event_id}/volunteers/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_event_volunteer_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    await volunteers_service.delete_volunteer_assignment(
        session,
        event_id=event_id,
        assignment_id=assignment_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
