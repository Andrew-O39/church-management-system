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
from app.db.models.event_reminder_rule import EventReminderRule
from app.db.models.event_reminder_run import EventReminderRun
from app.db.models.church_profile import ChurchProfile
from app.db.models.registry_saved_filter import RegistrySavedFilter

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
    "EventReminderRule",
    "EventReminderRun",
    "ChurchProfile",
    "RegistrySavedFilter",
]
