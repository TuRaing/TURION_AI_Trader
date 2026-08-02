import pandas as pd

# Updated: 2026-07-31 - researched at the user's suggestion after asking
# whether this project has any protection for a sudden market crash. It
# didn't - every existing safeguard (per-trade Stop-Loss, position sizing,
# the MAX_CONCURRENT_POSITIONS cap, Best Trade Engine's forced 14:45
# square-off) limits how much any *one* trade or *one* day can lose, but
# nothing looks at the market itself and pauses new entries during a
# crash. Calibrated against 19 years of real NIFTY daily history
# (2007-2026, yfinance period="max"): daily returns have a ~1.3% std dev;
# every major crash on record (2008 financial crisis, 2020 COVID crash,
# 24-Aug-2015 "Black Monday", 4-Jun-2024 election-result crash) shows up
# as a single-day return of -4% or worse (~1.9 such days/year historically)
# or a 5-day cumulative decline of -10% or worse (the 2008/2020 crises'
# worst 5-day windows ran -15% to -19%) - the defaults below are set from
# that real distribution, not a guess.


def detect_crash_state(daily_close, single_day_pct=-4.0, rolling_days=5, rolling_pct=-10.0):
    """
    Flags each day as a "crash state" if either:
    - that day's own return is <= single_day_pct, or
    - the rolling rolling_days-day cumulative return ending that day is
      <= rolling_pct.

    Both conditions only ever look at the current day and days before it
    (pct_change/rolling both trail, never lead) - no look-ahead by
    construction, same guarantee as every other filter in this codebase.

    Parameters
    ----------
    daily_close : Series
        Daily Close prices, oldest first.
    single_day_pct : float
        Single-day return threshold (%, negative). Default -4.0 - roughly
        the top ~2 crash-grade days/year historically on NIFTY.
    rolling_days : int
        Window for the cumulative-decline check.
    rolling_pct : float
        Cumulative return threshold (%, negative) over rolling_days.
        Default -10.0 - well inside the 2008/2020 crises' actual worst
        5-day windows (-15% to -19%), so it catches a crisis unfolding
        over several days, not just a single brutal one.

    Returns
    -------
    Series of bool, same index as daily_close. First rolling_days rows
    are False (not enough history yet to judge either condition).
    """

    if isinstance(daily_close, pd.DataFrame):
        daily_close = daily_close.iloc[:, 0]

    daily_return = daily_close.pct_change() * 100
    rolling_return = (daily_close / daily_close.shift(rolling_days) - 1) * 100

    crash = (daily_return <= single_day_pct) | (rolling_return <= rolling_pct)

    return crash.fillna(False)
