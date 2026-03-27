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


async def _create_event(
    client: AsyncClient,
    admin_token: str,
    *,
    title: str = "Sunday Service",
    ministry_id: str | None = None,
    is_active: bool = True,
) -> dict:
    start = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc)
    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": title,
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Main Church",
            "is_active": is_active,
            "visibility": "public" if ministry_id is None else "internal",
            "ministry_id": ministry_id,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _create_ministry(client: AsyncClient, admin_token: str, name: str = "Youth") -> dict:
    r = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "description": "test", "is_active": True},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_admin_can_create_attendance(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member1@example.com")
    await _register(client, "admin1@example.com")
    await _promote_to_admin(session_factory, "admin1@example.com")
    admin_tok = await _login(client, "admin1@example.com")

    event = await _create_event(client, admin_tok)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "present"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "present"
    assert body["user_id"] == member["user"]["id"]


@pytest.mark.asyncio
async def test_admin_can_update_attendance(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member2@example.com")
    await _register(client, "admin2@example.com")
    await _promote_to_admin(session_factory, "admin2@example.com")
    admin_tok = await _login(client, "admin2@example.com")

    event = await _create_event(client, admin_tok)
    create = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "absent"},
    )
    assert create.status_code == 201

    patch = await client.patch(
        f"/api/v1/events/{event['event_id']}/attendance/{member['user']['id']}",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"status": "excused"},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["status"] == "excused"


@pytest.mark.asyncio
async def test_duplicate_attendance_is_prevented(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member3@example.com")
    await _register(client, "admin3@example.com")
    await _promote_to_admin(session_factory, "admin3@example.com")
    admin_tok = await _login(client, "admin3@example.com")
    event = await _create_event(client, admin_tok)

    r1 = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "present"},
    )
    assert r1.status_code == 201

    r2 = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "absent"},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_inactive_event_attendance_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member4@example.com")
    await _register(client, "admin4@example.com")
    await _promote_to_admin(session_factory, "admin4@example.com")
    admin_tok = await _login(client, "admin4@example.com")
    event = await _create_event(client, admin_tok, is_active=False)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "present"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_create_or_update_attendance(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "member5@example.com")
    member_tok = reg["access_token"]
    await _register(client, "admin5@example.com")
    await _promote_to_admin(session_factory, "admin5@example.com")
    admin_tok = await _login(client, "admin5@example.com")
    event = await _create_event(client, admin_tok)

    create = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {member_tok}"},
        json={"user_id": reg["user"]["id"], "status": "present"},
    )
    assert create.status_code == 403

    patch = await client.patch(
        f"/api/v1/events/{event['event_id']}/attendance/{reg['user']['id']}",
        headers={"Authorization": f"Bearer {member_tok}"},
        json={"status": "absent"},
    )
    assert patch.status_code == 403


@pytest.mark.asyncio
async def test_ministry_linked_event_rejects_non_member_attendance_target(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    outsider = await _register(client, "outsider@example.com")
    await _register(client, "admin6@example.com")
    await _promote_to_admin(session_factory, "admin6@example.com")
    admin_tok = await _login(client, "admin6@example.com")

    ministry = await _create_ministry(client, admin_tok, "Choir")
    event = await _create_event(
        client,
        admin_tok,
        title="Choir Rehearsal",
        ministry_id=ministry["id"],
    )

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": outsider["user"]["id"], "status": "present"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_member_can_view_own_attendance_for_visible_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member7@example.com")
    await _register(client, "admin7@example.com")
    await _promote_to_admin(session_factory, "admin7@example.com")
    admin_tok = await _login(client, "admin7@example.com")

    event = await _create_event(client, admin_tok, title="Public Service")
    await client.post(
        f"/api/v1/events/{event['event_id']}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member["user"]["id"], "status": "present"},
    )

    r = await client.get(
        f"/api/v1/events/{event['event_id']}/attendance/me",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recorded"] is True
    assert body["status"] == "present"


@pytest.mark.asyncio
async def test_member_cannot_view_attendance_for_inaccessible_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "member8@example.com")
    await _register(client, "admin8@example.com")
    await _promote_to_admin(session_factory, "admin8@example.com")
    admin_tok = await _login(client, "admin8@example.com")

    ministry = await _create_ministry(client, admin_tok, "Council")
    event = await _create_event(
        client,
        admin_tok,
        title="Council Internal",
        ministry_id=ministry["id"],
    )

    r = await client.get(
        f"/api/v1/events/{event['event_id']}/attendance/me",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert r.status_code == 404

