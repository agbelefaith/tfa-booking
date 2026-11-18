"""Works out which start times are free on a given day.

This file has no database code on purpose: it takes plain values in
and gives a list of times back, so it's easy to test.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SLOT_STEP_MINUTES = 15


def overlaps(start_a, end_a, start_b, end_b) -> bool:
    """True if two time ranges overlap (touching end-to-start is fine)."""
    return start_a < end_b and start_b < end_a


def find_free_slots(
    day: date,
    opening_hours: list[tuple[time, time]],
    busy: list[tuple[datetime, datetime]],
    appointment_minutes: int,
    buffer_minutes: int,
    timezone: ZoneInfo,
    now: datetime,
) -> list[datetime]:
    """Return every start time on `day` where the appointment fits."""
    appointment = timedelta(minutes=appointment_minutes)
    buffer = timedelta(minutes=buffer_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)
    free = []

    for opens_at, closes_at in opening_hours:
        start = datetime.combine(day, opens_at, tzinfo=timezone)
        closing_time = datetime.combine(day, closes_at, tzinfo=timezone)

        while start + appointment <= closing_time:
            blocked_until = start + appointment + buffer
            clashes = any(overlaps(start, blocked_until, b_start, b_end) for b_start, b_end in busy)
            if not clashes and start > now:
                free.append(start)
            start += step

    return free
