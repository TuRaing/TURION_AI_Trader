import datetime

from strategy.squareoff import is_past_squareoff, IST


def test_same_day_before_squareoff_time_is_false():
    entry = "2026-08-19 03:45:00"  # 09:15 IST
    now_ist = datetime.datetime(2026, 8, 19, 12, 0, tzinfo=IST)  # noon IST, same day

    assert is_past_squareoff(entry, now_ist, (15, 15)) is False


def test_same_day_after_squareoff_time_is_true():
    entry = "2026-08-19 03:45:00"  # 09:15 IST
    now_ist = datetime.datetime(2026, 8, 19, 15, 20, tzinfo=IST)  # 15:20 IST, past cutoff

    assert is_past_squareoff(entry, now_ist, (15, 15)) is True


def test_carried_over_from_previous_day_is_true_even_before_todays_cutoff():
    # The actual live bug: opened 18-Aug 14:56 IST, never checked again
    # until 19-Aug 08:33 IST - old code said False (8,33 < 15,15),
    # letting a fully stale position keep running unprotected.
    entry = "2026-08-18 09:26:05"  # 14:56 IST, 18-Aug
    now_ist = datetime.datetime(2026, 8, 19, 8, 33, tzinfo=IST)  # 08:33 IST, 19-Aug - next day, well before cutoff

    assert is_past_squareoff(entry, now_ist, (15, 15)) is True


def test_carried_over_from_previous_day_is_true_even_at_midnight_boundary():
    entry = "2026-08-18 09:26:05"
    now_ist = datetime.datetime(2026, 8, 19, 0, 1, tzinfo=IST)  # just past midnight IST, still next day

    assert is_past_squareoff(entry, now_ist, (15, 15)) is True


def test_same_calendar_day_in_ist_even_though_entry_time_is_stored_as_utc():
    # Entry stored 2026-08-18 19:00:00 (naive UTC) = 2026-08-19 00:30 IST -
    # already the NEXT calendar day in IST, even though the raw string
    # still says "18". Confirms the UTC->IST conversion, not a naive
    # string-prefix date compare, is what actually runs.
    entry = "2026-08-18 19:00:00"
    now_ist = datetime.datetime(2026, 8, 19, 1, 0, tzinfo=IST)  # 01:00 IST, 19-Aug - same IST day as entry

    assert is_past_squareoff(entry, now_ist, (15, 15)) is False

    later_ist = datetime.datetime(2026, 8, 20, 1, 0, tzinfo=IST)  # now a real next day
    assert is_past_squareoff(entry, later_ist, (15, 15)) is True


def test_entry_stored_as_ist_is_not_double_shifted():
    # The event-driven engine (strategy/live_tick_harness.py) stores
    # Entry Time as the tick's own already-IST timestamp, not UTC -
    # entry_stored_as_utc=False must treat it as already-IST, not
    # apply another +5:30 shift on top.
    entry = "2026-08-19 09:15:00"  # already IST, same calendar day
    now_ist = datetime.datetime(2026, 8, 19, 12, 0, tzinfo=IST)

    assert is_past_squareoff(entry, now_ist, (15, 15), entry_stored_as_utc=False) is False


def test_entry_stored_as_ist_carried_over_from_previous_day():
    entry = "2026-08-18 14:56:00"  # already IST, previous day
    now_ist = datetime.datetime(2026, 8, 19, 8, 33, tzinfo=IST)  # next day, well before cutoff

    assert is_past_squareoff(entry, now_ist, (15, 15), entry_stored_as_utc=False) is True
