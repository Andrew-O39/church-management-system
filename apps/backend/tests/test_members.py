from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.enums import UserRole
from app.modules.auth import service as auth_service


async def _promote_to_admin(
    session_factory: async_sessionmaker,
    email: str,
) -> None:
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


@pytest.mark.asyncio
async def test_admin_can_list_members(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "m1@example.com", "Alpha")
    await _register(client, "m2@example.com", "Beta")
    admin_data = await _register(client, "adm@example.com", "Admin")
    await _promote_to_admin(session_factory, "adm@example.com")
    token = await _login(client, "adm@example.com")

    r = await client.get(
        "/api/v1/members/",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 10},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 3
    assert len(body["items"]) >= 3
    emails = {i["email"] for i in body["items"]}
    assert "m1@example.com" in emails
    assert admin_data["user"]["email"] in emails


@pytest.mark.asyncio
async def test_non_admin_cannot_list_members(
    client: AsyncClient,
) -> None:
    reg = await _register(client, "only@example.com")
    token = reg["access_token"]
    r = await client.get(
        "/api/v1/members/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_fetch_member_by_id(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    target = await _register(client, "target@example.com", "Target User")
    await _register(client, "adm2@example.com")
    await _promote_to_admin(session_factory, "adm2@example.com")
    admin_tok = await _login(client, "adm2@example.com")
    mid = target["user"]["id"]

    r = await client.get(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "target@example.com"
    assert body["profile"]["phone_number"] is None


@pytest.mark.asyncio
async def test_admin_can_patch_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    target = await _register(client, "patchme@example.com")
    await _register(client, "adm3@example.com")
    await _promote_to_admin(session_factory, "adm3@example.com")
    admin_tok = await _login(client, "adm3@example.com")
    mid = target["user"]["id"]

    r = await client.patch(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "full_name": "Patched Name",
            "phone_number": "+15550199",
            "marital_status": "married",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] == "Patched Name"
    assert body["profile"]["phone_number"] == "+15550199"
    assert body["profile"]["marital_status"] == "married"


@pytest.mark.asyncio
async def test_user_can_fetch_own_profile(client: AsyncClient) -> None:
    reg = await _register(client, "self@example.com", "Self User")
    token = reg["access_token"]
    r = await client.get(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "self@example.com"
    assert "profile" in r.json()


@pytest.mark.asyncio
async def test_user_can_patch_allowed_self_fields(client: AsyncClient) -> None:
    reg = await _register(client, "selfpatch@example.com")
    token = reg["access_token"]
    r = await client.patch(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": " New Name ",
            "phone_number": "+1000",
            "whatsapp_enabled": False,
            "preferred_channel": "email",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] == " New Name ".strip()
    assert body["profile"]["phone_number"] == "+1000"
    assert body["profile"]["whatsapp_enabled"] is False
    assert body["profile"]["preferred_channel"] == "email"


@pytest.mark.asyncio
async def test_user_cannot_patch_forbidden_fields(client: AsyncClient) -> None:
    reg = await _register(client, "forbid@example.com")
    token = reg["access_token"]
    r = await client.patch(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Ok", "role": "admin"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_admin_email_update_respects_uniqueness(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "keeper@example.com")
    b = await _register(client, "other@example.com")
    await _promote_to_admin(session_factory, "keeper@example.com")
    admin_tok = await _login(client, "keeper@example.com")

    r = await client.patch(
        f"/api/v1/members/{b['user']['id']}",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"email": "keeper@example.com"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_inactive_user_cannot_access_profile(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "inactive@example.com")
    token = reg["access_token"]
    async with session_factory() as session:
        u = await auth_service.get_user_by_email(session, "inactive@example.com")
        assert u is not None
        u.is_active = False
        await session.commit()

    r = await client.get(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_member_cannot_access_admin_member_detail(
    client: AsyncClient,
) -> None:
    victim = await _register(client, "victim@example.com")
    reg = await _register(client, "norule@example.com")
    token = reg["access_token"]
    r = await client.get(
        f"/api/v1/members/{victim['user']['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "selfadmin@example.com")
    await _promote_to_admin(session_factory, "selfadmin@example.com")
    token = await _login(client, "selfadmin@example.com")
    mid = reg["user"]["id"]
    r = await client.patch(
        f"/api/v1/members/{mid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "member"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_can_demote_peer_when_two_admins_exist(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "admA@example.com")
    b = await _register(client, "admB@example.com")
    await _promote_to_admin(session_factory, "admA@example.com")
    await _promote_to_admin(session_factory, "admB@example.com")
    tok_a = await _login(client, "admA@example.com")
    r = await client.patch(
        f"/api/v1/members/{b['user']['id']}",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"role": "member"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_search_and_role_filter(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "findme@example.com", "Unique Zebrane")
    await _register(client, "admsearch@example.com")
    await _promote_to_admin(session_factory, "admsearch@example.com")
    tok = await _login(client, "admsearch@example.com")

    r = await client.get(
        "/api/v1/members/",
        headers={"Authorization": f"Bearer {tok}"},
        params={"search": "Zebrane", "role": "member"},
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert any(i["email"] == "findme@example.com" for i in items)
