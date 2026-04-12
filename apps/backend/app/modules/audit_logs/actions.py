"""Stable action identifiers for filters and tests."""

# Authentication
AUTH_LOGIN_SUCCESS = "auth.login_success"
AUTH_LOGIN_FAILURE = "auth.login_failure"
AUTH_REGISTER_SUCCESS = "auth.register_success"

# Parish registry (ChurchMember)
REGISTRY_MEMBER_CREATE = "registry.member_create"
REGISTRY_MEMBER_UPDATE = "registry.member_update"
REGISTRY_MEMBER_LINK_USER = "registry.member_link_user"

# Exports
EXPORT_ATTENDANCE_CSV = "export.attendance_csv"
EXPORT_ATTENDANCE_PRINT = "export.attendance_print"
EXPORT_VOLUNTEERS_CSV = "export.volunteers_csv"
EXPORT_VOLUNTEERS_PRINT = "export.volunteers_print"
EXPORT_APP_USERS_CSV = "export.app_users_csv"
EXPORT_APP_USERS_PRINT = "export.app_users_print"
EXPORT_PARISH_REGISTRY_CSV = "export.parish_registry_csv"
EXPORT_PARISH_REGISTRY_PRINT = "export.parish_registry_print"

# Notifications
NOTIFICATION_SEND = "notification.send"
NOTIFICATION_RUN_DUE_REMINDERS = "notification.run_due_reminders"

# Church settings
CHURCH_PROFILE_UPDATE = "church_profile.update"

# App user directory (admin PATCH /members/{id})
APP_USER_ADMIN_UPDATE = "app_user.admin_update"
APP_USER_ADMIN_PROMOTED = "app_user.admin_promoted"
APP_USER_ADMIN_DEMOTED = "app_user.admin_demoted"
APP_USER_DEACTIVATED = "app_user.deactivated"
APP_USER_REACTIVATED = "app_user.reactivated"

# Events (admin)
EVENTS_CREATE = "events.create"
EVENTS_UPDATE = "events.update"

# Attendance (admin)
ATTENDANCE_CREATE = "attendance.create"
ATTENDANCE_UPDATE = "attendance.update"

# Volunteer assignments (admin)
VOLUNTEER_ASSIGNMENT_CREATE = "volunteer_assignment.create"
VOLUNTEER_ASSIGNMENT_UPDATE = "volunteer_assignment.update"
VOLUNTEER_ASSIGNMENT_DELETE = "volunteer_assignment.delete"

# Ministries (admin)
MINISTRIES_CREATE = "ministries.create"
MINISTRIES_UPDATE = "ministries.update"

# Volunteer roles (admin)
VOLUNTEER_ROLES_CREATE = "volunteer_roles.create"
VOLUNTEER_ROLES_UPDATE = "volunteer_roles.update"

# Event reminder rules (admin)
EVENT_REMINDER_RULE_CREATE = "event_reminder_rule.create"
EVENT_REMINDER_RULE_UPDATE = "event_reminder_rule.update"
EVENT_REMINDER_RULE_DELETE = "event_reminder_rule.delete"
