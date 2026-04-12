from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.audit_log import AuditLog
from app.db.models.enums import UserRole
from app.modules.audit_logs.actions import (
    AUTH_LOGIN_FAILURE,
    AUTH_LOGIN_SUCCESS,
    EVENTS_CREATE,
    EXPORT_ATTENDANCE_CSV,
    MINISTRIES_CREATE,
    NOTIFICATION_SEND,
)
from app.modules.auth import service as auth_service


async def _promote_to_admin(session_factory: async_sessionmaker, email: str) -> None:
    async with session_factory() as session:
        user = await auth_service.get_user_by_email(session, email)
        assert user is not None
        user.role = UserRole.ADMIN
        await session.commit()


async def _register(client: AsyncClient, email: str, name: str = "Member") -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={"full_name": name, "email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _login(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def _count_audit_rows(session_factory: async_sessionmaker, *, action: str | None = None) -> int:
    async with session_factory() as session:
        stmt = select(func.count()).select_from(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        return int((await session.execute(stmt)).scalar_one())


@pytest.mark.asyncio
async def test_audit_logs_forbidden_for_member(client: AsyncClient) -> None:
    reg = await _register(client, "mem_audit@example.com")
    token = reg["access_token"]
    r = await client.get("/api/v1/audit-logs/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_list_admin_ok(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm_audit@example.com")
    await _promote_to_admin(session_factory, "adm_audit@example.com")
    token = await _login(client, "adm_audit@example.com")
    r = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 10},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "total" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_login_failure_creates_audit_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "badlogin@example.com")
    before = await _count_audit_rows(session_factory, action=AUTH_LOGIN_FAILURE)
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "badlogin@example.com", "password": "wrong-password-xyz"},
    )
    assert r.status_code == 401
    after = await _count_audit_rows(session_factory, action=AUTH_LOGIN_FAILURE)
    assert after == before + 1


@pytest.mark.asyncio
async def test_login_success_creates_audit_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "goodlogin@example.com")
    before = await _count_audit_rows(session_factory, action=AUTH_LOGIN_SUCCESS)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "goodlogin@example.com", "password": "password123"},
    )
    after = await _count_audit_rows(session_factory, action=AUTH_LOGIN_SUCCESS)
    assert after == before + 1


@pytest.mark.asyncio
async def test_export_attendance_csv_creates_audit_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "exp_audit@example.com")
    await _promote_to_admin(session_factory, "exp_audit@example.com")
    token = await _login(client, "exp_audit@example.com")
    before = await _count_audit_rows(session_factory, action=EXPORT_ATTENDANCE_CSV)
    r = await client.get(
        "/api/v1/exports/attendance.csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    after = await _count_audit_rows(session_factory, action=EXPORT_ATTENDANCE_CSV)
    assert after == before + 1


@pytest.mark.asyncio
async def test_notification_send_creates_audit_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "notif_target@example.com")
    uid = reg["user"]["id"]
    await _register(client, "notif_admin@example.com")
    await _promote_to_admin(session_factory, "notif_admin@example.com")
    token = await _login(client, "notif_admin@example.com")
    before = await _count_audit_rows(session_factory, action=NOTIFICATION_SEND)
    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Audit test",
            "body": "Hello",
            "category": "general",
            "channels": ["in_app"],
            "audience_type": "direct_users",
            "user_ids": [uid],
        },
    )
    assert r.status_code == 201, r.text
    after = await _count_audit_rows(session_factory, action=NOTIFICATION_SEND)
    assert after == before + 1


@pytest.mark.asyncio
async def test_audit_logs_filter_by_action(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "filter_a@example.com")
    await _promote_to_admin(session_factory, "filter_a@example.com")
    admin_tok = await _login(client, "filter_a@example.com")
    # Ensure at least one auth event exists
    await client.post(
        "/api/v1/auth/login",
        json={"email": "filter_a@example.com", "password": "password123"},
    )
    r = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"action": AUTH_LOGIN_SUCCESS, "page": 1, "page_size": 50},
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert all(i["action"] == AUTH_LOGIN_SUCCESS for i in items)


@pytest.mark.asyncio
async def test_audit_logs_filter_date_range(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "dates@example.com")
    await _promote_to_admin(session_factory, "dates@example.com")
    admin_tok = await _login(client, "dates@example.com")
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()
    r = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"date_from": start, "date_to": end, "page": 1, "page_size": 20},
    )
    assert r.status_code == 200, r.text
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_event_create_writes_audit_log(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ev_audit@example.com")
    await _promote_to_admin(session_factory, "ev_audit@example.com")
    tok = await _login(client, "ev_audit@example.com")
    before = await _count_audit_rows(session_factory, action=EVENTS_CREATE)
    start = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 1, 11, 0, tzinfo=timezone.utc)
    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Audit Event",
            "description": "x",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Here",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert r.status_code == 201, r.text
    after = await _count_audit_rows(session_factory, action=EVENTS_CREATE)
    assert after == before + 1


@pytest.mark.asyncio
async def test_ministry_create_writes_audit_log(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "min_audit@example.com")
    await _promote_to_admin(session_factory, "min_audit@example.com")
    tok = await _login(client, "min_audit@example.com")
    before = await _count_audit_rows(session_factory, action=MINISTRIES_CREATE)
    r = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Audit Ministry", "description": "d", "is_active": True},
    )
    assert r.status_code == 201, r.text
    after = await _count_audit_rows(session_factory, action=MINISTRIES_CREATE)
    assert after == before + 1


@pytest.mark.asyncio
async def test_audit_logs_filter_actor_user_id(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "actor_f@example.com")
    uid = reg["user"]["id"]
    await _register(client, "actor_adm@example.com")
    await _promote_to_admin(session_factory, "actor_adm@example.com")
    admin_tok = await _login(client, "actor_adm@example.com")
    r = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"actor_user_id": str(uid), "page": 1, "page_size": 50},
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) >= 1
    for row in items:
        assert row["actor_user_id"] == str(uid)
