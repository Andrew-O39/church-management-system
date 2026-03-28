from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Member",
            "email": "member@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "member@example.com"
    assert body["user"]["role"] == "member"
    assert body["user"]["member_id"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Member",
            "email": "login@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Member",
            "email": "badpw@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "badpw@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Me User",
            "email": "me@example.com",
            "password": "password123",
        },
    )
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_admin_ping_forbidden_for_member(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Member",
            "email": "rbac@example.com",
            "password": "password123",
        },
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
