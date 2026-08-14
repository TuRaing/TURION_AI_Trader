import datetime

# Added 14-Aug-2026 - candidate #4 from doc/PROJECT_STATUS.md's
# "CIRCUIT-BREAKER PROTECTION IDEAS" entry: avoid holding through (or
# opening new positions on) days disproportionately likely to produce
# a large, sudden index move - Union Budget day, RBI Monetary Policy
# Committee (MPC) announcements, major election results, big macro
# announcements (US Fed FOMC, etc.). Unlike the other 14-Aug filters
# (circuit_band.py, the SL trigger-price solver), this one is NOT pure
# math over already-known data - it depends on a real-world event
# CALENDAR that has to be kept current by hand. Built as two pieces so
# the maintenance burden is isolated to one small, obvious place:
#
# 1. Union Budget day - the one genuinely fixed, programmatically-
#    computable date here (01-Feb every year; if that falls on a
#    weekend the government has historically still presented it that
#    day, so no weekend-shift logic is added - flag it by hand the one
#    year that turns out wrong rather than guess a rule).
#
# 2. Everything else (RBI MPC dates, election results, major
#    scheduled macro announcements) - NOT hardcoded here. RBI publishes
#    its MPC calendar for the fiscal year on rbi.org.in; election
#    result dates are set by the Election Commission; this module
#    intentionally ships with an EMPTY starter set for those rather
#    than fabricated/guessed 2026 dates - a wrong hardcoded date is
#    worse than no date, since it would either miss the real risk day
#    or needlessly block a normal trading day. HIGH_RISK_EVENT_DATES
#    is meant to be updated by hand, periodically, against the real
#    published calendars - not treated as complete out of the box.
#
# NOT WIRED INTO ANY STRATEGY - same built-not-deployed status as this
# session's other two circuit-breaker candidates.

BUDGET_DAY_MONTH = 2
BUDGET_DAY_DAY = 1

# Manually maintained - add confirmed RBI MPC / election-result / major
# macro-announcement dates here as ISO strings ("YYYY-MM-DD") once
# published by the relevant official source. Intentionally empty until
# then - see the module docstring above for why nothing is guessed.
HIGH_RISK_EVENT_DATES = set()


def is_budget_day(check_date):
    """
    Pure function - True if check_date (a datetime.date) is India's
    Union Budget day (01-Feb).
    """

    return check_date.month == BUDGET_DAY_MONTH and check_date.day == BUDGET_DAY_DAY


def is_high_risk_event_day(check_date, extra_event_dates=None):
    """
    Pure function - True if check_date is Budget day OR explicitly
    listed in extra_event_dates (defaults to the module-level
    HIGH_RISK_EVENT_DATES set - pass a different set/collection of
    "YYYY-MM-DD" strings to check against a custom list instead).

    Parameters
    ----------
    check_date : datetime.date
    extra_event_dates : iterable of str ("YYYY-MM-DD"), optional
    """

    if is_budget_day(check_date):
        return True

    event_dates = extra_event_dates if extra_event_dates is not None else HIGH_RISK_EVENT_DATES

    return check_date.strftime("%Y-%m-%d") in event_dates
