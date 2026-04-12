from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.audit_logs.actions import MINISTRIES_CREATE, MINISTRIES_UPDATE
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryDetailResponse:
    m = await ministries_service.create_ministry(session, body)
    out = await ministries_service.ministry_detail_for_admin(session, m)
    await record_audit_event(
        action=MINISTRIES_CREATE,
        summary=f"Ministry created: {out.name}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="ministry",
        target_id=str(out.id),
        metadata={"name": out.name},
        ip_address=client_ip_from_request(request),
    )
    return out


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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryDetailResponse:
    m = await ministries_service.get_ministry_or_404(session, ministry_id)
    updated = await ministries_service.patch_ministry(session, m, body)
    out = await ministries_service.ministry_detail_for_admin(session, updated)
    await record_audit_event(
        action=MINISTRIES_UPDATE,
        summary=f"Ministry updated: {out.name}",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="ministry",
        target_id=str(out.id),
        metadata={"fields_changed": sorted(body.model_dump(exclude_unset=True).keys())},
        ip_address=client_ip_from_request(request),
    )
    return out


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
    if mm.user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Membership user not loaded",
        )
    return ministries_service.membership_to_row(mm)


@router.patch(
    "/{ministry_id}/members/{user_id}",
    response_model=MinistryMemberRow,
)
async def patch_ministry_member(
    ministry_id: uuid.UUID,
    user_id: uuid.UUID,
    body: MinistryMembershipPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MinistryMemberRow:
    await ministries_service.get_ministry_or_404(session, ministry_id)
    mm = await ministries_service.patch_membership(session, ministry_id, user_id, body)
    if mm.user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Membership user not loaded",
        )
    return ministries_service.membership_to_row(mm)


@router.delete(
    "/{ministry_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_ministry_member(
    ministry_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> Response:
    await ministries_service.get_ministry_or_404(session, ministry_id)
    await ministries_service.deactivate_membership(session, ministry_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)