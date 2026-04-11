from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.registry_saved_filters import service as saved_filters_service
from app.modules.registry_saved_filters.schemas import (
    RegistrySavedFilterCreate,
    RegistrySavedFilterOut,
    RegistrySavedFilterPatch,
)

router = APIRouter(prefix="/registry-saved-filters", tags=["registry-saved-filters"])

_admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


@router.get("/", response_model=list[RegistrySavedFilterOut])
async def list_saved_registry_filters(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: _admin,
) -> list[RegistrySavedFilterOut]:
    rows = await saved_filters_service.list_for_user(session, user_id=admin.id)
    return [RegistrySavedFilterOut.model_validate(saved_filters_service.to_out(r)) for r in rows]


@router.post("/", response_model=RegistrySavedFilterOut, status_code=status.HTTP_201_CREATED)
async def create_saved_registry_filter(
    body: RegistrySavedFilterCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: _admin,
) -> RegistrySavedFilterOut:
    row = await saved_filters_service.create_saved(
        session,
        user_id=admin.id,
        name=body.name,
        filters=body.filters,
    )
    return RegistrySavedFilterOut.model_validate(saved_filters_service.to_out(row))


@router.patch("/{saved_id}", response_model=RegistrySavedFilterOut)
async def patch_saved_registry_filter(
    saved_id: uuid.UUID,
    body: RegistrySavedFilterPatch,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: _admin,
) -> RegistrySavedFilterOut:
    row = await saved_filters_service.update_saved(
        session,
        user_id=admin.id,
        saved_id=saved_id,
        name=body.name,
        filters=body.filters,
    )
    return RegistrySavedFilterOut.model_validate(saved_filters_service.to_out(row))


@router.delete("/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_registry_filter(
    saved_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    admin: _admin,
) -> Response:
    await saved_filters_service.delete_saved(session, user_id=admin.id, saved_id=saved_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
