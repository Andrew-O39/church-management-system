from __future__ import annotations

from fastapi import HTTPException, status

# Parish registry list / export query parameter names (no page / page_size).
REGISTRY_FILTER_ALLOWED_KEYS = frozenset(
    {
        "search",
        "membership_status",
        "is_active",
        "is_deceased",
        "gender",
        "is_baptized",
        "is_confirmed",
        "is_communicant",
        "is_married",
        "age_group",
        "joined_from",
        "joined_to",
        "deceased_from",
        "deceased_to",
        "baptism_date_from",
        "baptism_date_to",
        "first_communion_date_from",
        "first_communion_date_to",
        "confirmation_date_from",
        "confirmation_date_to",
        "marriage_date_from",
        "marriage_date_to",
        "date_of_birth_from",
        "date_of_birth_to",
    }
)

_MAX_VALUE_LEN = 512


def normalize_registry_filters_payload(raw: dict[str, object]) -> dict[str, str]:
    """Validate keys and coerce values to non-empty strings for storage."""
    out: dict[str, str] = {}
    for k, v in raw.items():
        if k not in REGISTRY_FILTER_ALLOWED_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown filter key: {k}",
            )
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        if len(s) > _MAX_VALUE_LEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Filter value too long for {k}",
            )
        out[k] = s
    return out
