from __future__ import annotations

import uuid
from datetime import timedelta
import re

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from sqlalchemy import func, select

from app.db.models.church_member import ChurchMember
from app.db.models.enums import RegistryAgeGroup, UserRole
from app.modules.auth import service as auth_service
from app.modules.church_registry.registry_age import (
    dob_inclusive_range_for_age_group,
    stats_reference_date,
)


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
async def test_admin_create_church_member_without_user(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regadmin@example.com")
    await _promote_to_admin(session_factory, "regadmin@example.com")
    tok = await _login(client, "regadmin@example.com")

    r = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Child", "last_name": "NoLogin"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["full_name"]
    assert body["linked_user_id"] is None


@pytest.mark.asyncio
async def test_link_user_to_standalone_church_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "linktarget@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    await _register(client, "linkadmin@example.com")
    await _promote_to_admin(session_factory, "linkadmin@example.com")
    tok = await _login(client, "linkadmin@example.com")

    cr = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Adult", "last_name": "Offline"},
    )
    assert cr.status_code == 201, cr.text
    cm_id = cr.json()["id"]

    lr = await client.patch(
        f"/api/v1/church-members/{cm_id}/link-user",
        headers={"Authorization": f"Bearer {tok}"},
        json={"user_id": str(uid)},
    )
    assert lr.status_code == 200, lr.text
    assert lr.json()["linked_user_id"] == str(uid)

    got = await client.get(
        f"/api/v1/church-members/{cm_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert got.status_code == 200, got.text
    assert got.json()["linked_user_id"] == str(uid)
    assert got.json()["user_id"] == str(uid)


@pytest.mark.asyncio
async def test_register_does_not_create_church_member(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "noregistry@example.com", "No Registry Row")
    assert reg["user"]["member_id"] is None
    async with session_factory() as session:
        n = (await session.execute(select(func.count()).select_from(ChurchMember))).scalar_one()
        assert int(n) == 0


@pytest.mark.asyncio
async def test_get_my_church_member_profile_requires_registry_link(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "memprofile@example.com", "Patronus Member")
    tok = reg["access_token"]

    r = await client.get(
        "/api/v1/church-members/me",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_get_my_church_member_404_when_unlinked(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    reg = await _register(client, "unlinkedme@example.com")
    uid = uuid.UUID(reg["user"]["id"])
    async with session_factory() as session:
        u = await auth_service.get_user_by_id(session, uid)
        assert u is not None
        u.member_id = None
        await session.commit()

    r = await client.get(
        "/api/v1/church-members/me",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_duplicate_name_and_dob_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "dupadmin@example.com")
    await _promote_to_admin(session_factory, "dupadmin@example.com")
    tok = await _login(client, "dupadmin@example.com")
    common = {"first_name": "Sam", "last_name": "Same", "date_of_birth": "2010-05-01"}

    r1 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json=common,
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json=common,
    )
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_church_member_stats_shape(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "statsuser@example.com")
    await _promote_to_admin(session_factory, "statsuser@example.com")
    tok = await _login(client, "statsuser@example.com")

    r0 = await client.get(
        "/api/v1/church-members/stats",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r0.status_code == 200, r0.text
    s0 = r0.json()
    assert "total_members" in s0
    assert "members_with_accounts" in s0
    assert "members_without_accounts" in s0
    assert "gender_distribution" in s0
    assert "age_groups" in s0
    for key in (
        "male_members",
        "female_members",
        "inactive_members",
        "visitor_members",
        "transferred_members",
        "children_members",
        "young_adult_members",
        "adult_members",
        "baptized_members",
        "confirmed_members",
        "communicant_members",
        "married_members",
        "single_members",
    ):
        assert key in s0
    assert set(s0["age_groups"].keys()) >= {"child", "young_adult", "adult", "unknown"}
    before_total = s0["total_members"]

    await client.post(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
        json={"first_name": "Stats", "last_name": "Only"},
    )

    r1 = await client.get(
        "/api/v1/church-members/stats",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r1.status_code == 200, r1.text
    s1 = r1.json()
    assert s1["total_members"] == before_total + 1
    assert s1["members_without_accounts"] == s0["members_without_accounts"] + 1


@pytest.mark.asyncio
async def test_church_member_list_filters_age_group_and_sacraments(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "filteradmin@example.com")
    await _promote_to_admin(session_factory, "filteradmin@example.com")
    tok = await _login(client, "filteradmin@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    ref = stats_reference_date()
    c_lo, c_hi = dob_inclusive_range_for_age_group(RegistryAgeGroup.CHILD, ref)
    assert c_lo is not None and c_hi is not None
    child_dob = c_lo + timedelta(days=max(1, (c_hi - c_lo).days // 2))

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Filter",
            "last_name": "ChildMaleBap",
            "gender": "male",
            "date_of_birth": child_dob.isoformat(),
            "is_baptized": True,
            "is_confirmed": False,
            "is_communicant": False,
            "is_married": False,
        },
    )
    ya_lo, ya_hi = dob_inclusive_range_for_age_group(RegistryAgeGroup.YOUNG_ADULT, ref)
    assert ya_lo is not None and ya_hi is not None
    ya_dob = ya_lo + timedelta(days=max(1, (ya_hi - ya_lo).days // 2))
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Filter",
            "last_name": "YoungFemale",
            "gender": "female",
            "date_of_birth": ya_dob.isoformat(),
            "is_baptized": False,
            "is_confirmed": True,
            "is_communicant": True,
            "is_married": False,
        },
    )

    lr = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={"age_group": "child", "gender": "male", "is_baptized": "true", "page_size": 50},
    )
    assert lr.status_code == 200, lr.text
    names = {it["last_name"] for it in lr.json()["items"]}
    assert "ChildMaleBap" in names
    assert "YoungFemale" not in names

    lr2 = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={"age_group": "young_adult", "is_confirmed": "true", "page_size": 50},
    )
    assert lr2.status_code == 200, lr2.text
    names2 = {it["last_name"] for it in lr2.json()["items"]}
    assert "YoungFemale" in names2


@pytest.mark.asyncio
async def test_church_member_list_sacramental_date_ranges_and_boolean_combo(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "sacdateadmin@example.com")
    await _promote_to_admin(session_factory, "sacdateadmin@example.com")
    tok = await _login(client, "sacdateadmin@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Bap",
            "last_name": "In2023",
            "is_baptized": True,
            "baptism_date": "2023-06-15",
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Bap",
            "last_name": "NoDateButFlag",
            "is_baptized": True,
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Conf",
            "last_name": "Range2022",
            "is_confirmed": True,
            "confirmation_date": "2022-03-01",
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Wed",
            "last_name": "Married2024",
            "is_married": True,
            "marriage_date": "2024-01-10",
        },
    )

    b = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "baptism_date_from": "2023-01-01",
            "baptism_date_to": "2023-12-31",
            "page_size": 50,
        },
    )
    assert b.status_code == 200, b.text
    bn = {it["last_name"] for it in b.json()["items"]}
    assert "In2023" in bn
    assert "NoDateButFlag" not in bn

    c = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "confirmation_date_from": "2022-01-01",
            "confirmation_date_to": "2022-12-31",
            "page_size": 50,
        },
    )
    assert c.status_code == 200, c.text
    assert "Range2022" in {it["last_name"] for it in c.json()["items"]}

    m = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "marriage_date_from": "2024-01-01",
            "marriage_date_to": "2024-12-31",
            "page_size": 50,
        },
    )
    assert m.status_code == 200, m.text
    assert "Married2024" in {it["last_name"] for it in m.json()["items"]}

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Communion",
            "last_name": "Fc2019",
            "is_communicant": True,
            "first_communion_date": "2019-04-21",
        },
    )
    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Communion",
            "last_name": "FcNoDate",
            "is_communicant": True,
        },
    )
    fc = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "first_communion_date_from": "2019-01-01",
            "first_communion_date_to": "2019-12-31",
            "page_size": 50,
        },
    )
    assert fc.status_code == 200, fc.text
    fcn = {it["last_name"] for it in fc.json()["items"]}
    assert "Fc2019" in fcn
    assert "FcNoDate" not in fcn

    combo = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "is_baptized": "true",
            "baptism_date_from": "2024-01-01",
            "baptism_date_to": "2024-12-31",
            "page_size": 50,
        },
    )
    assert combo.status_code == 200, combo.text
    assert combo.json()["total"] == 0

    await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Bap",
            "last_name": "Combo2024",
            "is_baptized": True,
            "baptism_date": "2024-07-01",
        },
    )
    combo2 = await client.get(
        "/api/v1/church-members/",
        headers=h,
        params={
            "is_baptized": "true",
            "baptism_date_from": "2024-01-01",
            "baptism_date_to": "2024-12-31",
            "page_size": 50,
        },
    )
    assert combo2.status_code == 200, combo2.text
    names = {it["last_name"] for it in combo2.json()["items"]}
    assert "Combo2024" in names
    assert "In2023" not in names


@pytest.mark.asyncio
async def test_patch_church_member_duplicate_registration_number(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "patchdupadmin@example.com")
    await _promote_to_admin(session_factory, "patchdupadmin@example.com")
    tok = await _login(client, "patchdupadmin@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    year = stats_reference_date().year
    kept = f"{year}-7701"
    clash = f"{year}-7702"

    r1 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Keep", "last_name": "Number", "registration_number": kept},
    )
    assert r1.status_code == 201, r1.text
    mid_keep = r1.json()["id"]

    r2 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Other", "last_name": "Row", "registration_number": clash},
    )
    assert r2.status_code == 201, r2.text
    mid_other = r2.json()["id"]

    pr = await client.patch(
        f"/api/v1/church-members/{mid_other}",
        headers=h,
        json={"registration_number": kept},
    )
    assert pr.status_code == 409, pr.text
    assert "already in use" in pr.json()["detail"].lower()

    ok = await client.get(f"/api/v1/church-members/{mid_keep}", headers=h)
    assert ok.status_code == 200, ok.text
    assert ok.json()["registration_number"] == kept


@pytest.mark.asyncio
async def test_church_members_list_forbidden_for_non_admin(client: AsyncClient) -> None:
    await _register(client, "nomemlist@example.com")
    tok = await _login(client, "nomemlist@example.com")
    r = await client.get(
        "/api/v1/church-members/",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_registration_number_auto_generated_and_sequential(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regnumadmin@example.com")
    await _promote_to_admin(session_factory, "regnumadmin@example.com")
    tok = await _login(client, "regnumadmin@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    r1 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Auto", "last_name": "One"},
    )
    assert r1.status_code == 201, r1.text
    n1 = r1.json()["registration_number"]
    assert n1 is not None
    assert re.fullmatch(r"\d{4}-\d{4}", n1)

    r2 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Auto", "last_name": "Two"},
    )
    assert r2.status_code == 201, r2.text
    n2 = r2.json()["registration_number"]
    assert n2 is not None
    assert re.fullmatch(r"\d{4}-\d{4}", n2)
    assert n2[:4] == n1[:4]
    assert int(n2[-4:]) == int(n1[-4:]) + 1


@pytest.mark.asyncio
async def test_registration_number_manual_override_and_duplicate_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regnummanual@example.com")
    await _promote_to_admin(session_factory, "regnummanual@example.com")
    tok = await _login(client, "regnummanual@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    r1 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Manual",
            "last_name": "One",
            "registration_number": "2030-0042",
        },
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["registration_number"] == "2030-0042"

    r2 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Manual",
            "last_name": "Dup",
            "registration_number": "2030-0042",
        },
    )
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_registration_number_invalid_format_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regnumformat@example.com")
    await _promote_to_admin(session_factory, "regnumformat@example.com")
    tok = await _login(client, "regnumformat@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Bad",
            "last_name": "Format",
            "registration_number": "ABC-1234",
        },
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_registration_number_auto_generation_respects_existing_highest_same_year(
    client: AsyncClient,
    session_factory: async_sessionmaker,
) -> None:
    await _register(client, "regnumseed@example.com")
    await _promote_to_admin(session_factory, "regnumseed@example.com")
    tok = await _login(client, "regnumseed@example.com")
    h = {"Authorization": f"Bearer {tok}"}

    year = stats_reference_date().year
    seeded = f"{year}-0099"
    r1 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={
            "first_name": "Seed",
            "last_name": "NinetyNine",
            "registration_number": seeded,
        },
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/church-members/",
        headers=h,
        json={"first_name": "Seed", "last_name": "Auto"},
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["registration_number"] == f"{year}-0100"
