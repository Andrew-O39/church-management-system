from __future__ import annotations

from datetime import datetime, timezone

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


async def _create_ministry(client: AsyncClient, admin_token: str, name: str = "Youth") -> dict:
    r = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "description": "test", "is_active": True},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_admin_create_event(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    await _register(client, "admin@example.com")
    await _promote_to_admin(session_factory, "admin@example.com")
    tok = await _login(client, "admin@example.com")

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc)
    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Sunday Mass",
            "description": "test",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Main Church",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Sunday Mass"
    assert body["event_type"] == "service"


@pytest.mark.asyncio
async def test_admin_list_events_filter(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "admin2@example.com")
    await _promote_to_admin(session_factory, "admin2@example.com")
    tok = await _login(client, "admin2@example.com")

    base = datetime(2026, 4, 2, 10, 0, tzinfo=timezone.utc)
    e1_start = base
    e1_end = base.replace(hour=11)
    e2_start = base.replace(day=3)
    e2_end = e2_start.replace(hour=12)

    await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Choir Rehearsal",
            "event_type": "rehearsal",
            "start_at": e1_start.isoformat(),
            "end_at": e1_end.isoformat(),
            "location": "Hall",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Council Meeting",
            "event_type": "meeting",
            "start_at": e2_start.isoformat(),
            "end_at": e2_end.isoformat(),
            "location": "Room 2",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )

    r = await client.get(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        params={"search": "choir", "page": 1, "page_size": 20},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["event_type"] == "rehearsal"


@pytest.mark.asyncio
async def test_invalid_date_range_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "admin3@example.com")
    await _promote_to_admin(session_factory, "admin3@example.com")
    tok = await _login(client, "admin3@example.com")

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Bad Event",
            "event_type": "other",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Somewhere",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_ministry_linked_event_creation_blocked_when_ministry_inactive(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "admin4@example.com")
    await _promote_to_admin(session_factory, "admin4@example.com")
    tok = await _login(client, "admin4@example.com")

    ministry = await _create_ministry(client, tok, name="Youth")

    # Deactivate ministry.
    await client.patch(
        f"/api/v1/ministries/{ministry['id']}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"is_active": False},
    )

    start = datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 5, 11, 0, tzinfo=timezone.utc)
    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Youth Meet",
            "event_type": "meeting",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Youth Room",
            "is_active": True,
            "visibility": "internal",
            "ministry_id": ministry["id"],
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_events(client: AsyncClient) -> None:
    reg = await _register(client, "member@example.com")
    tok = reg["access_token"]

    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc)

    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Should Fail",
            "event_type": "other",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Somewhere",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_events_me_visibility_for_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    # Admin + a member who belongs to one ministry.
    member = await _register(client, "visible_member@example.com")
    await _register(client, "admin5@example.com")
    await _promote_to_admin(session_factory, "admin5@example.com")
    admin_tok = await _login(client, "admin5@example.com")

    ministry = await _create_ministry(client, admin_tok, name="Prayer Group")
    # Add member to ministry.
    await client.post(
        f"/api/v1/ministries/{ministry['id']}/members",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "role_in_ministry": "member"},
    )

    start = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)

    # Church-wide public (visible).
    pub = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Sunday Service",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Main Church",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert pub.status_code == 201

    # Church-wide internal (visible to authenticated non-admins after the visibility rule change).
    internal = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Internal Retreat Info",
            "event_type": "retreat",
            "start_at": start.replace(day=2).isoformat(),
            "end_at": end.replace(day=2).isoformat(),
            "location": "Secret",
            "is_active": True,
            "visibility": "internal",
            "ministry_id": None,
        },
    )
    assert internal.status_code == 201

    # Ministry-linked active (visible).
    min_ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Prayer Meeting",
            "event_type": "meeting",
            "start_at": start.replace(day=3).isoformat(),
            "end_at": end.replace(day=3).isoformat(),
            "location": "Chapel",
            "is_active": True,
            "visibility": "internal",
            "ministry_id": ministry["id"],
        },
    )
    assert min_ev.status_code == 201

    # Ministry-linked inactive (not visible).
    old = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Old Prayer Meeting",
            "event_type": "meeting",
            "start_at": start.replace(day=4).isoformat(),
            "end_at": end.replace(day=4).isoformat(),
            "location": "Chapel",
            "is_active": False,
            "visibility": "internal",
            "ministry_id": ministry["id"],
        },
    )
    assert old.status_code == 201

    member_tok = member["access_token"]
    r = await client.get(
        "/api/v1/events/me",
        headers={"Authorization": f"Bearer {member_tok}"},
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    names = {i["title"] for i in items}

    assert "Sunday Service" in names
    assert "Internal Retreat Info" in names
    assert "Prayer Meeting" in names
    assert "Old Prayer Meeting" not in names

@pytest.mark.asyncio
async def test_member_view_event_access_control(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "m1@example.com", "M1")
    outsider = await _register(client, "m2@example.com", "M2")

    await _register(client, "admin6@example.com")
    await _promote_to_admin(session_factory, "admin6@example.com")
    admin_tok = await _login(client, "admin6@example.com")

    ministry = await _create_ministry(client, admin_tok, name="Ministry A")
    await client.post(
        f"/api/v1/ministries/{ministry['id']}/members",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "role_in_ministry": "member"},
    )

    start = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Ministry Event",
            "event_type": "meeting",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Room",
            "is_active": True,
            "visibility": "internal",
            "ministry_id": ministry["id"],
        },
    )
    assert ev.status_code == 201
    event_id = ev.json()["event_id"]

    # Member can view.
    r1 = await client.get(
        f"/api/v1/events/{event_id}/view",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert r1.status_code == 200

    # Outsider cannot.
    r2 = await client.get(
        f"/api/v1/events/{event_id}/view",
        headers={"Authorization": f"Bearer {outsider['access_token']}"},
    )
    assert r2.status_code in (403, 404)

