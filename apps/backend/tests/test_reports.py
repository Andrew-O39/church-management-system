from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


async def _register(client: AsyncClient, email: str, name: str = "User") -> dict:
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
async def test_reports_endpoints_forbidden_for_non_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "reports_member@example.com")
    tok = await _login(client, "reports_member@example.com")
    headers = {"Authorization": f"Bearer {tok}"}
    for path in (
        "/api/v1/reports/dashboard",
        "/api/v1/reports/attendance",
        "/api/v1/reports/volunteers",
        "/api/v1/reports/notifications",
    ):
        r = await client.get(path, headers=headers)
        assert r.status_code == 403, path


@pytest.mark.asyncio
async def test_dashboard_summary_ok_for_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "reports_admin_dash@example.com")
    await _promote_to_admin(session_factory, "reports_admin_dash@example.com")
    tok = await _login(client, "reports_admin_dash@example.com")
    r = await client.get(
        "/api/v1/reports/dashboard",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total_users"] >= 1
    assert "active_users_last_30_days" in d
    assert d["total_ministries"] >= 0
    assert d["active_ministries"] >= 0
    assert d["upcoming_events_count"] >= 0
    assert d["events_this_week"] >= 0
    assert d["volunteers_assigned_upcoming"] >= 0
    assert d["unread_notifications_total"] >= 0


@pytest.mark.asyncio
async def test_attendance_and_volunteer_reports_with_seed_data(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "reports_member2@example.com")
    await _register(client, "reports_admin2@example.com")
    await _promote_to_admin(session_factory, "reports_admin2@example.com")
    admin_tok = await _login(client, "reports_admin2@example.com")
    member_id = member["user"]["id"]

    now = datetime.now(timezone.utc)
    start = now + timedelta(days=14)
    end = start + timedelta(hours=2)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Report Test Event",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Hall",
            "is_active": True,
            "visibility": "public",
        },
    )
    assert ev.status_code == 201, ev.text
    event_id = ev.json()["event_id"]

    att = await client.post(
        f"/api/v1/events/{event_id}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member_id, "status": "present"},
    )
    assert att.status_code == 201, att.text

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"name": "Reports Role", "description": "r", "is_active": True},
    )
    assert role.status_code == 201, role.text
    role_id = role.json()["id"]

    vol = await client.post(
        f"/api/v1/events/{event_id}/volunteers",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": member_id, "role_id": role_id},
    )
    assert vol.status_code == 201, vol.text

    r_att = await client.get(
        "/api/v1/reports/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r_att.status_code == 200, r_att.text
    items = r_att.json()["items"]
    assert len(items) >= 1
    match = next((i for i in items if i["event_id"] == event_id), None)
    assert match is not None
    assert match["attendance_count"] == 1
    assert match["event_title"] == "Report Test Event"

    r_vol = await client.get(
        "/api/v1/reports/volunteers",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r_vol.status_code == 200, r_vol.text
    vitems = r_vol.json()["items"]
    assert len(vitems) >= 1
    top = vitems[0]
    assert top["user_id"] == member_id
    assert top["assignments_count"] >= 1

    dash = await client.get(
        "/api/v1/reports/dashboard",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert dash.status_code == 200
    dd = dash.json()
    assert dd["upcoming_events_count"] >= 1
    assert dd["volunteers_assigned_upcoming"] >= 1


@pytest.mark.asyncio
async def test_notification_insights_reflect_delivery_attempts(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    u1 = await _register(client, "reports_n1@example.com")
    await _register(client, "reports_admin_n@example.com")
    await _promote_to_admin(session_factory, "reports_admin_n@example.com")
    admin_tok = await _login(client, "reports_admin_n@example.com")

    r = await client.post(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Insight",
            "body": "Body",
            "category": "general",
            "channels": ["in_app", "sms"],
            "audience_type": "direct_users",
            "user_ids": [u1["user"]["id"]],
        },
    )
    assert r.status_code == 201, r.text

    ins = await client.get(
        "/api/v1/reports/notifications",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert ins.status_code == 200, ins.text
    n = ins.json()
    assert n["total_notifications_sent"] >= 1
    assert n["total_recipients"] >= 1
    assert n["in_app_delivered"] >= 1
    assert n["sms_attempted"] >= 0
