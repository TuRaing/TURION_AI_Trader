import pandas as pd

from indicators.supertrend import calculate_supertrend


def _make_trend(closes):

    return pd.DataFrame({
        "High": [c + 1 for c in closes],
        "Low": [c - 1 for c in closes],
        "Close": closes,
    })


def test_leading_rows_before_atr_window_are_nan():
    data = _make_trend([100 + i for i in range(5)])

    result = calculate_supertrend(data, period=10)

    assert result["Supertrend"].iloc[:5].isna().all()
    assert result["Direction"].iloc[:5].isna().all()


def test_steady_uptrend_settles_in_up_direction_below_price():
    closes = [100 + i * 2 for i in range(30)]
    data = _make_trend(closes)

    result = calculate_supertrend(data, period=10, multiplier=3.0)

    tail = result.iloc[-5:]
    assert (tail["Direction"] == "up").all()
    assert (tail["Supertrend"] < data["Close"].iloc[-5:]).all()


def test_steady_downtrend_settles_in_down_direction_above_price():
    closes = [200 - i * 2 for i in range(30)]
    data = _make_trend(closes)

    result = calculate_supertrend(data, period=10, multiplier=3.0)

    tail = result.iloc[-5:]
    assert (tail["Direction"] == "down").all()
    assert (tail["Supertrend"] > data["Close"].iloc[-5:]).all()
