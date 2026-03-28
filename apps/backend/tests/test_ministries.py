from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.enums import UserRole
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


@pytest.mark.asyncio
async def test_admin_create_ministry(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    await _register(client, "admin1@example.com")
    await _promote_to_admin(session_factory, "admin1@example.com")
    tok = await _login(client, "admin1@example.com")

    r = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "name": "  Youth Ministry  ",
            "description": "Teens and young adults",
            "is_active": True,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Youth Ministry"
    assert body["is_active"] is True
    assert body["members"] == []


@pytest.mark.asyncio
async def test_admin_list_ministries_search_filter(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "admin2@example.com")
    await _promote_to_admin(session_factory, "admin2@example.com")
    tok = await _login(client, "admin2@example.com")

    for name in ("Choir", "Ushers", "Youth Group"):
        cr = await client.post(
            "/api/v1/ministries/",
            headers={"Authorization": f"Bearer {tok}"},
            json={"name": name},
        )
        assert cr.status_code == 201, cr.text

    r = await client.get(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        params={"search": "cho", "page": 1, "page_size": 20},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    names = {i["name"] for i in body["items"]}
    assert "Choir" in names
    assert "Ushers" not in names


@pytest.mark.asyncio
async def test_admin_patch_ministry(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    await _register(client, "admin3@example.com")
    await _promote_to_admin(session_factory, "admin3@example.com")
    tok = await _login(client, "admin3@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Readers"},
    )
    mid = c.json()["id"]

    r = await client.patch(
        f"/api/v1/ministries/{mid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"description": "Lectors", "is_active": False},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["description"] == "Lectors"
    assert body["is_active"] is False


@pytest.mark.asyncio
async def test_admin_add_member_to_ministry(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    member = await _register(client, "joiner@example.com", "Joiner")
    uid = member["user"]["id"]

    await _register(client, "admin4@example.com")
    await _promote_to_admin(session_factory, "admin4@example.com")
    tok = await _login(client, "admin4@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Prayer Group"},
    )
    mid = c.json()["id"]

    r = await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_in_ministry": "member"},
    )
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["linked_user_id"] == uid
    assert row["church_member_id"] == member["user"]["member_id"]
    assert row["email"] == "joiner@example.com"

    d = await client.get(
        f"/api/v1/ministries/{mid}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert d.status_code == 200
    assert len(d.json()["members"]) == 1


@pytest.mark.asyncio
async def test_duplicate_active_membership_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "dup@example.com")
    uid = member["user"]["id"]
    await _register(client, "admin5@example.com")
    await _promote_to_admin(session_factory, "admin5@example.com")
    tok = await _login(client, "admin5@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Band"},
    )
    mid = c.json()["id"]

    r1 = await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid},
    )
    assert r1.status_code == 201, r1.text
    r2 = await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_ministries(client: AsyncClient) -> None:
    reg = await _register(client, "plain@example.com")
    tok = reg["access_token"]

    r = await client.get("/api/v1/ministries/", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403

    r2 = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "X"},
    )
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_ministries_me_returns_user_ministries(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "inmin@example.com")
    mtok = member["access_token"]
    uid = member["user"]["id"]

    await _register(client, "admin6@example.com")
    await _promote_to_admin(session_factory, "admin6@example.com")
    atok = await _login(client, "admin6@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {atok}"},
        json={"name": "Altar Guild"},
    )
    mid = c.json()["id"]

    await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {atok}"},
        json={"user_id": uid},
    )

    r = await client.get("/api/v1/ministries/me", headers={"Authorization": f"Bearer {mtok}"})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["ministry_id"] == mid
    assert items[0]["name"] == "Altar Guild"


@pytest.mark.asyncio
async def test_member_can_view_own_ministry_detail_not_full_roster(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m1 = await _register(client, "m_a@example.com")
    m2 = await _register(client, "m_b@example.com")
    uid_a = m1["user"]["id"]

    await _register(client, "admin7@example.com")
    await _promote_to_admin(session_factory, "admin7@example.com")
    atok = await _login(client, "admin7@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {atok}"},
        json={"name": "Guild"},
    )
    mid = c.json()["id"]

    await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {atok}"},
        json={"user_id": uid_a},
    )
    await client.post(
        f"/api/v1/ministries/{mid}/members",
        headers={"Authorization": f"Bearer {atok}"},
        json={"user_id": m2["user"]["id"]},
    )

    tok_a = await _login(client, "m_a@example.com")
    r = await client.get(
        f"/api/v1/ministries/{mid}",
        headers={"Authorization": f"Bearer {tok_a}"},
    )
    assert r.status_code == 200, r.text
    members = r.json()["members"]
    assert len(members) == 1
    assert members[0]["linked_user_id"] == uid_a


@pytest.mark.asyncio
async def test_member_cannot_view_ministry_not_in(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "outsider@example.com")
    otok = await _login(client, "outsider@example.com")

    await _register(client, "admin8@example.com")
    await _promote_to_admin(session_factory, "admin8@example.com")
    atok = await _login(client, "admin8@example.com")

    c = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {atok}"},
        json={"name": "Secret Club"},
    )
    mid = c.json()["id"]

    r = await client.get(
        f"/api/v1/ministries/{mid}",
        headers={"Authorization": f"Bearer {otok}"},
    )
    assert r.status_code == 403
