from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.availability import find_free_slots

DUBLIN = ZoneInfo("Europe/Dublin")
SATURDAY = date(2026, 11, 21)
LONG_AGO = datetime(2020, 1, 1, tzinfo=DUBLIN)


def at(hour, minute=0):
    """Saturday at hour:minute, Irish time."""
    return datetime(2026, 11, 21, hour, minute, tzinfo=DUBLIN)


def test_empty_day_offers_slots_until_the_appointment_fits():
    slots = find_free_slots(SATURDAY, [(time(10), time(12))], [], 60, 0, DUBLIN, LONG_AGO)

    assert slots[0] == at(10)
    assert slots[-1] == at(11)  # 11:00 + 60 min = 12:00, still fits


def test_existing_booking_blocks_overlapping_slots():
    busy = [(at(10), at(11))]

    slots = find_free_slots(SATURDAY, [(time(10), time(13))], busy, 60, 0, DUBLIN, LONG_AGO)

    assert at(10) not in slots
    assert at(10, 30) not in slots
    assert at(11) in slots  # back-to-back is allowed


def test_buffer_keeps_cleanup_time_before_the_next_booking():
    busy = [(at(12), at(13))]

    slots = find_free_slots(SATURDAY, [(time(10), time(13))], busy, 60, 15, DUBLIN, LONG_AGO)

    assert at(10, 45) in slots  # ends 11:45, cleanup until 12:00
    assert at(11) not in slots  # cleanup would run into the 12:00 booking


def test_time_off_blocks_the_whole_day():
    busy = [(at(0), at(23, 59))]

    slots = find_free_slots(SATURDAY, [(time(10), time(18))], busy, 60, 0, DUBLIN, LONG_AGO)

    assert slots == []


def test_closed_day_has_no_slots():
    assert find_free_slots(SATURDAY, [], [], 60, 0, DUBLIN, LONG_AGO) == []


def test_slots_in_the_past_are_hidden():
    slots = find_free_slots(SATURDAY, [(time(10), time(13))], [], 60, 0, DUBLIN, now=at(11))

    assert slots[0] == at(11, 15)
