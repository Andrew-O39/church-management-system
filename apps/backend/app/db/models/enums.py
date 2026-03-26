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
