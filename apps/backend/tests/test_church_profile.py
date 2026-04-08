from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from sqlalchemy import select

from app.db.models.church_profile import CHURCH_PROFILE_SINGLETON_ID, ChurchProfile
from app.db.models.enums import UserRole
from app.modules.auth import service as auth_service


async def _promote_to_admin(session_factory: async_sessionmaker, email: str) -> None:
    async with session_factory() as session:
        user = await auth_service.get_user_by_email(session, email)
        assert user is not None
        user.role = UserRole.ADMIN
        await session.commit()


async def _register(client: AsyncClient, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"full_name": "U", "email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text


async def _login(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_church_profile_forbidden_for_non_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_member@example.com")
    tok = await _login(client, "cp_member@example.com")
    h = {"Authorization": f"Bearer {tok}"}
    for method, path in (
        ("GET", "/api/v1/church-profile/"),
        ("PUT", "/api/v1/church-profile/"),
    ):
        r = await client.request(method, path, headers=h, json={"church_name": "X"})
        assert r.status_code == 403, (method, path, r.text)


@pytest.mark.asyncio
async def test_church_profile_get_returns_empty_then_put_creates(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_admin1@example.com")
    await _promote_to_admin(session_factory, "cp_admin1@example.com")
    tok = await _login(client, "cp_admin1@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    g0 = await client.get("/api/v1/church-profile/", headers=h)
    assert g0.status_code == 200
    b0 = g0.json()
    assert b0["id"] is None
    assert b0["church_name"] == ""

    p1 = await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={
            "church_name": "Shepherd Parish",
            "short_name": "Shepherd",
            "address": "123 Main St",
            "phone": "+1 555 0100",
            "email": "office@example.com",
        },
    )
    assert p1.status_code == 200, p1.text
    j1 = p1.json()
    assert j1["id"] == str(CHURCH_PROFILE_SINGLETON_ID)
    assert j1["church_name"] == "Shepherd Parish"
    assert j1["short_name"] == "Shepherd"
    assert j1["address"] == "123 Main St"

    g1 = await client.get("/api/v1/church-profile/", headers=h)
    assert g1.status_code == 200
    assert g1.json()["church_name"] == "Shepherd Parish"
    assert g1.json()["id"] == str(CHURCH_PROFILE_SINGLETON_ID)


@pytest.mark.asyncio
async def test_church_profile_put_updates_existing(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_admin2@example.com")
    await _promote_to_admin(session_factory, "cp_admin2@example.com")
    tok = await _login(client, "cp_admin2@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={"church_name": "First Name"},
    )
    p2 = await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={"church_name": "Updated Parish", "phone": None, "address": "New Rd"},
    )
    assert p2.status_code == 200
    assert p2.json()["church_name"] == "Updated Parish"
    assert p2.json()["address"] == "New Rd"


@pytest.mark.asyncio
async def test_export_csv_filename_uses_church_slug(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_csv_fn@example.com")
    await _promote_to_admin(session_factory, "cp_csv_fn@example.com")
    tok = await _login(client, "cp_csv_fn@example.com")
    h = {"Authorization": f"Bearer {tok}"}
    await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={"church_name": "Shepherd Parish"},
    )
    r = await client.get("/api/v1/exports/users.csv", headers=h)
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "shepherd-parish-app-users-" in cd
    assert ".csv" in cd


@pytest.mark.asyncio
async def test_export_print_payload_includes_church_identity(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_export@example.com")
    await _promote_to_admin(session_factory, "cp_export@example.com")
    tok = await _login(client, "cp_export@example.com")
    h = {"Authorization": f"Bearer {tok}"}
    await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={
            "church_name": "Holy Name Parish",
            "address": "1 Church Rd",
            "phone": "555",
            "email": "office@holyname.example",
        },
    )
    r = await client.get("/api/v1/exports/users/print", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["church_name"] == "Holy Name Parish"
    assert body["address"] == "1 Church Rd"
    assert body["phone"] == "555"
    assert body["email"] == "office@holyname.example"


@pytest.mark.asyncio
async def test_singleton_row_in_db(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "cp_admin3@example.com")
    await _promote_to_admin(session_factory, "cp_admin3@example.com")
    tok = await _login(client, "cp_admin3@example.com")
    h = {"Authorization": f"Bearer {tok}"}
    await client.put(
        "/api/v1/church-profile/",
        headers=h,
        json={"church_name": "One Row Only"},
    )
    async with session_factory() as session:
        rows = (await session.execute(select(ChurchProfile))).scalars().all()
        assert len(rows) == 1
        assert rows[0].church_name == "One Row Only"
