from __future__ import annotations

import uuid

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
async def test_user_search_requires_admin(client: AsyncClient) -> None:
    reg = await _register(client, "plainmember@example.com")
    tok = reg["access_token"]

    r = await client.get(
        "/api/v1/users/search?q=test",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_user_search_returns_expected_results(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "findable_alpha@example.com", "Zeta UniqueNameXYZ")
    await _register(client, "findable_beta@example.com", "Other Person")

    await _register(client, "searchadmin@example.com")
    await _promote_to_admin(session_factory, "searchadmin@example.com")
    tok = await _login(client, "searchadmin@example.com")

    r = await client.get(
        "/api/v1/users/search?q=UniqueNameXYZ",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    emails = {item["email"] for item in body["items"]}
    assert "findable_alpha@example.com" in emails


@pytest.mark.asyncio
async def test_user_search_registry_filter_unlinked(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "unlinkedonly@example.com", "Unlinked Search User")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    await _register(client, "filteradmin@example.com")
    await _promote_to_admin(session_factory, "filteradmin@example.com")
    tok = await _login(client, "filteradmin@example.com")

    r = await client.get(
        "/api/v1/users/search?q=Unlinked+Search&registry_filter=unlinked",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    ids = {item["user_id"] for item in body["items"]}
    assert str(uid) in ids
    for item in body["items"]:
        assert item["member_id"] is None


@pytest.mark.asyncio
async def test_link_user_rejects_already_linked_elsewhere(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "linkbusy@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    await _register(client, "linkadmin2@example.com")
    await _promote_to_admin(session_factory, "linkadmin2@example.com")
    tok = await _login(client, "linkadmin2@example.com")

    cm1 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "First", "last_name": "Record"},
    )
    assert cm1.status_code == 201, cm1.text
    cm1_id = cm1.json()["id"]

    cm2 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Second", "last_name": "Record"},
    )
    assert cm2.status_code == 201, cm2.text
    cm2_id = cm2.json()["id"]

    lr = await client.patch(
        f"/api/v1/church-members/{cm1_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": str(uid)},
    )
    assert lr.status_code == 200, lr.text

    bad = await client.patch(
        f"/api/v1/church-members/{cm2_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": str(uid)},
    )
    assert bad.status_code == 409, bad.text
    assert "already linked" in bad.json()["detail"].lower()


@pytest.mark.asyncio
async def test_link_user_succeeds_for_unlinked_user(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "linkfree@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    await _register(client, "linkadmin3@example.com")
    await _promote_to_admin(session_factory, "linkadmin3@example.com")
    tok = await _login(client, "linkadmin3@example.com")

    cm = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Solo", "last_name": "Link"},
    )
    assert cm.status_code == 201, cm.text
    cm_id = cm.json()["id"]

    lr = await client.patch(
        f"/api/v1/church-members/{cm_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": str(uid)},
    )
    assert lr.status_code == 200, lr.text
    assert lr.json()["linked_user_id"] == str(uid)


@pytest.mark.asyncio
async def test_user_search_for_member_id_marks_link_context(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "ctxadmin@example.com")
    await _promote_to_admin(session_factory, "ctxadmin@example.com")
    tok = await _login(client, "ctxadmin@example.com")

    # Admin is linked to a different registry row than the search context (for_member_id).
    linked_elsewhere = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Other", "last_name": "ParishPerson"},
    )
    assert linked_elsewhere.status_code == 201, linked_elsewhere.text
    link_cm_id = linked_elsewhere.json()["id"]
    lr = await client.patch(
        f"/api/v1/church-members/{link_cm_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": reg["user"]["id"]},
    )
    assert lr.status_code == 200, lr.text

    cm = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Ctx", "last_name": "Member"},
    )
    assert cm.status_code == 201, cm.text
    cm_id = cm.json()["id"]

    r = await client.get(
        f"/api/v1/users/search?q=ctxadmin&for_member_id={cm_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["items"]
    admin_item = next(i for i in body["items"] if i["email"] == "ctxadmin@example.com")
    assert admin_item["registry_link_status"] == "linked_other_member"
    assert admin_item["linked_church_member_name"]
