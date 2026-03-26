from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine


async def _db_is_healthy(timeout_seconds: float = 2.0) -> bool:
    """
    Lightweight DB connectivity check.
    No domain logic, just verifies the DB can answer `SELECT 1`.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, Exception):
        return False


async def healthz() -> dict[str, Any]:
    db_ok = await _db_is_healthy()
    return {
        "status": "ok",
        "db": "ok" if db_ok else "unreachable",
    }


async def readyz() -> dict[str, Any]:
    db_ok = await _db_is_healthy()
    if not db_ok:
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready", "db": "ok"}

