from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.ministries import service as ministries_service
from app.modules.ministries.schemas import (
    MinistryCreate,
    MinistryDetailResponse,
    MinistryListResponse,
    MinistryMemberRow,
    MinistryMembershipCreate,
    MinistryMembershipPatch,
    MinistryPatch,
    MyMinistriesResponse,
)

router = APIRouter(prefix="/ministries", tags=["ministries"])

_MAX_PAGE_SIZE = 100


@router.get("/me", response_model=MyMinistriesResponse)
async def list_my_ministries(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MyMinistriesResponse:
    items = await ministries_service.list_my_ministries(session, user)
    return MyMinistriesResponse(items=items)


@router.get("/", response_model=MinistryListResponse)
async def list_ministries(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> MinistryListResponse:
    rows, total = await ministries_service.list_ministries(
        session,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    items = [await ministries_service.ministry_to_list_item(session, m) for m in rows]
    return MinistryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=MinistryDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ministry(
    body: MinistryCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryDetailResponse:
    m = await ministries_service.create_ministry(session, body)
    return await ministries_service.ministry_detail_for_admin(session, m)


@router.get("/{ministry_id}", response_model=MinistryDetailResponse)
async def get_ministry(
    ministry_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MinistryDetailResponse:
    m = await ministries_service.get_ministry_or_404(session, ministry_id)
    if user.role == UserRole.ADMIN:
        return await ministries_service.ministry_detail_for_admin(session, m)
    return await ministries_service.ministry_detail_for_member(session, m, user)


@router.patch("/{ministry_id}", response_model=MinistryDetailResponse)
async def patch_ministry(
    ministry_id: uuid.UUID,
    body: MinistryPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryDetailResponse:
    m = await ministries_service.get_ministry_or_404(session, ministry_id)
    updated = await ministries_service.patch_ministry(session, m, body)
    return await ministries_service.ministry_detail_for_admin(session, updated)


@router.post(
    "/{ministry_id}/members",
    response_model=MinistryMemberRow,
    status_code=status.HTTP_201_CREATED,
)
async def add_ministry_member(
    ministry_id: uuid.UUID,
    body: MinistryMembershipCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryMemberRow:
    m = await ministries_service.get_ministry_or_404(session, ministry_id)
    mm = await ministries_service.add_or_reactivate_membership(session, m, body)
    if mm.church_member is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Membership church member not loaded",
        )
    return ministries_service.membership_to_row(mm)


@router.patch(
    "/{ministry_id}/members/{church_member_id}",
    response_model=MinistryMemberRow,
)
async def patch_ministry_member(
    ministry_id: uuid.UUID,
    church_member_id: uuid.UUID,
    body: MinistryMembershipPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryMemberRow:
    await ministries_service.get_ministry_or_404(session, ministry_id)
    mm = await ministries_service.patch_membership(session, ministry_id, church_member_id, body)
    if mm.church_member is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Membership church member not loaded",
        )
    return ministries_service.membership_to_row(mm)


@router.delete(
    "/{ministry_id}/members/{church_member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_ministry_member(
    ministry_id: uuid.UUID,
    church_member_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    await ministries_service.get_ministry_or_404(session, ministry_id)
    await ministries_service.deactivate_membership(session, ministry_id, church_member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)