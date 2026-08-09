import pandas as pd

from strategy.rsi_divergence_backtest import _run_on_data


def _make_ohlcv(closes, seed_range=5.0):

    n = len(closes)
    dates = pd.date_range("2026-01-01 09:15", periods=n, freq="5min")
    close = pd.Series(closes, index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + seed_range
    low = pd.concat([open_, close], axis=1).min(axis=1) - seed_range
    volume = pd.Series([1000] * n, index=dates)

    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume})


def test_run_on_data_returns_well_formed_summary_on_flat_data():
    # No real swings/divergence in a flat series - should return a
    # clean empty-trades summary, not crash.
    data = _make_ohlcv([24500.0] * 80)

    result = _run_on_data(
        data, lot_size=75, atr_sl_mult=1.0, atr_target_mult=2.0, starting_capital=250000,
        worst_case_move_pct=10.0, allow_short=True, swing_lookback=3,
    )

    assert result["Total Trades"] == 0
    assert result["Capital Ever Negative"] is False


def test_run_on_data_handles_a_realistic_series_without_crashing():
    # A choppy-then-trending series - the point is the full pipeline
    # (swings -> RSI-at-swing -> divergence check -> entry -> SL/
    # Target management) runs end to end without error, and capital
    # never goes negative (the safety design under test).
    up_down = [24500 + (i % 10) * 5 - (i % 7) * 4 for i in range(60)]
    trend = [up_down[-1] + i * 3 for i in range(1, 40)]

    data = _make_ohlcv(up_down + trend)

    result = _run_on_data(
        data, lot_size=75, atr_sl_mult=1.0, atr_target_mult=2.0, starting_capital=250000,
        worst_case_move_pct=10.0, allow_short=True, swing_lookback=3,
    )

    assert "Total Trades" in result
    assert result["Total Trades"] == len(result["Trades"])
    assert result["Capital Ever Negative"] is False
