"""ORM models — import for metadata registration (Alembic, tests)."""

from app.db.models.member_profile import MemberProfile
from app.db.models.church_event import ChurchEvent
from app.db.models.event_attendance import EventAttendance
from app.db.models.ministry_group import MinistryGroup
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User

__all__ = [
    "User",
    "MemberProfile",
    "ChurchEvent",
    "EventAttendance",
    "MinistryGroup",
    "MinistryMembership",
]
