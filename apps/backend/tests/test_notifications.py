from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.enums import UserRole
from app.modules.auth import service as auth_service
from app.modules.notifications.providers.base import SMSDeliveryResult


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


async def _create_event(client: AsyncClient, admin_token: str) -> dict:
    start = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc)
    r = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Sunday Service",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Main Church",
            "is_active": True,
            "visibility": "public",
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


async def _create_role(client: AsyncClient, admin_token: str, name: str = "Usher") -> dict:
    r = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": name, "description": "Help", "is_active": True},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _notif_payload_direct(
    user_ids: list[str],
    dup: bool = False,
    *,
    channels: list[str] | None = None,
) -> dict:
    ids = list(user_ids)
    if dup and ids:
        ids = ids + [ids[0]]
    return {
        "title": " Hello ",
        "body": " Test body ",
        "category": "general",
        "channels": channels or ["in_app"],
        "audience_type": "direct_users",
        "user_ids": ids,
    }


async def _set_profile_phone(client: AsyncClient, token: str, phone: str) -> None:
    r = await client.patch(
        "/api/v1/members/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"phone_number": phone},
    )
    assert r.status_code == 200, r.text


@pytest.fixture
def mock_sms_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _send(*, to_e164: str, body: str) -> SMSDeliveryResult:
        _ = body
        return SMSDeliveryResult(ok=True, provider_message_id=f"SM_{to_e164[-4:]}")

    monkeypatch.setattr("app.modules.notifications.service.send_sms_twilio", _send)


@pytest.fixture
def mock_sms_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _send(*, to_e164: str, body: str) -> SMSDeliveryResult:
        _ = (to_e164, body)
        return SMSDeliveryResult(ok=False, error_message="provider rejected")

    monkeypatch.setattr("app.modules.notifications.service.send_sms_twilio", _send)


@pytest.mark.asyncio
async def test_direct_user_notification_send(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "dir1@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_d1@example.com")
    await _promote_to_admin(session_factory, "adm_d1@example.com")
    tok = await _login(client, "adm_d1@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json=_notif_payload_direct([uid]),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Hello"
    assert body["body"] == "Test body"
    assert len(body["recipients"]) == 1
    assert body["recipients"][0]["user_id"] == uid
    assert body["channels"] == ["in_app"]
    assert len(body["recipients"][0]["delivery_attempts"]) == 1
    assert body["recipients"][0]["delivery_attempts"][0]["channel"] == "in_app"


@pytest.mark.asyncio
async def test_duplicate_recipient_deduped(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "dedup@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_dedup@example.com")
    await _promote_to_admin(session_factory, "adm_dedup@example.com")
    tok = await _login(client, "adm_dedup@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json=_notif_payload_direct([uid], dup=True),
    )
    assert r.status_code == 201, r.text
    assert len(r.json()["recipients"]) == 1


@pytest.mark.asyncio
async def test_ministry_member_notification_send(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "minmem@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_min@example.com")
    await _promote_to_admin(session_factory, "adm_min@example.com")
    tok = await _login(client, "adm_min@example.com")

    ministry = await _create_ministry(client, tok, "Choir")
    mid = ministry["id"]
    await _add_ministry_member(client, tok, mid, uid)

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Choir note",
            "body": "Practice moved",
            "category": "ministry",
            "channels": ["in_app"],
            "audience_type": "ministry_members",
            "ministry_id": mid,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["related_ministry_id"] == mid
    assert len(body["recipients"]) == 1
    assert body["recipients"][0]["user_id"] == uid


@pytest.mark.asyncio
async def test_event_volunteer_notification_send(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "vol@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_vol@example.com")
    await _promote_to_admin(session_factory, "adm_vol@example.com")
    tok = await _login(client, "adm_vol@example.com")

    event = await _create_event(client, tok)
    eid = event["event_id"]
    role = await _create_role(client, tok, "Greeter")
    await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "Volunteer reminder",
            "body": "Please arrive early",
            "category": "volunteer",
            "channels": ["in_app"],
            "audience_type": "event_volunteers",
            "event_id": eid,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["related_event_id"] == eid
    assert len(body["recipients"]) == 1


@pytest.mark.asyncio
async def test_empty_audience_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "adm_empty@example.com")
    await _promote_to_admin(session_factory, "adm_empty@example.com")
    tok = await _login(client, "adm_empty@example.com")

    ministry = await _create_ministry(client, tok, "EmptyMin")
    mid = ministry["id"]

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "title": "No one",
            "body": "Should fail",
            "category": "general",
            "channels": ["in_app"],
            "audience_type": "ministry_members",
            "ministry_id": mid,
        },
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_user_lists_own_notifications_unread_mark_read(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "inbox@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_inbox@example.com")
    await _promote_to_admin(session_factory, "adm_inbox@example.com")
    adm_tok = await _login(client, "adm_inbox@example.com")
    user_tok = await _login(client, "inbox@example.com")

    r0 = await client.get(
        "/api/v1/notifications/me/unread-count",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert r0.status_code == 200
    assert r0.json()["unread_count"] == 0

    cr = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid]),
    )
    assert cr.status_code == 201, cr.text
    nid = cr.json()["id"]

    r1 = await client.get(
        "/api/v1/notifications/me/unread-count",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert r1.json()["unread_count"] == 1

    me_list = await client.get(
        "/api/v1/notifications/me",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert me_list.status_code == 200
    items = me_list.json()["items"]
    assert len(items) == 1
    assert items[0]["notification_id"] == nid

    mr = await client.patch(
        f"/api/v1/notifications/{nid}/read",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert mr.status_code == 200
    assert mr.json()["status"] == "read"

    r2 = await client.get(
        "/api/v1/notifications/me/unread-count",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert r2.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "mall@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_mall@example.com")
    await _promote_to_admin(session_factory, "adm_mall@example.com")
    adm_tok = await _login(client, "adm_mall@example.com")
    user_tok = await _login(client, "mall@example.com")

    for i in range(2):
        r = await client.post(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {adm_tok}"},
            json={
                "title": f"N{i}",
                "body": "x",
                "category": "general",
                "channels": ["in_app"],
                "audience_type": "direct_users",
                "user_ids": [uid],
            },
        )
        assert r.status_code == 201, r.text

    assert (
        await client.get(
            "/api/v1/notifications/me/unread-count",
            headers={"Authorization": f"Bearer {user_tok}"},
        )
    ).json()["unread_count"] == 2

    mar = await client.patch(
        "/api/v1/notifications/read-all",
        headers={"Authorization": f"Bearer {user_tok}"},
    )
    assert mar.status_code == 200
    assert mar.json()["updated"] == 2

    assert (
        await client.get(
            "/api/v1/notifications/me/unread-count",
            headers={"Authorization": f"Bearer {user_tok}"},
        )
    ).json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_non_admin_cannot_create_notification(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "mem_only@example.com")
    uid = m["user"]["id"]
    tok = await _login(client, "mem_only@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
        json=_notif_payload_direct([uid]),
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_member_cannot_list_admin_notifications(
    client: AsyncClient,
) -> None:
    await _register(client, "mem_list@example.com")
    tok = await _login(client, "mem_list@example.com")

    r = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_sms_direct_users(
    mock_sms_ok: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "smsdir@example.com")
    uid = m["user"]["id"]
    mem_tok = await _login(client, "smsdir@example.com")
    await _set_profile_phone(client, mem_tok, "+15551234567")
    await _register(client, "adm_sms1@example.com")
    await _promote_to_admin(session_factory, "adm_sms1@example.com")
    adm_tok = await _login(client, "adm_sms1@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["sms"]),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["channels"] == ["sms"]
    assert body["delivery_summary"]["sms_sent"] == 1
    attempts = body["recipients"][0]["delivery_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["channel"] == "sms"
    assert attempts[0]["status"] == "sent"


@pytest.mark.asyncio
async def test_sms_ministry_members(
    mock_sms_ok: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "smsmin@example.com")
    uid = m["user"]["id"]
    mem_tok = await _login(client, "smsmin@example.com")
    await _set_profile_phone(client, mem_tok, "+15557654321")
    await _register(client, "adm_smsmin@example.com")
    await _promote_to_admin(session_factory, "adm_smsmin@example.com")
    adm_tok = await _login(client, "adm_smsmin@example.com")
    ministry = await _create_ministry(client, adm_tok, "SMS Ministry")
    mid = ministry["id"]
    await _add_ministry_member(client, adm_tok, mid, uid)

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json={
            "title": "M",
            "body": "B",
            "category": "ministry",
            "channels": ["sms"],
            "audience_type": "ministry_members",
            "ministry_id": mid,
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["delivery_summary"]["sms_sent"] == 1


@pytest.mark.asyncio
async def test_sms_event_volunteers(
    mock_sms_ok: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "smsvol@example.com")
    uid = m["user"]["id"]
    mem_tok = await _login(client, "smsvol@example.com")
    await _set_profile_phone(client, mem_tok, "+15559876543")
    await _register(client, "adm_smsvol@example.com")
    await _promote_to_admin(session_factory, "adm_smsvol@example.com")
    adm_tok = await _login(client, "adm_smsvol@example.com")
    event = await _create_event(client, adm_tok)
    eid = event["event_id"]
    role = await _create_role(client, adm_tok)
    await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json={"user_id": uid, "role_id": role["id"]},
    )
    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json={
            "title": "V",
            "body": "B",
            "category": "volunteer",
            "channels": ["sms"],
            "audience_type": "event_volunteers",
            "event_id": eid,
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["delivery_summary"]["sms_sent"] == 1


@pytest.mark.asyncio
async def test_sms_only_all_missing_phone_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "nosms@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_nosms@example.com")
    await _promote_to_admin(session_factory, "adm_nosms@example.com")
    adm_tok = await _login(client, "adm_nosms@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["sms"]),
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_in_app_and_sms_partial_no_phone_skipped(
    mock_sms_ok: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "partial@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_part@example.com")
    await _promote_to_admin(session_factory, "adm_part@example.com")
    adm_tok = await _login(client, "adm_part@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["in_app", "sms"]),
    )
    assert r.status_code == 201, r.text
    summary = r.json()["delivery_summary"]
    assert summary["sms_skipped_no_phone"] == 1
    assert summary["sms_sent"] == 0


@pytest.mark.asyncio
async def test_whatsapp_not_implemented(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "wa@example.com")
    uid = m["user"]["id"]
    await _register(client, "adm_wa@example.com")
    await _promote_to_admin(session_factory, "adm_wa@example.com")
    adm_tok = await _login(client, "adm_wa@example.com")
    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["whatsapp"]),
    )
    assert r.status_code == 501, r.text


@pytest.mark.asyncio
async def test_sms_provider_failure_recorded(
    mock_sms_fail: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "fail@example.com")
    uid = m["user"]["id"]
    mem_tok = await _login(client, "fail@example.com")
    await _set_profile_phone(client, mem_tok, "+15551112222")
    await _register(client, "adm_fail@example.com")
    await _promote_to_admin(session_factory, "adm_fail@example.com")
    adm_tok = await _login(client, "adm_fail@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["sms"]),
    )
    assert r.status_code == 201, r.text
    summary = r.json()["delivery_summary"]
    assert summary["sms_failed"] == 1
    assert summary["sms_sent"] == 0
    sms_att = [
        a
        for a in r.json()["recipients"][0]["delivery_attempts"]
        if a["channel"] == "sms"
    ]
    assert sms_att[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_sms_only_excluded_from_inbox(
    mock_sms_ok: None,
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    m = await _register(client, "smsonly@example.com")
    uid = m["user"]["id"]
    mem_tok = await _login(client, "smsonly@example.com")
    await _set_profile_phone(client, mem_tok, "+15553334444")
    await _register(client, "adm_smsonly@example.com")
    await _promote_to_admin(session_factory, "adm_smsonly@example.com")
    adm_tok = await _login(client, "adm_smsonly@example.com")

    await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {adm_tok}"},
        json=_notif_payload_direct([uid], channels=["sms"]),
    )
    me = await client.get(
        "/api/v1/notifications/me",
        headers={"Authorization": f"Bearer {mem_tok}"},
    )
    assert me.status_code == 200
    assert me.json()["items"] == []
