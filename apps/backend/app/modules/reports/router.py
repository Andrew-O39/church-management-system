from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth.deps import require_roles
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import (
    AttendanceReportResponse,
    DashboardSummaryResponse,
    NotificationInsightsResponse,
    VolunteerReportResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
) -> DashboardSummaryResponse:
    return await reports_service.get_dashboard_summary(session)


@router.get("/attendance", response_model=AttendanceReportResponse)
async def get_attendance_report(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    limit: int = Query(default=50, ge=1, le=200),
) -> AttendanceReportResponse:
    return await reports_service.get_attendance_report(session, limit=limit)


@router.get("/volunteers", response_model=VolunteerReportResponse)
async def get_volunteer_report(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
    limit: int = Query(default=20, ge=1, le=100),
) -> VolunteerReportResponse:
    return await reports_service.get_volunteer_report(session, limit=limit)


@router.get("/notifications", response_model=NotificationInsightsResponse)
async def get_notification_insights(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _: _admin,
) -> NotificationInsightsResponse:
    return await reports_service.get_notification_insights(session)
