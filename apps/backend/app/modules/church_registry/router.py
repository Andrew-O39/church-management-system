from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import ChurchMembershipStatus, Gender, RegistryAgeGroup, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.church_registry import service as registry_service
from app.modules.audit_logs.actions import (
    REGISTRY_MEMBER_CREATE,
    REGISTRY_MEMBER_LINK_USER,
    REGISTRY_MEMBER_UPDATE,
)
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event
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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    out = await registry_service.create_church_member(session, body)
    await record_audit_event(
        action=REGISTRY_MEMBER_CREATE,
        summary=f"Parish registry record created ({out.full_name})",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="church_member",
        target_id=str(out.id),
        metadata={"registration_number": out.registration_number},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.get("/", response_model=ChurchMemberListResponse)
async def list_church_members(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    search: str | None = Query(default=None, max_length=200),
    membership_status: ChurchMembershipStatus | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_deceased: bool | None = Query(default=None),
    gender: Gender | None = Query(default=None),
    is_baptized: bool | None = Query(default=None),
    is_confirmed: bool | None = Query(default=None),
    is_communicant: bool | None = Query(default=None),
    is_married: bool | None = Query(default=None),
    age_group: RegistryAgeGroup | None = Query(default=None),
    joined_from: date | None = Query(default=None),
    joined_to: date | None = Query(default=None),
    deceased_from: date | None = Query(default=None),
    deceased_to: date | None = Query(default=None),
    baptism_date_from: date | None = Query(default=None),
    baptism_date_to: date | None = Query(default=None),
    confirmation_date_from: date | None = Query(default=None),
    confirmation_date_to: date | None = Query(default=None),
    first_communion_date_from: date | None = Query(default=None),
    first_communion_date_to: date | None = Query(default=None),
    marriage_date_from: date | None = Query(default=None),
    marriage_date_to: date | None = Query(default=None),
    date_of_birth_from: date | None = Query(default=None),
    date_of_birth_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
) -> ChurchMemberListResponse:
    return await registry_service.list_church_members(
        session,
        search=search,
        membership_status=membership_status,
        is_active=is_active,
        is_deceased=is_deceased,
        gender=gender,
        is_baptized=is_baptized,
        is_confirmed=is_confirmed,
        is_communicant=is_communicant,
        is_married=is_married,
        age_group=age_group,
        joined_from=joined_from,
        joined_to=joined_to,
        deceased_from=deceased_from,
        deceased_to=deceased_to,
        baptism_date_from=baptism_date_from,
        baptism_date_to=baptism_date_to,
        confirmation_date_from=confirmation_date_from,
        confirmation_date_to=confirmation_date_to,
        first_communion_date_from=first_communion_date_from,
        first_communion_date_to=first_communion_date_to,
        marriage_date_from=marriage_date_from,
        marriage_date_to=marriage_date_to,
        date_of_birth_from=date_of_birth_from,
        date_of_birth_to=date_of_birth_to,
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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    cm = await registry_service.get_church_member_or_404(session, member_id)
    out = await registry_service.patch_church_member(session, cm=cm, body=body)
    fields = sorted(body.model_dump(exclude_unset=True).keys())
    await record_audit_event(
        action=REGISTRY_MEMBER_UPDATE,
        summary=f"Parish registry record updated ({out.full_name})",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="church_member",
        target_id=str(out.id),
        metadata={"fields_changed": fields},
        ip_address=client_ip_from_request(request),
    )
    return out


@router.patch("/{member_id}/link-user", response_model=ChurchMemberDetailResponse)
async def link_church_member_user(
    member_id: uuid.UUID,
    body: LinkUserBody,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> ChurchMemberDetailResponse:
    """Optional admin/maintenance: attach a login to a registry row. Not part of primary product UX."""
    cm = await registry_service.get_church_member_or_404(session, member_id)
    out = await registry_service.link_user_to_member(session, cm=cm, user_id=body.user_id)
    await record_audit_event(
        action=REGISTRY_MEMBER_LINK_USER,
        summary=f"Linked app user to parish registry record ({out.full_name})",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="church_member",
        target_id=str(out.id),
        metadata={"linked_user_id": str(body.user_id)},
        ip_address=client_ip_from_request(request),
    )
    return out
