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
async def test_saved_filters_crud_admin_only_own_rows(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "sf_admin_a@example.com")
    await _promote_to_admin(session_factory, "sf_admin_a@example.com")
    tok_a = await _login(client, "sf_admin_a@example.com")
    ha = {"Authorization": f"Bearer {tok_a}"}

    await _register(client, "sf_admin_b@example.com")
    await _promote_to_admin(session_factory, "sf_admin_b@example.com")
    tok_b = await _login(client, "sf_admin_b@example.com")
    hb = {"Authorization": f"Bearer {tok_b}"}

    cr = await client.post(
        "/api/v1/registry-saved-filters/",
        headers=ha,
        json={
            "name": "Young adults",
            "filters": {"age_group": "young_adult", "is_baptized": "true"},
        },
    )
    assert cr.status_code == 201, cr.text
    body = cr.json()
    sid = body["id"]
    assert body["name"] == "Young adults"
    assert body["filters"]["age_group"] == "young_adult"

    lst = await client.get("/api/v1/registry-saved-filters/", headers=ha)
    assert lst.status_code == 200
    assert len(lst.json()) == 1

    lst_b = await client.get("/api/v1/registry-saved-filters/", headers=hb)
    assert lst_b.status_code == 200
    assert lst_b.json() == []

    pat = await client.patch(
        f"/api/v1/registry-saved-filters/{sid}",
        headers=ha,
        json={"name": "Young adults (updated)"},
    )
    assert pat.status_code == 200
    assert pat.json()["name"] == "Young adults (updated)"

    other = str(uuid.uuid4())
    nf = await client.patch(
        f"/api/v1/registry-saved-filters/{other}",
        headers=ha,
        json={"name": "noop"},
    )
    assert nf.status_code == 404

    de = await client.delete(f"/api/v1/registry-saved-filters/{sid}", headers=ha)
    assert de.status_code == 204

    lst2 = await client.get("/api/v1/registry-saved-filters/", headers=ha)
    assert lst2.json() == []


@pytest.mark.asyncio
async def test_saved_filters_member_forbidden(client: AsyncClient) -> None:
    reg = await _register(client, "sf_member@example.com")
    tok = reg["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.get("/api/v1/registry-saved-filters/", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_saved_filters_rejects_unknown_filter_key(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "sf_badkey@example.com")
    await _promote_to_admin(session_factory, "sf_badkey@example.com")
    tok = await _login(client, "sf_badkey@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.post(
        "/api/v1/registry-saved-filters/",
        headers=h,
        json={"name": "Bad", "filters": {"page": "1"}},
    )
    assert r.status_code == 400
    assert "unknown filter key" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_saved_filters_persists_registry_keys(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "sf_keys@example.com")
    await _promote_to_admin(session_factory, "sf_keys@example.com")
    tok = await _login(client, "sf_keys@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    payload = {
        "name": "Full sample",
        "filters": {
            "search": "Smith",
            "membership_status": "inactive",
            "is_active": "false",
            "gender": "female",
            "baptism_date_from": "2024-01-01",
            "first_communion_date_to": "2020-12-31",
        },
    }
    cr = await client.post("/api/v1/registry-saved-filters/", headers=h, json=payload)
    assert cr.status_code == 201, cr.text
    got = cr.json()["filters"]
    assert got["search"] == "Smith"
    assert got["membership_status"] == "inactive"
    assert got["baptism_date_from"] == "2024-01-01"

    lid = await client.get("/api/v1/registry-saved-filters/", headers=h)
    assert lid.status_code == 200
    assert lid.json()[0]["filters"]["first_communion_date_to"] == "2020-12-31"
