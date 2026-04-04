from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import quote

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


async def _create_ministry(client: AsyncClient, admin_token: str, name: str = "Choir") -> dict:
    r = await client.post(
        "/api/v1/ministries/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "description": "test", "is_active": True},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _add_ministry_member(client: AsyncClient, admin_token: str, ministry_id: str, user_id: str) -> None:
    r = await client.post(
        f"/api/v1/ministries/{ministry_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": user_id, "role_in_ministry": "member"},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_create_list_patch_delete_reminder_rule(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm_er1@example.com")
    await _promote_to_admin(session_factory, "adm_er1@example.com")
    tok = await _login(client, "adm_er1@example.com")

    start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Test Event",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Sanctuary",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert ev.status_code == 201, ev.text
    eid = ev.json()["event_id"]

    cr = await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
            "is_active": True,
        },
    )
    assert cr.status_code == 201, cr.text
    rid = cr.json()["id"]

    ls = await client.get(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert ls.status_code == 200, ls.text
    assert len(ls.json()["items"]) == 1

    up = await client.patch(
        f"/api/v1/events/{eid}/reminders/{rid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"is_active": False, "title_override": "Custom"},
    )
    assert up.status_code == 200, up.text
    assert up.json()["is_active"] is False
    assert up.json()["title_override"] == "Custom"

    dl = await client.delete(
        f"/api/v1/events/{eid}/reminders/{rid}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert dl.status_code == 204

    ls2 = await client.get(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert len(ls2.json()["items"]) == 0


@pytest.mark.asyncio
async def test_duplicate_rule_conflict(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm_er2@example.com")
    await _promote_to_admin(session_factory, "adm_er2@example.com")
    tok = await _login(client, "adm_er2@example.com")

    start = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 2, 11, 0, tzinfo=timezone.utc)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Dup",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Hall",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 30,
        },
    )
    r2 = await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 30,
        },
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_ministry_audience_requires_event_ministry(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm_er3@example.com")
    await _promote_to_admin(session_factory, "adm_er3@example.com")
    tok = await _login(client, "adm_er3@example.com")

    start = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 3, 11, 0, tzinfo=timezone.utc)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "No min",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Hall",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    r = await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "ministry_members",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
        },
    )
    assert r.status_code == 400


@pytest.fixture
def mock_sms_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _send(*, to_e164: str, body: str):
        from app.modules.notifications.providers.base import SMSDeliveryResult

        _ = body
        return SMSDeliveryResult(ok=True, provider_message_id=f"SM_{to_e164[-4:]}")

    monkeypatch.setattr("app.modules.notifications.service.send_sms_twilio", _send)


@pytest.mark.asyncio
async def test_due_reminder_sends_notification(
    client: AsyncClient,
    session_factory: async_sessionmaker,
    mock_sms_ok: None,
) -> None:
    m = await _register(client, "vol_er@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_er4@example.com")
    await _promote_to_admin(session_factory, "adm_er4@example.com")
    tok = await _login(client, "adm_er4@example.com")

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Usher", "description": "Help", "is_active": True},
    )
    assert role.status_code == 201, role.text
    role_id = role.json()["id"]

    base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    start_at = base + timedelta(hours=2)
    end_at = start_at + timedelta(hours=1)

    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Reminder Event",
            "event_type": "service",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Main",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    assert ev.status_code == 201, ev.text
    eid = ev.json()["event_id"]

    va = await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role_id, "notes": None},
    )
    assert va.status_code == 201, va.text

    cr = await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
        },
    )
    assert cr.status_code == 201, cr.text

    as_of = base + timedelta(hours=1, minutes=1)
    run = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["reminders_sent"] >= 1
    assert body["rules_considered"] >= 1

    nlist = await client.get(
        "/api/v1/notifications/?page=1&page_size=20",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert nlist.status_code == 200
    titles = [x["title"] for x in nlist.json()["items"]]
    assert any("Reminder: Reminder Event" in t for t in titles)


@pytest.mark.asyncio
async def test_duplicate_job_does_not_resend(
    client: AsyncClient,
    session_factory: async_sessionmaker,
    mock_sms_ok: None,
) -> None:
    m = await _register(client, "vol_er2@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_er5@example.com")
    await _promote_to_admin(session_factory, "adm_er5@example.com")
    tok = await _login(client, "adm_er5@example.com")

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Greeter", "description": "Hi", "is_active": True},
    )
    role_id = role.json()["id"]

    base = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
    start_at = base + timedelta(hours=2)
    end_at = start_at + timedelta(hours=1)

    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Dedup Event",
            "event_type": "service",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Main",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role_id, "notes": None},
    )

    await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
        },
    )

    as_of = base + timedelta(hours=1, minutes=1)
    r1 = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r1.json()["reminders_sent"] == 1

    r2 = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r2.json()["reminders_sent"] == 0
    assert r2.json()["skipped_already_sent"] >= 1


@pytest.mark.asyncio
async def test_inactive_rule_not_sent(
    client: AsyncClient,
    session_factory: async_sessionmaker,
    mock_sms_ok: None,
) -> None:
    m = await _register(client, "vol_er3@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_er6@example.com")
    await _promote_to_admin(session_factory, "adm_er6@example.com")
    tok = await _login(client, "adm_er6@example.com")

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Reader", "description": "R", "is_active": True},
    )
    role_id = role.json()["id"]

    base = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    start_at = base + timedelta(hours=2)
    end_at = start_at + timedelta(hours=1)

    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Inactive rule",
            "event_type": "service",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Main",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role_id, "notes": None},
    )

    cr = await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
            "is_active": False,
        },
    )
    rid = cr.json()["id"]

    as_of = base + timedelta(hours=1, minutes=1)
    run = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run.json()["reminders_sent"] == 0
    assert run.json()["rules_considered"] == 0

    await client.patch(
        f"/api/v1/events/{eid}/reminders/{rid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={"is_active": True},
    )
    run2 = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run2.json()["reminders_sent"] == 1


@pytest.mark.asyncio
async def test_inactive_event_not_sent(
    client: AsyncClient,
    session_factory: async_sessionmaker,
    mock_sms_ok: None,
) -> None:
    m = await _register(client, "vol_er4@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_er7@example.com")
    await _promote_to_admin(session_factory, "adm_er7@example.com")
    tok = await _login(client, "adm_er7@example.com")

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {tok}"},
        json={"name": "Alt", "description": "A", "is_active": True},
    )
    role_id = role.json()["id"]

    base = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
    start_at = base + timedelta(hours=2)
    end_at = start_at + timedelta(hours=1)

    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Inactive ev",
            "event_type": "service",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Main",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role_id, "notes": None},
    )

    await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "event_volunteers",
            "channels": ["in_app"],
            "offset_minutes_before": 60,
        },
    )

    await client.patch(
        f"/api/v1/events/{eid}",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Inactive ev",
            "event_type": "service",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Main",
            "is_active": False,
            "visibility": "public",
            "ministry_id": None,
        },
    )

    as_of = base + timedelta(hours=1, minutes=1)
    run = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run.json()["reminders_sent"] == 0


@pytest.mark.asyncio
async def test_ministry_reminder_sends(
    client: AsyncClient,
    session_factory: async_sessionmaker,
    mock_sms_ok: None,
) -> None:
    m = await _register(client, "minmem_er@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_er8@example.com")
    await _promote_to_admin(session_factory, "adm_er8@example.com")
    tok = await _login(client, "adm_er8@example.com")

    ministry = await _create_ministry(client, tok, "Bell Choir")
    mid = ministry["id"]
    await _add_ministry_member(client, tok, mid, uid)

    base = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    start_at = base + timedelta(hours=3)
    end_at = start_at + timedelta(hours=1)

    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Ministry Event",
            "event_type": "rehearsal",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "location": "Chapel",
            "is_active": True,
            "visibility": "public",
            "ministry_id": mid,
        },
    )
    eid = ev.json()["event_id"]

    await client.post(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "audience_type": "ministry_members",
            "channels": ["in_app"],
            "offset_minutes_before": 120,
        },
    )

    as_of = base + timedelta(hours=1, minutes=1)
    run = await client.post(
        f"/api/v1/notifications/jobs/run-reminders?as_of={quote(as_of.isoformat())}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run.json()["reminders_sent"] == 1


@pytest.mark.asyncio
async def test_run_reminders_summary_non_admin_forbidden(client: AsyncClient) -> None:
    await _register(client, "mem_only@example.com")
    tok = await _login(client, "mem_only@example.com")
    r = await client.post(
        "/api/v1/notifications/jobs/run-reminders",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reminder_crud_non_admin_forbidden(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    await _register(client, "adm_er9@example.com")
    await _promote_to_admin(session_factory, "adm_er9@example.com")
    adm_tok = await _login(client, "adm_er9@example.com")

    start = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json={
            "title": "RBAC",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "X",
            "is_active": True,
            "visibility": "public",
            "ministry_id": None,
        },
    )
    eid = ev.json()["event_id"]

    await _register(client, "plain@example.com")
    mem_tok = await _login(client, "plain@example.com")

    r = await client.get(
        f"/api/v1/events/{eid}/reminders",
        headers={"Authorization": f"Bearer {mem_tok}"},
    )
    assert r.status_code == 403
