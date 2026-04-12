from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session as db_session_module
from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


async def record_audit_event(
    *,
    action: str,
    summary: str,
    actor_user_id: uuid.UUID | None = None,
    actor_email: str | None = None,
    actor_display_name: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Persist an audit row in a dedicated transaction. Swallows errors so primary flows are not blocked."""
    safe_meta = _json_safe(metadata or {})
    if not isinstance(safe_meta, dict):
        safe_meta = {}
    row = AuditLog(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        actor_display_name=actor_display_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        metadata_json=safe_meta,
        ip_address=ip_address,
    )
    try:
        factory = db_session_module.async_session_factory
        async with factory() as audit_session:
            audit_session.add(row)
            await audit_session.commit()
    except Exception:
        logger.exception("audit_log_write_failed action=%s", action)


async def list_audit_logs(
    session: AsyncSession,
    *,
    action: str | None,
    actor_user_id: uuid.UUID | None,
    target_type: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    page: int,
    page_size: int,
) -> tuple[list[AuditLog], int]:
    conds: list[Any] = []
    if action:
        conds.append(AuditLog.action == action)
    if actor_user_id is not None:
        conds.append(AuditLog.actor_user_id == actor_user_id)
    if target_type:
        conds.append(AuditLog.target_type == target_type)
    if date_from is not None:
        conds.append(AuditLog.created_at >= date_from)
    if date_to is not None:
        conds.append(AuditLog.created_at <= date_to)

    base: Select[tuple[AuditLog]] = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if conds:
        base = base.where(and_(*conds))
        count_stmt = count_stmt.where(and_(*conds))

    total = int((await session.execute(count_stmt)).scalar_one())
    stmt = (
        base.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    rows = list(result.scalars().all())
    return rows, total
