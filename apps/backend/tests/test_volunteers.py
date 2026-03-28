from __future__ import annotations

import uuid
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


async def _add_ministry_member(
    client: AsyncClient,
    admin_token: str,
    ministry_id: str,
    user_id: str,
) -> None:
    r = await client.post(
        f"/api/v1/ministries/{ministry_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": user_id, "role_in_ministry": "member"},
    )
    assert r.status_code == 201, r.text


async def _create_role(
    client: AsyncClient,
    admin_token: str,
    *,
    name: str = "Usher",
    ministry_id: str | None = None,
    is_active: bool = True,
) -> dict:
    r = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "description": "Help", "ministry_id": ministry_id, "is_active": is_active},
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_admin_create_and_update_volunteer_role(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm@example.com")
    await _promote_to_admin(session_factory, "adm@example.com")
    tok = await _login(client, "adm@example.com")

    r = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Lector", "description": "Reads", "is_active": True},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Lector"
    role_id = body["id"]

    r2 = await client.patch(
        f"/api/v1/volunteers/roles/{role_id}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"description": "Updated"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_assign_volunteer_to_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    mreg = await _register(client, "mem@example.com")
    await _register(client, "adm2@example.com")
    await _promote_to_admin(session_factory, "adm2@example.com")
    tok = await _login(client, "adm2@example.com")

    role = await _create_role(client, tok, name="Greeter")
    event = await _create_event(client, tok)
    user_id = mreg["user"]["id"]

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": user_id, "role_id": role["id"], "notes": "Door A"},
    )
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["user_id"] == user_id
    assert row["notes"] == "Door A"

    r_list = await client.get(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r_list.status_code == 200
    assert len(r_list.json()["items"]) == 1


@pytest.mark.asyncio
async def test_duplicate_assignment_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "m2@example.com")
    await _register(client, "adm3@example.com")
    await _promote_to_admin(session_factory, "adm3@example.com")
    tok = await _login(client, "adm3@example.com")
    m2_tok = await _login(client, "m2@example.com")
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {m2_tok}"})
    uid = me.json()["id"]

    role = await _create_role(client, tok, name="Altar Server")
    event = await _create_event(client, tok)

    r1 = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_inactive_event_rejects_new_assignment(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "m3@example.com")
    await _register(client, "adm4@example.com")
    await _promote_to_admin(session_factory, "adm4@example.com")
    tok = await _login(client, "adm4@example.com")
    m3_tok = await _login(client, "m3@example.com")
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {m3_tok}"})
    uid = me.json()["id"]

    role = await _create_role(client, tok, name="Reader")
    event = await _create_event(client, tok, is_active=False)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_inactive_user_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "inactive@example.com")
    uid = reg["user"]["id"]

    await _register(client, "adm5@example.com")
    await _promote_to_admin(session_factory, "adm5@example.com")
    tok = await _login(client, "adm5@example.com")

    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uuid.UUID(uid))
        assert u is not None
        u.is_active = False
        await session.commit()

    role = await _create_role(client, tok, name="Hospitality")
    event = await _create_event(client, tok)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_inactive_role_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "m4@example.com")
    await _register(client, "adm6@example.com")
    await _promote_to_admin(session_factory, "adm6@example.com")
    tok = await _login(client, "adm6@example.com")
    m4_tok = await _login(client, "m4@example.com")
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {m4_tok}"})
    uid = me.json()["id"]

    role = await _create_role(client, tok, name="Choir", is_active=False)
    event = await _create_event(client, tok)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_assignments(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "m5@example.com")
    await _register(client, "adm7@example.com")
    await _promote_to_admin(session_factory, "adm7@example.com")
    admin_tok = await _login(client, "adm7@example.com")
    member_tok = await _login(client, "m5@example.com")
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {member_tok}"})
    uid = me.json()["id"]

    role = await _create_role(client, admin_tok, name="Media")
    event = await _create_event(client, admin_tok)

    r = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {member_tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_ministry_event_only_ministry_members_assignable(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    inside = await _register(client, "inside@example.com")
    await _register(client, "outside@example.com")
    await _register(client, "adm8@example.com")
    await _promote_to_admin(session_factory, "adm8@example.com")
    tok = await _login(client, "adm8@example.com")

    ministry = await _create_ministry(client, tok, name="Choir Ministry")
    await _add_ministry_member(client, tok, ministry["id"], inside["user"]["id"])

    out_tok = await _login(client, "outside@example.com")
    out_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {out_tok}"})
    out_uid = out_me.json()["id"]

    role = await _create_role(client, tok, name="Section Lead")
    event = await _create_event(client, tok, ministry_id=ministry["id"])

    r_bad = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": out_uid, "role_id": role["id"]},
    )
    assert r_bad.status_code == 400, r_bad.text

    r_ok = await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": inside["user"]["id"], "role_id": role["id"]},
    )
    assert r_ok.status_code == 201, r_ok.text


@pytest.mark.asyncio
async def test_ministry_scoped_role_must_match_event_ministry(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    mem = await _register(client, "vuser@example.com")
    await _register(client, "adm9@example.com")
    await _promote_to_admin(session_factory, "adm9@example.com")
    tok = await _login(client, "adm9@example.com")

    m_a = await _create_ministry(client, tok, name="Ministry A")
    m_b = await _create_ministry(client, tok, name="Ministry B")
    await _add_ministry_member(client, tok, m_a["id"], mem["user"]["id"])
    await _add_ministry_member(client, tok, m_b["id"], mem["user"]["id"])

    role_only_a = await _create_role(client, tok, name="Altar A", ministry_id=m_a["id"])
    event_on_b = await _create_event(client, tok, ministry_id=m_b["id"])

    r = await client.post(
        f"/api/v1/events/{event_on_b['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": mem["user"]["id"], "role_id": role_only_a["id"]},
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_member_sees_assignments_only_for_visible_events(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    insider = await _register(client, "insider@example.com")
    await _register(client, "outsider@example.com")
    await _register(client, "adm10@example.com")
    await _promote_to_admin(session_factory, "adm10@example.com")
    tok = await _login(client, "adm10@example.com")

    ministry = await _create_ministry(client, tok, name="Private Min")
    await _add_ministry_member(client, tok, ministry["id"], insider["user"]["id"])

    role = await _create_role(client, tok, name="Helper")
    pub_event = await _create_event(client, tok, title="Public Mass")
    min_event = await _create_event(client, tok, title="Choir Practice", ministry_id=ministry["id"])

    r_assign_pub = await client.post(
        f"/api/v1/events/{pub_event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": insider["user"]["id"], "role_id": role["id"]},
    )
    assert r_assign_pub.status_code == 201, r_assign_pub.text

    r_assign_min = await client.post(
        f"/api/v1/events/{min_event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": insider["user"]["id"], "role_id": role["id"]},
    )
    assert r_assign_min.status_code == 201, r_assign_min.text

    in_tok = await _login(client, "insider@example.com")
    r_me = await client.get(
        "/api/v1/volunteers/me",
        headers={"Authorization": f"Bearer {in_tok}"},
    )
    assert r_me.status_code == 200, r_me.text
    titles = {x["event_title"] for x in r_me.json()["items"]}
    assert "Public Mass" in titles
    assert "Choir Practice" in titles

    out_tok = await _login(client, "outsider@example.com")
    r_out = await client.get(
        "/api/v1/volunteers/me",
        headers={"Authorization": f"Bearer {out_tok}"},
    )
    assert r_out.status_code == 200, r_out.text
    out_titles = {x["event_title"] for x in r_out.json()["items"]}
    assert out_titles == set()

@pytest.mark.asyncio
async def test_member_event_volunteers_me_forbidden_when_event_invisible(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    inside = await _register(client, "invis@example.com")
    await _register(client, "outsider2@example.com")
    await _register(client, "adm11@example.com")
    await _promote_to_admin(session_factory, "adm11@example.com")
    tok = await _login(client, "adm11@example.com")

    ministry = await _create_ministry(client, tok, name="Closed")
    await _add_ministry_member(client, tok, ministry["id"], inside["user"]["id"])

    role = await _create_role(client, tok, name="Role X")
    event = await _create_event(client, tok, ministry_id=ministry["id"])
    await client.post(
        f"/api/v1/events/{event['event_id']}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": inside["user"]["id"], "role_id": role["id"]},
    )

    out_tok = await _login(client, "outsider2@example.com")

    r = await client.get(
        f"/api/v1/events/{event['event_id']}/volunteers/me",
        headers={"Authorization": f"Bearer {out_tok}"},
    )
    assert r.status_code == 403, r.text