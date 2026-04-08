from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.church_profile import service as church_profile_service
from app.modules.church_profile.schemas import ChurchProfileResponse, ChurchProfileUpdateRequest

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
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
) -> ChurchProfileResponse:
    return await church_profile_service.update_or_create_church_profile(session, body)
