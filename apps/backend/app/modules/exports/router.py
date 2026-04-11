from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import ChurchMembershipStatus, Gender, RegistryAgeGroup, UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.exports import service as exports_service
from app.modules.exports.schemas import PrintExportPayload

router = APIRouter(prefix="/exports", tags=["exports"])

_admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def _csv_response(*, filename: str, columns: list[str], rows: list[list]) -> Response:
    body = exports_service.rows_to_csv_bytes(columns, rows)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _summary_parts(**kwargs: object | None) -> str | None:
    parts: list[str] = []
    for k, v in kwargs.items():
        if v is None or v == "":
            continue
        parts.append(f"{k.replace('_', ' ')}: {v}")
    return " · ".join(parts) if parts else None


@router.get("/attendance.csv")
async def export_attendance_csv(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    event_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    ministry_id: uuid.UUID | None = None,
) -> Response:
    cols, rows = await exports_service.build_attendance_export(
        session,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        ministry_id=ministry_id,
    )
    fname = await exports_service.resolve_csv_filename(session, base_slug="attendance")
    return _csv_response(filename=fname, columns=cols, rows=rows)


@router.get("/attendance/print", response_model=PrintExportPayload)
async def export_attendance_print(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    event_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    ministry_id: uuid.UUID | None = None,
) -> PrintExportPayload:
    cols, rows = await exports_service.build_attendance_export(
        session,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        ministry_id=ministry_id,
    )
    fs = _summary_parts(
        event_id=str(event_id) if event_id else None,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        ministry_id=str(ministry_id) if ministry_id else None,
    )
    return await exports_service.build_print_export_payload(
        session,
        title="Attendance export",
        subtitle="App users only · operational attendance records",
        columns=cols,
        rows=rows,
        filters_summary=fs,
    )


@router.get("/volunteers.csv")
async def export_volunteers_csv(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    event_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    ministry_id: uuid.UUID | None = None,
) -> Response:
    cols, rows = await exports_service.build_volunteers_export(
        session,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        ministry_id=ministry_id,
    )
    fname = await exports_service.resolve_csv_filename(session, base_slug="volunteers")
    return _csv_response(filename=fname, columns=cols, rows=rows)


@router.get("/volunteers/print", response_model=PrintExportPayload)
async def export_volunteers_print(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    event_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    ministry_id: uuid.UUID | None = None,
) -> PrintExportPayload:
    cols, rows = await exports_service.build_volunteers_export(
        session,
        event_id=event_id,
        date_from=date_from,
        date_to=date_to,
        ministry_id=ministry_id,
    )
    fs = _summary_parts(
        event_id=str(event_id) if event_id else None,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        ministry_id=str(ministry_id) if ministry_id else None,
    )
    return await exports_service.build_print_export_payload(
        session,
        title="Volunteer assignments export",
        subtitle="App users only · volunteer roles per event",
        columns=cols,
        rows=rows,
        filters_summary=fs,
    )


@router.get("/users.csv")
async def export_users_csv(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    is_active: bool | None = None,
    role: UserRole | None = Query(default=None),
    ministry_id: uuid.UUID | None = None,
) -> Response:
    cols, rows = await exports_service.build_app_users_export(
        session,
        is_active=is_active,
        role=role,
        ministry_id=ministry_id,
    )
    fname = await exports_service.resolve_csv_filename(session, base_slug="app-users")
    return _csv_response(filename=fname, columns=cols, rows=rows)


@router.get("/users/print", response_model=PrintExportPayload)
async def export_users_print(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    is_active: bool | None = None,
    role: UserRole | None = Query(default=None),
    ministry_id: uuid.UUID | None = None,
) -> PrintExportPayload:
    cols, rows = await exports_service.build_app_users_export(
        session,
        is_active=is_active,
        role=role,
        ministry_id=ministry_id,
    )
    fs = _summary_parts(
        is_active=is_active,
        role=role.value if role else None,
        ministry_id=str(ministry_id) if ministry_id else None,
    )
    return await exports_service.build_print_export_payload(
        session,
        title="App users export",
        subtitle="Login accounts and profiles · not parish registry",
        columns=cols,
        rows=rows,
        filters_summary=fs,
    )


@router.get("/parish-registry.csv")
async def export_parish_registry_csv(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    search: str | None = Query(default=None, max_length=200),
    membership_status: ChurchMembershipStatus | None = Query(default=None),
    is_active: bool | None = None,
    is_deceased: bool | None = None,
    gender: Gender | None = Query(default=None),
    is_baptized: bool | None = None,
    is_confirmed: bool | None = None,
    is_communicant: bool | None = None,
    is_married: bool | None = None,
    age_group: RegistryAgeGroup | None = Query(default=None),
    joined_from: date | None = Query(default=None),
    joined_to: date | None = Query(default=None),
    deceased_from: date | None = Query(default=None),
    deceased_to: date | None = Query(default=None),
    baptism_date_from: date | None = Query(default=None),
    baptism_date_to: date | None = Query(default=None),
    confirmation_date_from: date | None = Query(default=None),
    confirmation_date_to: date | None = Query(default=None),
    first_communion_date_from: date | None = Query(default=None),
    first_communion_date_to: date | None = Query(default=None),
    marriage_date_from: date | None = Query(default=None),
    marriage_date_to: date | None = Query(default=None),
    date_of_birth_from: date | None = Query(default=None),
    date_of_birth_to: date | None = Query(default=None),
) -> Response:
    cols, rows = await exports_service.build_parish_registry_export(
        session,
        search=search,
        membership_status=membership_status,
        is_deceased=is_deceased,
        gender=gender,
        is_baptized=is_baptized,
        is_confirmed=is_confirmed,
        is_communicant=is_communicant,
        is_active=is_active,
        is_married=is_married,
        age_group=age_group,
        joined_from=joined_from,
        joined_to=joined_to,
        deceased_from=deceased_from,
        deceased_to=deceased_to,
        baptism_date_from=baptism_date_from,
        baptism_date_to=baptism_date_to,
        confirmation_date_from=confirmation_date_from,
        confirmation_date_to=confirmation_date_to,
        first_communion_date_from=first_communion_date_from,
        first_communion_date_to=first_communion_date_to,
        marriage_date_from=marriage_date_from,
        marriage_date_to=marriage_date_to,
        date_of_birth_from=date_of_birth_from,
        date_of_birth_to=date_of_birth_to,
    )
    fname = await exports_service.resolve_csv_filename(session, base_slug="parish-registry")
    return _csv_response(filename=fname, columns=cols, rows=rows)


@router.get("/parish-registry/print", response_model=PrintExportPayload)
async def export_parish_registry_print(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    search: str | None = Query(default=None, max_length=200),
    membership_status: ChurchMembershipStatus | None = Query(default=None),
    is_active: bool | None = None,
    is_deceased: bool | None = None,
    gender: Gender | None = Query(default=None),
    is_baptized: bool | None = None,
    is_confirmed: bool | None = None,
    is_communicant: bool | None = None,
    is_married: bool | None = None,
    age_group: RegistryAgeGroup | None = Query(default=None),
    joined_from: date | None = Query(default=None),
    joined_to: date | None = Query(default=None),
    deceased_from: date | None = Query(default=None),
    deceased_to: date | None = Query(default=None),
    baptism_date_from: date | None = Query(default=None),
    baptism_date_to: date | None = Query(default=None),
    confirmation_date_from: date | None = Query(default=None),
    confirmation_date_to: date | None = Query(default=None),
    first_communion_date_from: date | None = Query(default=None),
    first_communion_date_to: date | None = Query(default=None),
    marriage_date_from: date | None = Query(default=None),
    marriage_date_to: date | None = Query(default=None),
    date_of_birth_from: date | None = Query(default=None),
    date_of_birth_to: date | None = Query(default=None),
) -> PrintExportPayload:
    cols, rows = await exports_service.build_parish_registry_export(
        session,
        search=search,
        membership_status=membership_status,
        is_deceased=is_deceased,
        gender=gender,
        is_baptized=is_baptized,
        is_confirmed=is_confirmed,
        is_communicant=is_communicant,
        is_active=is_active,
        is_married=is_married,
        age_group=age_group,
        joined_from=joined_from,
        joined_to=joined_to,
        deceased_from=deceased_from,
        deceased_to=deceased_to,
        baptism_date_from=baptism_date_from,
        baptism_date_to=baptism_date_to,
        confirmation_date_from=confirmation_date_from,
        confirmation_date_to=confirmation_date_to,
        first_communion_date_from=first_communion_date_from,
        first_communion_date_to=first_communion_date_to,
        marriage_date_from=marriage_date_from,
        marriage_date_to=marriage_date_to,
        date_of_birth_from=date_of_birth_from,
        date_of_birth_to=date_of_birth_to,
    )
    fs = _summary_parts(
        search=search,
        membership_status=membership_status.value if membership_status else None,
        is_active=is_active,
        is_deceased=is_deceased,
        gender=gender.value if gender else None,
        is_baptized=is_baptized,
        is_confirmed=is_confirmed,
        is_communicant=is_communicant,
        is_married=is_married,
        age_group=age_group.value if age_group else None,
        joined_from=joined_from.isoformat() if joined_from else None,
        joined_to=joined_to.isoformat() if joined_to else None,
        deceased_from=deceased_from.isoformat() if deceased_from else None,
        deceased_to=deceased_to.isoformat() if deceased_to else None,
        baptism_date_from=baptism_date_from.isoformat() if baptism_date_from else None,
        baptism_date_to=baptism_date_to.isoformat() if baptism_date_to else None,
        confirmation_date_from=confirmation_date_from.isoformat() if confirmation_date_from else None,
        confirmation_date_to=confirmation_date_to.isoformat() if confirmation_date_to else None,
        first_communion_date_from=first_communion_date_from.isoformat()
        if first_communion_date_from
        else None,
        first_communion_date_to=first_communion_date_to.isoformat() if first_communion_date_to else None,
        marriage_date_from=marriage_date_from.isoformat() if marriage_date_from else None,
        marriage_date_to=marriage_date_to.isoformat() if marriage_date_to else None,
        date_of_birth_from=date_of_birth_from.isoformat() if date_of_birth_from else None,
        date_of_birth_to=date_of_birth_to.isoformat() if date_of_birth_to else None,
    )
    return await exports_service.build_print_export_payload(
        session,
        title="Parish registry export",
        subtitle="Official parish records only · separate from app users",
        columns=cols,
        rows=rows,
        filters_summary=fs,
    )
