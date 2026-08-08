import pandas as pd

from strategy.ict_smc_backtest import _run_on_data


def _make_ohlcv(closes, seed_range=0.3):

    n = len(closes)
    dates = pd.date_range("2026-01-01 09:15", periods=n, freq="5min")
    close = pd.Series(closes, index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + seed_range
    low = pd.concat([open_, close], axis=1).min(axis=1) - seed_range
    volume = pd.Series([1000] * n, index=dates)

    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume})


def test_run_on_data_returns_summary_shape_on_flat_data():
    # No real structure breaks in a flat series - should return a clean
    # empty-trades summary, not crash.
    data = _make_ohlcv([100.0] * 60)

    result = _run_on_data(data, atr_sl_mult=1.0, atr_target_mult=2.0, allow_short=True, swing_lookback=2)

    assert result["Total Trades"] == 0
    assert result["Net PnL"] == 0
    assert result["Exit Reasons"] == {}


def test_run_on_data_handles_a_clear_downtrend_then_reversal_without_crashing():
    # A down-swing (establishing a downtrend), then a sharp reversal up
    # through the last swing high - this SHOULD produce a CHOCH and may
    # or may not produce a trade depending on whether a valid OB/FVG zone
    # forms and gets retraced into. The point of this test is that the
    # full pipeline (swings -> tracker -> OB/FVG -> entry -> SL/Target
    # management) runs end to end without error on a realistic-shaped
    # series, and returns a well-formed summary either way.
    down_leg = [100 - i * 0.5 for i in range(20)]
    up_leg = [down_leg[-1] + i * 1.5 for i in range(1, 25)]
    tail = [up_leg[-1]] * 15

    data = _make_ohlcv(down_leg + up_leg + tail)

    result = _run_on_data(data, atr_sl_mult=1.0, atr_target_mult=2.0, allow_short=True, swing_lookback=2)

    assert "Total Trades" in result
    assert "Net PnL" in result
    assert result["Total Trades"] == len(result["Trades"])


def test_run_on_data_no_shorts_when_allow_short_false():
    down_leg = [100 - i * 0.5 for i in range(20)]
    up_leg = [down_leg[-1] + i * 1.5 for i in range(1, 25)]
    tail = [up_leg[-1]] * 15

    data = _make_ohlcv(down_leg + up_leg + tail)

    result = _run_on_data(data, atr_sl_mult=1.0, atr_target_mult=2.0, allow_short=False, swing_lookback=2)

    assert all(t["Direction"] == "BUY" for t in result["Trades"])
