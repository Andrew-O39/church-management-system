"""Parish registry age bands: child 0–12, young adult 13–17, adult 18+ (relative to UTC 'today')."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from enum import Enum

from app.db.models.enums import RegistryAgeGroup


def stats_reference_date() -> date:
    """UTC calendar date used for age calculations (matches product note: UTC acceptable)."""
    return datetime.now(timezone.utc).date()


def years_subtract_calendar(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return d.replace(year=d.year - years, month=2, day=28)


def dob_inclusive_range_for_age_group(
    group: RegistryAgeGroup,
    ref: date,
) -> tuple[date, date] | None:
    """Inclusive (min_dob, max_dob) for `ChurchMember.date_of_birth` to fall in the age band."""
    if group == RegistryAgeGroup.CHILD:
        lo = years_subtract_calendar(ref, 13) + timedelta(days=1)
        hi = ref
        return lo, hi
    if group == RegistryAgeGroup.YOUNG_ADULT:
        lo = years_subtract_calendar(ref, 18) + timedelta(days=1)
        hi = years_subtract_calendar(ref, 13)
        return lo, hi
    if group == RegistryAgeGroup.ADULT:
        lo = date(1800, 1, 1)
        hi = years_subtract_calendar(ref, 18)
        return lo, hi
    return None
