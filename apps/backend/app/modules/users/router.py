from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.users import service as users_service
from app.modules.users.schemas import RegistryFilter, UserSearchResponse

router = APIRouter(prefix="/users", tags=["users"])

_MAX_PAGE_SIZE = 50


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    q: str | None = Query(default=None, max_length=200, description="Search name, email, phone, or contact email"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
    registry_filter: RegistryFilter = Query(
        default=RegistryFilter.all,
        description="Limit to users with/without a linked parish record",
    ),
    for_member_id: uuid.UUID | None = Query(
        default=None,
        description="Church member id being edited — used to label link context (this vs other record)",
    ),
) -> UserSearchResponse:
    """Search app ``User`` accounts (admin tooling). Not the parish registry API."""
    return await users_service.search_users_for_admin(
        session,
        q=q,
        page=page,
        page_size=page_size,
        registry_filter=registry_filter,
        for_member_id=for_member_id,
    )
