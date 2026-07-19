import pandas as pd

from strategy.multi_timeframe_backtest import _analyze_series, WARMUP


def _make_ohlcv(n=150, start_price=100.0, drift=0.2, seed=1):

    import random

    random.seed(seed)

    dates = pd.date_range("2026-01-01", periods=n, freq="15min")

    closes = [start_price]

    for _ in range(n - 1):
        closes.append(closes[-1] + drift + random.uniform(-0.5, 0.5))

    close = pd.Series(closes, index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = close + 0.3
    low = close - 0.3
    volume = pd.Series([1000] * n, index=dates)

    return pd.DataFrame({
        "Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume
    })


def test_analyze_series_returns_rows_after_warmup():

    data = _make_ohlcv(n=150)

    result = _analyze_series(data)

    assert not result.empty
    assert len(result) == 150 - WARMUP
    assert set(result.columns) == {"Bias", "Decision", "Confidence", "Price", "ATR"}


def test_analyze_series_bias_values_are_valid():

    data = _make_ohlcv(n=150, drift=0.3)

    result = _analyze_series(data)

    assert set(result["Bias"].unique()).issubset({"Bullish", "Bearish", "Neutral"})


def test_analyze_series_empty_on_too_short_data():

    data = _make_ohlcv(n=30)

    result = _analyze_series(data)

    assert result.empty
