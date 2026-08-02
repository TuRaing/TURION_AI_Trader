import pandas as pd

from strategy.crash_protection_engine import detect_crash_state


def test_single_day_crash_flagged():
    prices = pd.Series([100, 100, 100, 100, 100, 90])  # -10% on the last day

    result = detect_crash_state(prices, single_day_pct=-4.0, rolling_days=5, rolling_pct=-10.0)

    assert result.iloc[-1] == True
    assert not result.iloc[:-1].any()


def test_normal_volatility_not_flagged():
    prices = pd.Series([100, 101, 99, 100.5, 99.5, 100.2, 99.8])  # small day-to-day moves

    result = detect_crash_state(prices, single_day_pct=-4.0, rolling_days=5, rolling_pct=-10.0)

    assert not result.any()


def test_rolling_decline_flagged_without_a_single_bad_day():
    # -2.5%/day for 5 days compounds to roughly -12%, but no single day hits -4%
    prices = pd.Series([100])
    for _ in range(6):
        prices = pd.concat([prices, pd.Series([prices.iloc[-1] * 0.975])], ignore_index=True)

    result = detect_crash_state(prices, single_day_pct=-4.0, rolling_days=5, rolling_pct=-10.0)

    assert result.iloc[-1] == True


def test_leading_rows_are_false():
    prices = pd.Series([100, 95, 90, 85, 80])

    result = detect_crash_state(prices, rolling_days=5)

    assert not result.iloc[0]
