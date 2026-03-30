"""ORM models — import for metadata registration (Alembic, tests)."""

from app.db.models.church_member import ChurchMember
from app.db.models.member_profile import MemberProfile
from app.db.models.church_event import ChurchEvent
from app.db.models.event_attendance import EventAttendance
from app.db.models.ministry_group import MinistryGroup
from app.db.models.ministry_membership import MinistryMembership
from app.db.models.user import User
from app.db.models.volunteer_assignment import VolunteerAssignment
from app.db.models.volunteer_role import VolunteerRole
from app.db.models.notification import Notification
from app.db.models.notification_delivery_attempt import NotificationDeliveryAttempt
from app.db.models.notification_recipient import NotificationRecipient

__all__ = [
    "User",
    "ChurchMember",
    "MemberProfile",
    "ChurchEvent",
    "EventAttendance",
    "MinistryGroup",
    "MinistryMembership",
    "VolunteerRole",
    "VolunteerAssignment",
    "Notification",
    "NotificationDeliveryAttempt",
    "NotificationRecipient",
]
