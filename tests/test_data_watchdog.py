import datetime

from strategy.data_watchdog import should_restart_for_stale_feed

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _dt(y, m, d, h, mi):
    return datetime.datetime(y, m, d, h, mi, tzinfo=IST)


def test_true_when_stale_within_market_hours():
    last = _dt(2026, 8, 26, 10, 0)  # Wednesday
    now = _dt(2026, 8, 26, 10, 6)

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is True


def test_false_when_not_yet_stale():
    last = _dt(2026, 8, 26, 10, 0)
    now = _dt(2026, 8, 26, 10, 4)

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is False


def test_boundary_is_inclusive():
    last = _dt(2026, 8, 26, 10, 0)
    now = _dt(2026, 8, 26, 10, 5)

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is True


def test_false_before_market_open():
    last = _dt(2026, 8, 26, 8, 0)
    now = _dt(2026, 8, 26, 9, 0)  # before 09:15, even though 60 min stale

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is False


def test_false_after_market_close():
    last = _dt(2026, 8, 26, 15, 40)
    now = _dt(2026, 8, 26, 16, 0)  # after 15:30

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is False


def test_false_on_a_weekend_even_if_stale_and_in_time_range():
    # 2026-08-29 is a Saturday
    last = _dt(2026, 8, 29, 10, 0)
    now = _dt(2026, 8, 29, 10, 30)

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is False


def test_false_right_after_a_fresh_message():
    last = _dt(2026, 8, 26, 12, 0)
    now = last + datetime.timedelta(seconds=5)

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is False


def test_real_incident_scenario_9_minutes_silent_at_market_open():
    # 26-Aug-2026's real incident: WebSocket abandoned at 09:13:36 IST,
    # a human noticed and restarted at ~09:22 IST - the watchdog should
    # have fired well before that real 9-minute gap.
    last = _dt(2026, 8, 26, 9, 13)
    now = _dt(2026, 8, 26, 9, 19)  # 6 minutes later, past a 5-min timeout

    assert should_restart_for_stale_feed(last, now, timeout_minutes=5) is True
