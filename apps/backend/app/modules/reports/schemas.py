from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DashboardSummaryResponse(BaseModel):
    """High-level counts for the admin home / dashboard."""

    total_users: int = Field(description="All application user accounts.")
    active_users_last_30_days: int = Field(
        description=(
            "Distinct users with operational activity in the last 30 days: attendance touch, "
            "volunteer assignment touch, or notification recipient activity."
        ),
    )
    total_ministries: int
    active_ministries: int
    upcoming_events_count: int = Field(description="Active events with start time in the future.")
    events_this_week: int = Field(
        description="Active events starting within the next 7 days (from now, inclusive window).",
    )
    volunteers_assigned_upcoming: int = Field(
        description="Volunteer assignment rows for future, active events.",
    )
    unread_notifications_total: int = Field(
        description="In-app recipient rows still in delivered (unread) state, all users.",
    )


class AttendanceEventRow(BaseModel):
    event_id: uuid.UUID
    event_title: str
    start_at: datetime
    attendance_count: int


class AttendanceReportResponse(BaseModel):
    items: list[AttendanceEventRow]


class VolunteerLeaderRow(BaseModel):
    user_id: uuid.UUID
    full_name: str
    assignments_count: int


class VolunteerReportResponse(BaseModel):
    items: list[VolunteerLeaderRow]


class NotificationInsightsResponse(BaseModel):
    total_notifications_sent: int = Field(
        description="Notifications with sent_at set (considered sent).",
    )
    total_recipients: int = Field(description="All notification_recipients rows.")
    in_app_delivered: int = Field(
        description="In-app delivery attempts marked sent or delivered.",
    )
    in_app_failed: int
    sms_attempted: int = Field(description="SMS delivery attempt rows (any outcome).")
    sms_failed: int
    whatsapp_attempted: int
    whatsapp_failed: int
