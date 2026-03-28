from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.volunteers import service as volunteers_service
from app.modules.volunteers.schemas import (
    MyVolunteerAssignmentsResponse,
    VolunteerRoleCreate,
    VolunteerRoleDetailResponse,
    VolunteerRoleListResponse,
    VolunteerRolePatch,
)

router = APIRouter(prefix="/volunteers", tags=["volunteers"])

_MAX_PAGE_SIZE = 100


@router.get("/me", response_model=MyVolunteerAssignmentsResponse)
async def list_my_volunteer_assignments(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MyVolunteerAssignmentsResponse:
    return await volunteers_service.list_my_volunteer_assignments(session, user=user)


@router.get("/roles", response_model=VolunteerRoleListResponse)
async def list_volunteer_roles(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    is_active: bool | None = Query(default=None),
    ministry_id: uuid.UUID | None = Query(default=None),
    for_event_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> VolunteerRoleListResponse:
    return await volunteers_service.list_volunteer_roles_admin(
        session,
        search=search,
        is_active=is_active,
        ministry_id=ministry_id,
        for_event_id=for_event_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/roles",
    response_model=VolunteerRoleDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_volunteer_role(
    body: VolunteerRoleCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerRoleDetailResponse:
    return await volunteers_service.create_volunteer_role(session, body=body)


@router.get("/roles/{role_id}", response_model=VolunteerRoleDetailResponse)
async def get_volunteer_role(
    role_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerRoleDetailResponse:
    role = await volunteers_service.get_volunteer_role_or_404(session, role_id)
    return volunteers_service.volunteer_role_to_detail(role)


@router.patch("/roles/{role_id}", response_model=VolunteerRoleDetailResponse)
async def patch_volunteer_role(
    role_id: uuid.UUID,
    body: VolunteerRolePatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> VolunteerRoleDetailResponse:
    role = await volunteers_service.get_volunteer_role_or_404(session, role_id)
    return await volunteers_service.patch_volunteer_role(session, role=role, body=body)
