from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone

from app.db.models.enums import RegistryAgeGroup
from app.modules.church_registry.registry_age import dob_inclusive_range_for_age_group, stats_reference_date

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


def _parse_csv(content: bytes) -> tuple[list[str], list[list[str]]]:
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    assert rows
    return rows[0], rows[1:]


@pytest.mark.asyncio
async def test_exports_forbidden_for_non_admin(client: AsyncClient, session_factory: async_sessionmaker) -> None:
    await _register(client, "ex_member@example.com")
    tok = await _login(client, "ex_member@example.com")
    h = {"Authorization": f"Bearer {tok}"}
    for path in (
        "/api/v1/exports/attendance.csv",
        "/api/v1/exports/attendance/print",
        "/api/v1/exports/volunteers.csv",
        "/api/v1/exports/users.csv",
        "/api/v1/exports/parish-registry.csv",
    ):
        r = await client.get(path, headers=h)
        assert r.status_code == 403, path


@pytest.mark.asyncio
async def test_users_csv_and_print_use_app_user_columns(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "ex_user_csv@example.com", "CSV User")
    await _register(client, "ex_admin_u@example.com")
    await _promote_to_admin(session_factory, "ex_admin_u@example.com")
    admin_tok = await _login(client, "ex_admin_u@example.com")

    r = await client.get(
        "/api/v1/exports/users.csv",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "attachment" in r.headers.get("content-disposition", "")
    hdr, data = _parse_csv(r.content)
    assert "Login email" in hdr
    assert "Role" in hdr
    row_for_user = next((row for row in data if "ex_user_csv@example.com" in row), None)
    assert row_for_user is not None

    pr = await client.get(
        "/api/v1/exports/users/print",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert pr.status_code == 200
    body = pr.json()
    assert body["title"] == "App users export"
    assert "Login email" in body["columns"]
    assert any("ex_user_csv@example.com" in (x or "") for x in sum(body["rows"], []))


@pytest.mark.asyncio
async def test_users_csv_filter_active_and_role(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ex_active@example.com")
    await _register(client, "ex_admin_f@example.com")
    await _promote_to_admin(session_factory, "ex_admin_f@example.com")
    admin_tok = await _login(client, "ex_admin_f@example.com")

    r = await client.get(
        "/api/v1/exports/users.csv",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"is_active": "true", "role": "member"},
    )
    assert r.status_code == 200
    hdr, data = _parse_csv(r.content)
    role_i = hdr.index("Role")
    email_i = hdr.index("Login email")
    assert any(row[email_i] == "ex_active@example.com" for row in data)
    assert all(row[role_i] == "member" for row in data)


@pytest.mark.asyncio
async def test_parish_registry_csv_uses_registry_fields_only(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ex_admin_pr@example.com")
    await _promote_to_admin(session_factory, "ex_admin_pr@example.com")
    admin_tok = await _login(client, "ex_admin_pr@example.com")

    cr = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "first_name": "Registry",
            "last_name": "Only",
            "registration_number": "2026-0001",
            "gender": "male",
        },
    )
    assert cr.status_code == 201, cr.text

    r = await client.get(
        "/api/v1/exports/parish-registry.csv",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"gender": "male"},
    )
    assert r.status_code == 200
    hdr, data = _parse_csv(r.content)
    assert "Registration number" in hdr
    assert "Full name" in hdr
    assert "Login email" not in hdr
    flat = "\n".join(",".join(row) for row in data)
    assert "Registry" in flat and "Only" in flat

    pr = await client.get(
        "/api/v1/exports/parish-registry/print",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"membership_status": "active"},
    )
    assert pr.status_code == 200
    assert pr.json()["title"] == "Parish registry export"


@pytest.mark.asyncio
async def test_parish_registry_csv_respects_age_group_filter(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ex_admin_age@example.com")
    await _promote_to_admin(session_factory, "ex_admin_age@example.com")
    admin_tok = await _login(client, "ex_admin_age@example.com")
    h = {"Authorization": f"Bearer {admin_tok}"}

    ref = stats_reference_date()
    c_lo, c_hi = dob_inclusive_range_for_age_group(RegistryAgeGroup.CHILD, ref)
    assert c_lo is not None and c_hi is not None
    child_dob = c_lo + timedelta(days=max(1, (c_hi - c_lo).days // 2))

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Export",
            "last_name": "AgeChild",
            "gender": "male",
            "date_of_birth": child_dob.isoformat(),
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Export", "last_name": "NoDob", "gender": "female"},
    )

    r = await client.get(
        "/api/v1/exports/parish-registry.csv",
        headers=h,
        params={"age_group": "child"},
    )
    assert r.status_code == 200
    _, data = _parse_csv(r.content)
    flat = "\n".join(",".join(row) for row in data)
    assert "AgeChild" in flat
    assert "NoDob" not in flat


@pytest.mark.asyncio
async def test_parish_registry_csv_and_print_respect_sacramental_date_filters(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ex_admin_sac@example.com")
    await _promote_to_admin(session_factory, "ex_admin_sac@example.com")
    admin_tok = await _login(client, "ex_admin_sac@example.com")
    h = {"Authorization": f"Bearer {admin_tok}"}

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Sac",
            "last_name": "CsvBaptism",
            "is_baptized": True,
            "baptism_date": "2021-05-20",
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Sac",
            "last_name": "CsvOtherYear",
            "is_baptized": True,
            "baptism_date": "2015-01-01",
        },
    )

    r = await client.get(
        "/api/v1/exports/parish-registry.csv",
        headers=h,
        params={
            "baptism_date_from": "2021-01-01",
            "baptism_date_to": "2021-12-31",
        },
    )
    assert r.status_code == 200
    _, data = _parse_csv(r.content)
    flat = "\n".join(",".join(row) for row in data)
    assert "CsvBaptism" in flat
    assert "CsvOtherYear" not in flat

    pr = await client.get(
        "/api/v1/exports/parish-registry/print",
        headers=h,
        params={
            "baptism_date_from": "2021-01-01",
            "baptism_date_to": "2021-12-31",
        },
    )
    assert pr.status_code == 200
    body = pr.json()
    assert body["title"] == "Parish registry export"
    fs = body.get("filters_summary") or ""
    assert "baptism date from: 2021-01-01" in fs.lower()
    assert "baptism date to: 2021-12-31" in fs.lower()
    flatp = "\n".join(",".join(x or "" for x in row) for row in body["rows"])
    assert "CsvBaptism" in flatp
    assert "CsvOtherYear" not in flatp


@pytest.mark.asyncio
async def test_parish_registry_csv_and_print_respect_first_communion_date_filters(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "ex_admin_fc@example.com")
    await _promote_to_admin(session_factory, "ex_admin_fc@example.com")
    admin_tok = await _login(client, "ex_admin_fc@example.com")
    h = {"Authorization": f"Bearer {admin_tok}"}

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Fc",
            "last_name": "InRange",
            "is_communicant": True,
            "first_communion_date": "2018-06-10",
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Fc",
            "last_name": "OutOfRange",
            "is_communicant": True,
            "first_communion_date": "2005-01-01",
        },
    )

    r = await client.get(
        "/api/v1/exports/parish-registry.csv",
        headers=h,
        params={
            "first_communion_date_from": "2018-01-01",
            "first_communion_date_to": "2018-12-31",
        },
    )
    assert r.status_code == 200
    _, data = _parse_csv(r.content)
    flat = "\n".join(",".join(row) for row in data)
    assert "InRange" in flat
    assert "OutOfRange" not in flat

    pr = await client.get(
        "/api/v1/exports/parish-registry/print",
        headers=h,
        params={
            "first_communion_date_from": "2018-01-01",
            "first_communion_date_to": "2018-12-31",
        },
    )
    assert pr.status_code == 200
    body = pr.json()
    fs = body.get("filters_summary") or ""
    assert "first communion date from: 2018-01-01" in fs.lower()
    assert "first communion date to: 2018-12-31" in fs.lower()
    flatp = "\n".join(",".join(x or "" for x in row) for row in body["rows"])
    assert "InRange" in flatp
    assert "OutOfRange" not in flatp


@pytest.mark.asyncio
async def test_attendance_and_volunteer_exports_filtered_by_event(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    member = await _register(client, "ex_att@example.com")
    await _register(client, "ex_admin_av@example.com")
    await _promote_to_admin(session_factory, "ex_admin_av@example.com")
    admin_tok = await _login(client, "ex_admin_av@example.com")
    mid = member["user"]["id"]

    now = datetime.now(timezone.utc)
    start = now + timedelta(days=20)
    end = start + timedelta(hours=1)
    ev = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={
            "title": "Export Event",
            "event_type": "service",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location": "Hall",
            "is_active": True,
            "visibility": "public",
        },
    )
    assert ev.status_code == 201, ev.text
    eid = ev.json()["event_id"]

    att = await client.post(
        f"/api/v1/events/{eid}/attendance",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": mid, "status": "present"},
    )
    assert att.status_code == 201, att.text

    role = await client.post(
        "/api/v1/volunteers/roles",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"name": "Export Role", "description": "x", "is_active": True},
    )
    assert role.status_code == 201, role.text
    rid = role.json()["id"]

    vol = await client.post(
        f"/api/v1/events/{eid}/volunteers",
        headers={"Authorization": f"Bearer {admin_tok}"},
        json={"user_id": mid, "role_id": rid},
    )
    assert vol.status_code == 201, vol.text

    ac = await client.get(
        "/api/v1/exports/attendance.csv",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"event_id": eid},
    )
    assert ac.status_code == 200
    _, arows = _parse_csv(ac.content)
    assert len(arows) >= 1
    assert any("Export Event" in cell for row in arows for cell in row)
    assert any("present" in cell for row in arows for cell in row)

    ap = await client.get(
        "/api/v1/exports/attendance/print",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"event_id": eid},
    )
    assert ap.status_code == 200
    assert ap.json()["rows"]

    vc = await client.get(
        "/api/v1/exports/volunteers.csv",
        headers={"Authorization": f"Bearer {admin_tok}"},
        params={"event_id": eid},
    )
    assert vc.status_code == 200
    _, vrows = _parse_csv(vc.content)
    assert len(vrows) >= 1
    assert any("Export Role" in cell for row in vrows for cell in row)
