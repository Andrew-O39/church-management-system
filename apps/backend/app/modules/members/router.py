from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.members import service as members_service
from app.modules.audit_logs.actions import (
    APP_USER_ADMIN_DEMOTED,
    APP_USER_ADMIN_PROMOTED,
    APP_USER_ADMIN_UPDATE,
    APP_USER_DEACTIVATED,
    APP_USER_REACTIVATED,
)
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
from app.modules.members.schemas import (
    MemberAdminPatch,
    MemberDetailResponse,
    MemberListItem,
    MemberListResponse,
    MemberProfileOut,
    MemberSelfPatch,
)

router = APIRouter(prefix="/members", tags=["members"])

_MAX_PAGE_SIZE = 100


def _audit_action_for_member_change(
    *,
    old_role: UserRole,
    old_active: bool,
    loaded: User,
) -> tuple[str, str]:
    """Return (action, summary) for app-user admin edits."""
    if old_role != loaded.role:
        if loaded.role == UserRole.ADMIN and old_role != UserRole.ADMIN:
            return (
                APP_USER_ADMIN_PROMOTED,
                f"Granted administrator access: {loaded.full_name}",
            )
        if old_role == UserRole.ADMIN and loaded.role != UserRole.ADMIN:
            return (
                APP_USER_ADMIN_DEMOTED,
                f"Removed administrator access: {loaded.full_name}",
            )
    if old_active and not loaded.is_active:
        return APP_USER_DEACTIVATED, f"Deactivated app user: {loaded.full_name}"
    if not old_active and loaded.is_active:
        return APP_USER_REACTIVATED, f"Reactivated app user: {loaded.full_name}"
    return APP_USER_ADMIN_UPDATE, f"App user updated: {loaded.full_name}"


def _to_list_item(user: User) -> MemberListItem:
    profile = user.member_profile
    return MemberListItem(
        member_id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
        phone_number=profile.phone_number if profile else None,
        contact_email=profile.contact_email if profile else None,
        join_date=profile.join_date if profile else None,
        preferred_channel=profile.preferred_channel if profile else None,
    )


def _to_detail(user: User) -> MemberDetailResponse:
    profile = user.member_profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )
    return MemberDetailResponse(
        member_id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        profile=MemberProfileOut.model_validate(profile),
    )


@router.get("/", response_model=MemberListResponse)
async def list_members(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> MemberListResponse:
    users, total = await members_service.list_members(
        session,
        search=search,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return MemberListResponse(
        items=[_to_list_item(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me/profile", response_model=MemberDetailResponse)
async def get_my_profile(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MemberDetailResponse:
    loaded = await members_service.get_user_with_profile(session, user.id)
    if loaded is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )
    return _to_detail(loaded)


@router.patch("/me/profile", response_model=MemberDetailResponse)
async def patch_my_profile(
    body: MemberSelfPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> MemberDetailResponse:
    loaded = await members_service.get_user_with_profile(session, user.id)
    if loaded is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )
    updated = await members_service.apply_self_patch(session, user=loaded, patch=body)
    reloaded = await members_service.get_user_with_profile(session, updated.id)
    if reloaded is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found",
        )
    return _to_detail(reloaded)


@router.get("/{member_id}", response_model=MemberDetailResponse)
async def get_member(
    member_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MemberDetailResponse:
    user = await members_service.get_user_with_profile(session, member_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return _to_detail(user)


@router.patch("/{member_id}", response_model=MemberDetailResponse)
async def patch_member(
    member_id: uuid.UUID,
    body: MemberAdminPatch,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> MemberDetailResponse:
    target = await members_service.get_user_with_profile(session, member_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    old_role = target.role
    old_active = target.is_active
    updated = await members_service.apply_admin_patch(
        session,
        target=target,
        patch=body,
        acting_admin_id=admin.id,
    )
    loaded = await members_service.get_user_with_profile(session, updated.id)
    if loaded is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    data = body.model_dump(exclude_unset=True)
    meta: dict = {"fields_changed": sorted(data.keys())}
    if data.get("role") is not None:
        meta["previous_role"] = str(old_role)
        meta["new_role"] = str(loaded.role)
    if data.get("is_active") is not None:
        meta["previous_active"] = old_active
        meta["is_active"] = bool(loaded.is_active)
    audit_action, audit_summary = _audit_action_for_member_change(
        old_role=old_role,
        old_active=old_active,
        loaded=loaded,
    )
    await record_audit_event(
        action=audit_action,
        summary=audit_summary,
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="user",
        target_id=str(loaded.id),
        metadata=meta,
        ip_address=client_ip_from_request(request),
    )
    return _to_detail(loaded)
