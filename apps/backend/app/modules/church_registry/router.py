from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import ChurchMembershipStatus, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.church_registry import service as registry_service
from app.modules.church_registry.schemas import (
    ChurchMemberCreate,
    ChurchMemberDetailResponse,
    ChurchMemberListResponse,
    ChurchMemberPatch,
    ChurchMemberStatsResponse,
    EligibleChurchMemberListItem,
    LinkUserBody,
)

router = APIRouter(prefix="/church-members", tags=["church-members"])

_MAX_PAGE_SIZE = 100


@router.get("/stats", response_model=ChurchMemberStatsResponse)
async def member_stats(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberStatsResponse:
    return await registry_service.church_member_stats(session)


@router.get("/eligible-for-event/{event_id}", response_model=list[EligibleChurchMemberListItem])
async def eligible_for_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> list[EligibleChurchMemberListItem]:
    from app.modules.attendance.service import get_event_or_404

    event = await get_event_or_404(session, event_id)
    return await registry_service.list_eligible_church_members_for_event(session, event=event)


@router.post("/", response_model=ChurchMemberDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_church_member(
    body: ChurchMemberCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    return await registry_service.create_church_member(session, body)


@router.get("/", response_model=ChurchMemberListResponse)
async def list_church_members(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    membership_status: ChurchMembershipStatus | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_deceased: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> ChurchMemberListResponse:
    return await registry_service.list_church_members(
        session,
        search=search,
        membership_status=membership_status,
        is_active=is_active,
        is_deceased=is_deceased,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=ChurchMemberDetailResponse)
async def get_my_church_member(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> ChurchMemberDetailResponse:
    """Compatibility: resolve registry row tied to the current user, if any."""
    return await registry_service.get_my_church_member_profile(session, user=user)


@router.get("/{member_id}", response_model=ChurchMemberDetailResponse)
async def get_church_member(
    member_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    cm = await registry_service.get_church_member_or_404(session, member_id)
    return registry_service.church_member_to_detail(cm)


@router.patch("/{member_id}", response_model=ChurchMemberDetailResponse)
async def patch_church_member(
    member_id: uuid.UUID,
    body: ChurchMemberPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    cm = await registry_service.get_church_member_or_404(session, member_id)
    return await registry_service.patch_church_member(session, cm=cm, body=body)


@router.patch("/{member_id}/link-user", response_model=ChurchMemberDetailResponse)
async def link_church_member_user(
    member_id: uuid.UUID,
    body: LinkUserBody,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    """Optional admin/maintenance: attach a login to a registry row. Not part of primary product UX."""
    cm = await registry_service.get_church_member_or_404(session, member_id)
    return await registry_service.link_user_to_member(session, cm=cm, user_id=body.user_id)
