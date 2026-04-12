from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.church_profile import service as church_profile_service
from app.modules.church_profile.schemas import ChurchProfileResponse, ChurchProfileUpdateRequest
from app.modules.audit_logs.actions import CHURCH_PROFILE_UPDATE
from app.modules.audit_logs.request_ip import client_ip_from_request
from app.modules.audit_logs.service import record_audit_event

router = APIRouter(prefix="/church-profile", tags=["church-profile"])

_admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


@router.get("/", response_model=ChurchProfileResponse)
async def get_church_profile(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
) -> ChurchProfileResponse:
    return await church_profile_service.get_church_profile(session)


@router.put("/", response_model=ChurchProfileResponse)
async def put_church_profile(
    body: ChurchProfileUpdateRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: _admin,
) -> ChurchProfileResponse:
    out = await church_profile_service.update_or_create_church_profile(session, body)
    fields = sorted(body.model_dump(exclude_unset=True).keys())
    await record_audit_event(
        action=CHURCH_PROFILE_UPDATE,
        summary="Church profile / settings updated",
        actor_user_id=admin.id,
        actor_email=admin.email,
        actor_display_name=admin.full_name,
        target_type="church_profile",
        target_id=str(out.id),
        metadata={"fields_changed": fields},
        ip_address=client_ip_from_request(request),
    )
    return out
