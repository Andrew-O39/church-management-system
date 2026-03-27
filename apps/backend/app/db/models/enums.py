from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    GROUP_LEADER = "group_leader"
    MEMBER = "member"


class PreferredChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class MaritalStatus(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"
    SEPARATED = "separated"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MinistryRoleInMinistry(str, enum.Enum):
    """Role of a user within a ministry (not the same as system UserRole)."""

    MEMBER = "member"
    LEADER = "leader"
    COORDINATOR = "coordinator"


class EventType(str, enum.Enum):
    SERVICE = "service"
    MEETING = "meeting"
    REHEARSAL = "rehearsal"
    RETREAT = "retreat"
    CONFERENCE = "conference"
    OTHER = "other"


class EventVisibility(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
