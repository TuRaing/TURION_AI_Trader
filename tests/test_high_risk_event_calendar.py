import datetime

from indicators.high_risk_event_calendar import (
    is_budget_day,
    is_high_risk_event_day,
)


def test_is_budget_day_true_on_1_feb():
    assert is_budget_day(datetime.date(2026, 2, 1))


def test_is_budget_day_false_on_other_days():
    assert not is_budget_day(datetime.date(2026, 2, 2))
    assert not is_budget_day(datetime.date(2026, 1, 1))


def test_is_budget_day_true_every_year():
    assert is_budget_day(datetime.date(2027, 2, 1))
    assert is_budget_day(datetime.date(2030, 2, 1))


def test_high_risk_event_day_true_on_budget_day():
    assert is_high_risk_event_day(datetime.date(2026, 2, 1))


def test_high_risk_event_day_false_on_a_normal_day_with_empty_calendar():
    assert not is_high_risk_event_day(datetime.date(2026, 8, 14), extra_event_dates=set())


def test_high_risk_event_day_true_for_an_explicitly_listed_extra_date():
    custom_dates = {"2026-08-14"}

    assert is_high_risk_event_day(datetime.date(2026, 8, 14), extra_event_dates=custom_dates)


def test_high_risk_event_day_false_for_a_date_not_in_the_extra_list():
    custom_dates = {"2026-09-30"}

    assert not is_high_risk_event_day(datetime.date(2026, 8, 14), extra_event_dates=custom_dates)


def test_default_module_calendar_is_empty_by_design():
    # See the module docstring - RBI/election/macro dates are
    # deliberately NOT hardcoded until confirmed against a real
    # published calendar, so this should stay empty out of the box.
    from indicators.high_risk_event_calendar import HIGH_RISK_EVENT_DATES

    assert HIGH_RISK_EVENT_DATES == set()
