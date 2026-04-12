from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.audit_log import AuditLog
from app.db.models.enums import UserRole
from app.modules.audit_logs.actions import (
    APP_USER_ADMIN_DEMOTED,
    APP_USER_ADMIN_PROMOTED,
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


async def _audit_count_for(
    session_factory: async_sessionmaker,
    *,
    action: str,
    target_id: str,
) -> int:
    async with session_factory() as session:
        q = await session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == action, AuditLog.target_id == target_id),
        )
        return int(q.scalar_one())


@pytest.mark.asyncio
async def test_admin_promotes_user_to_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "promo_target@example.com", "Promo Target")
    await _register(client, "promo_adm@example.com")
    await _promote_to_admin(session_factory, "promo_adm@example.com")
    tok = await _login(client, "promo_adm@example.com")
    mid = m["user"]["id"]
    before = await _audit_count_for(
        session_factory,
        action=APP_USER_ADMIN_PROMOTED,
        target_id=mid,
    )
    r = await client.patch(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"role": "admin"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "admin"
    after = await _audit_count_for(
        session_factory,
        action=APP_USER_ADMIN_PROMOTED,
        target_id=mid,
    )
    assert after == before + 1


@pytest.mark.asyncio
async def test_admin_demotes_other_admin_when_two_exist(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    a = await _register(client, "two_a@example.com", "Admin A")
    b = await _register(client, "two_b@example.com", "Admin B")
    await _promote_to_admin(session_factory, "two_a@example.com")
    await _promote_to_admin(session_factory, "two_b@example.com")
    tok_a = await _login(client, "two_a@example.com")
    bid = b["user"]["id"]
    r = await client.patch(
        f"/api/v1/members/{bid}",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"role": "member"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "member"


@pytest.mark.asyncio
async def test_sole_admin_cannot_change_own_role_away_from_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    solo = await _register(client, "solo_role@example.com", "Solo Admin")
    await _promote_to_admin(session_factory, "solo_role@example.com")
    tok = await _login(client, "solo_role@example.com")
    mid = solo["user"]["id"]
    r = await client.patch(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"role": "member"},
    )
    assert r.status_code == 400
    assert "cannot change your own role" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_deactivate_last_active_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    solo = await _register(client, "deact_solo@example.com", "Solo")
    await _promote_to_admin(session_factory, "deact_solo@example.com")
    tok = await _login(client, "deact_solo@example.com")
    mid = solo["user"]["id"]
    r = await client.patch(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"is_active": False},
    )
    assert r.status_code == 400
    assert "last active administrator" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_member_cannot_promote_to_admin(
    client: AsyncClient,
) -> None:
    victim = await _register(client, "victim@example.com", "Victim")
    member_reg = await _register(client, "plain@example.com", "Plain")
    tok = member_reg["access_token"]
    vid = victim["user"]["id"]
    r2 = await client.patch(
        f"/api/v1/members/{vid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"role": "admin"},
    )
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_demote_emits_audit_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "dm_a@example.com", "A")
    b = await _register(client, "dm_b@example.com", "B")
    await _promote_to_admin(session_factory, "dm_a@example.com")
    await _promote_to_admin(session_factory, "dm_b@example.com")
    tok = await _login(client, "dm_a@example.com")
    bid = b["user"]["id"]
    before = await _audit_count_for(
        session_factory,
        action=APP_USER_ADMIN_DEMOTED,
        target_id=bid,
    )
    r = await client.patch(
        f"/api/v1/members/{bid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"role": "member"},
    )
    assert r.status_code == 200, r.text
    after = await _audit_count_for(
        session_factory,
        action=APP_USER_ADMIN_DEMOTED,
        target_id=bid,
    )
    assert after == before + 1
