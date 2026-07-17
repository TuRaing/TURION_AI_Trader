from datetime import datetime

import daily_best_trade as dbt


class _FixedDatetime(datetime):
    """Lets tests pin daily_best_trade's notion of "now" without touching
    the real clock - _before_entry_start/_past_entry_cutoff both call
    datetime.now(IST) directly, so the module-level `datetime` name is
    swapped for one whose .now() always returns the time under test."""

    _fixed = None

    @classmethod
    def now(cls, tz=None):
        return cls._fixed


def _set_ist_time(monkeypatch, hour, minute):

    fixed = _FixedDatetime(2026, 7, 17, hour, minute, tzinfo=dbt.IST)
    _FixedDatetime._fixed = fixed

    monkeypatch.setattr(dbt, "datetime", _FixedDatetime)


# ---------------- ENTRY_START (10:00 IST) ----------------

def test_before_market_open_is_before_entry_start(monkeypatch):
    _set_ist_time(monkeypatch, 8, 30)
    assert dbt._before_entry_start() is True


def test_just_after_open_09_30_is_before_entry_start(monkeypatch):
    _set_ist_time(monkeypatch, 9, 30)
    assert dbt._before_entry_start() is True


def test_at_09_59_is_still_before_entry_start(monkeypatch):
    _set_ist_time(monkeypatch, 9, 59)
    assert dbt._before_entry_start() is True


def test_at_exactly_10_00_entry_start_has_arrived(monkeypatch):
    _set_ist_time(monkeypatch, 10, 0)
    assert dbt._before_entry_start() is False


def test_mid_morning_11_30_is_past_entry_start(monkeypatch):
    _set_ist_time(monkeypatch, 11, 30)
    assert dbt._before_entry_start() is False


# ---------------- LAST_ENTRY_CUTOFF (14:15 IST) ----------------

def test_at_14_14_not_yet_past_cutoff(monkeypatch):
    _set_ist_time(monkeypatch, 14, 14)
    assert dbt._past_entry_cutoff() is False


def test_at_exactly_14_15_is_past_cutoff(monkeypatch):
    _set_ist_time(monkeypatch, 14, 15)
    assert dbt._past_entry_cutoff() is True


def test_at_square_off_time_14_45_is_past_cutoff(monkeypatch):
    _set_ist_time(monkeypatch, 14, 45)
    assert dbt._past_entry_cutoff() is True


def test_after_market_close_17_00_is_past_cutoff(monkeypatch):
    _set_ist_time(monkeypatch, 17, 0)
    assert dbt._past_entry_cutoff() is True


# ---------------- the entry window itself ----------------

def test_11_30_is_inside_the_entry_window_not_before_not_past(monkeypatch):
    _set_ist_time(monkeypatch, 11, 30)
    assert dbt._before_entry_start() is False
    assert dbt._past_entry_cutoff() is False


def test_09_00_is_before_the_entry_window(monkeypatch):
    _set_ist_time(monkeypatch, 9, 0)
    assert dbt._before_entry_start() is True
    assert dbt._past_entry_cutoff() is False
