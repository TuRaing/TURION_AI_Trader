import datetime

from analyze_latency_slippage import price_deltas_over_window

FMT = "%Y-%m-%d %H:%M:%S.%f"


def _rec(dt_str, ltp):
    return {"_dt": datetime.datetime.strptime(dt_str, FMT), "ltp": ltp}


def test_finds_the_delta_at_least_window_seconds_later():
    records = [
        _rec("2026-08-26 09:30:00.000", 100.0),
        _rec("2026-08-26 09:30:00.500", 101.0),
        _rec("2026-08-26 09:30:01.100", 103.0),  # first one >= 1.0s after record 0
    ]

    deltas = price_deltas_over_window(records, window_seconds=1.0)

    # record 0 (100.0) -> record 2 (103.0), delta 3.0
    # record 1 (101.0) -> no record >= 1.0s later exists, skipped
    assert deltas == [3.0]


def test_no_delta_when_nothing_is_far_enough_in_the_future():
    records = [
        _rec("2026-08-26 09:30:00.000", 100.0),
        _rec("2026-08-26 09:30:00.500", 101.0),
    ]

    assert price_deltas_over_window(records, window_seconds=5.0) == []


def test_uses_absolute_value_for_price_drops_too():
    records = [
        _rec("2026-08-26 09:30:00.000", 100.0),
        _rec("2026-08-26 09:30:01.500", 92.0),
    ]

    assert price_deltas_over_window(records, window_seconds=1.0) == [8.0]


def test_zero_delta_when_price_unchanged():
    records = [
        _rec("2026-08-26 09:30:00.000", 100.0),
        _rec("2026-08-26 09:30:01.500", 100.0),
    ]

    assert price_deltas_over_window(records, window_seconds=1.0) == [0.0]


def test_every_eligible_record_contributes_one_delta():
    records = [
        _rec("2026-08-26 09:30:00.000", 100.0),
        _rec("2026-08-26 09:30:01.000", 105.0),
        _rec("2026-08-26 09:30:02.000", 110.0),
    ]

    deltas = price_deltas_over_window(records, window_seconds=1.0)

    # record 0 -> record 1: |105-100|=5, record 1 -> record 2: |110-105|=5
    assert deltas == [5.0, 5.0]
