from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.audit_logs import service as audit_service
from app.modules.audit_logs.schemas import AuditLogItem, AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

_MAX_PAGE_SIZE = 100


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _admin: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    action: str | None = Query(default=None, max_length=128),
    actor_user_id: uuid.UUID | None = Query(default=None),
    target_type: str | None = Query(default=None, max_length=64),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=_MAX_PAGE_SIZE),
) -> AuditLogListResponse:
    rows, total = await audit_service.list_audit_logs(
        session,
        action=action,
        actor_user_id=actor_user_id,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[AuditLogItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
