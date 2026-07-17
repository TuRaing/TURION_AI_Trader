from strategy.multi_timeframe_engine import analyze_timeframes


def _analysis(bias, decision="BUY", confidence=70, price=100, atr=2):
    return {
        "Price": price, "ATR": atr, "Signal": decision, "Filter Notes": [],
        "Decision": decision, "Bias": bias, "Confidence": confidence,
        "Candle Pattern": "No Pattern",
    }


def test_all_three_aligned_bullish():
    result = analyze_timeframes({
        "15m": _analysis("Bullish"),
        "5m": _analysis("Bullish", confidence=75, price=105, atr=3),
        "1m": _analysis("Bullish"),
    })

    assert result["Aligned"] is True
    assert result["Bias"] == "Bullish"
    # entry (5m) timeframe's fields become the trade's
    assert result["Decision"] == "BUY"
    assert result["Confidence"] == 75
    assert result["Price"] == 105
    assert result["ATR"] == 3


def test_all_three_aligned_bearish():
    result = analyze_timeframes({
        "15m": _analysis("Bearish", decision="SELL"),
        "5m": _analysis("Bearish", decision="SELL"),
        "1m": _analysis("Bearish", decision="SELL"),
    })

    assert result["Aligned"] is True
    assert result["Bias"] == "Bearish"


def test_trend_neutral_is_never_aligned():
    result = analyze_timeframes({
        "15m": _analysis("Neutral", decision="NO TRADE"),
        "5m": _analysis("Neutral", decision="NO TRADE"),
        "1m": _analysis("Neutral", decision="NO TRADE"),
    })

    assert result["Aligned"] is False


def test_entry_disagrees_with_trend_not_aligned():
    result = analyze_timeframes({
        "15m": _analysis("Bullish"),
        "5m": _analysis("Bearish", decision="SELL"),
        "1m": _analysis("Bullish"),
    })

    assert result["Aligned"] is False
    assert "Bullish" in result["Reason"]
    assert "Bearish" in result["Reason"]


def test_timing_disagrees_not_aligned():
    result = analyze_timeframes({
        "15m": _analysis("Bullish"),
        "5m": _analysis("Bullish"),
        "1m": _analysis("Bearish", decision="SELL"),
    })

    assert result["Aligned"] is False


def test_missing_timeframe_data_is_never_aligned():
    result = analyze_timeframes({
        "15m": _analysis("Bullish"),
        "5m": _analysis("Bullish"),
        "1m": None,
    })

    assert result["Aligned"] is False
    assert "Missing data" in result["Reason"]


def test_all_missing_is_never_aligned():
    result = analyze_timeframes({"15m": None, "5m": None, "1m": None})

    assert result["Aligned"] is False
