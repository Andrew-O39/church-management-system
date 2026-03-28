from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from sqlalchemy import func, select

from app.db.models.church_member import ChurchMember
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
async def test_admin_create_church_member_without_user(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regadmin@example.com")
    await _promote_to_admin(session_factory, "regadmin@example.com")
    tok = await _login(client, "regadmin@example.com")

    r = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Child", "last_name": "NoLogin"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["full_name"]
    assert body["linked_user_id"] is None


@pytest.mark.asyncio
async def test_link_user_to_standalone_church_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "linktarget@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    await _register(client, "linkadmin@example.com")
    await _promote_to_admin(session_factory, "linkadmin@example.com")
    tok = await _login(client, "linkadmin@example.com")

    cr = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Adult", "last_name": "Offline"},
    )
    assert cr.status_code == 201, cr.text
    cm_id = cr.json()["id"]

    lr = await client.patch(
        f"/api/v1/church-members/{cm_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": str(uid)},
    )
    assert lr.status_code == 200, lr.text
    assert lr.json()["linked_user_id"] == str(uid)

    got = await client.get(
        f"/api/v1/church-members/{cm_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert got.status_code == 200, got.text
    assert got.json()["linked_user_id"] == str(uid)
    assert got.json()["user_id"] == str(uid)


@pytest.mark.asyncio
async def test_register_does_not_create_church_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "noregistry@example.com", "No Registry Row")
    assert reg["user"]["member_id"] is None
    async with session_factory() as session:
        n = (await session.execute(select(func.count()).select_from(ChurchMember))).scalar_one()
        assert int(n) == 0


@pytest.mark.asyncio
async def test_get_my_church_member_profile_requires_registry_link(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "memprofile@example.com", "Patronus Member")
    tok = reg["access_token"]

    r = await client.get(
        "/api/v1/church-members/me",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_get_my_church_member_404_when_unlinked(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "unlinkedme@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    r = await client.get(
        "/api/v1/church-members/me",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_duplicate_name_and_dob_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "dupadmin@example.com")
    await _promote_to_admin(session_factory, "dupadmin@example.com")
    tok = await _login(client, "dupadmin@example.com")
    common = {"first_name": "Sam", "last_name": "Same", "date_of_birth": "2010-05-01"}

    r1 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json=common,
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json=common,
    )
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_church_member_stats_shape(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "statsuser@example.com")
    await _promote_to_admin(session_factory, "statsuser@example.com")
    tok = await _login(client, "statsuser@example.com")

    r0 = await client.get(
        "/api/v1/church-members/stats",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r0.status_code == 200, r0.text
    s0 = r0.json()
    assert "total_members" in s0
    assert "members_with_accounts" in s0
    assert "members_without_accounts" in s0
    assert "gender_distribution" in s0
    assert "age_groups" in s0
    before_total = s0["total_members"]

    await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Stats", "last_name": "Only"},
    )

    r1 = await client.get(
        "/api/v1/church-members/stats",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r1.status_code == 200, r1.text
    s1 = r1.json()
    assert s1["total_members"] == before_total + 1
    assert s1["members_without_accounts"] == s0["members_without_accounts"] + 1
