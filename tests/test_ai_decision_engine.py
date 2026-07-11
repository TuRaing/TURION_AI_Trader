from strategy.ai_decision_engine import (
    get_ai_decision,
    score_ema_trend,
    score_rsi,
    score_market_structure,
    score_levels,
    score_candlestick,
)


# ---------------- individual scorers ----------------

def test_score_ema_trend():
    assert score_ema_trend(101, 100) == 1
    assert score_ema_trend(99, 100) == -1


def test_score_rsi():
    assert score_rsi(65) == 1
    assert score_rsi(35) == -1
    assert score_rsi(50) == 0


def test_score_market_structure():
    assert score_market_structure("🟢 Bullish") == 1
    assert score_market_structure("🔴 Bearish") == -1
    assert score_market_structure("🟡 Sideways") == 0


def test_score_candlestick():
    assert score_candlestick({"Bias": "Bullish"}) == 1
    assert score_candlestick({"Bias": "Bearish"}) == -1
    assert score_candlestick({"Bias": "Neutral"}) == 0


def _levels(price, dist_res, dist_sup):
    return {
        "Current Price": price,
        "Distance To Resistance": dist_res,
        "Distance To Support": dist_sup,
    }


def test_score_levels_near_support_is_bullish():
    # buffer = 100 * 0.15/100 = 0.15; support distance 0.05 <= buffer -> +1
    assert score_levels(_levels(100, 50, 0.05)) == 1


def test_score_levels_near_resistance_is_bearish():
    assert score_levels(_levels(100, 0.05, 50)) == -1


def test_score_levels_mid_range_neutral():
    assert score_levels(_levels(100, 50, 50)) == 0


# ---------------- full decision ----------------

def _neutral_candle():
    return {"Pattern": "No Pattern", "Bias": "Neutral"}


def _no_spike():
    return {"Average Volume": 1000, "Volume Ratio": 1.0, "Spike": False}


def test_strong_bullish_gives_buy():
    levels = _levels(100, 50, 0.05)  # near support -> +1
    ai = get_ai_decision(101, 100, 65, "🟢 Bullish", levels, _no_spike(),
                         {"Pattern": "Hammer", "Bias": "Bullish"})
    assert ai["Bias"] == "Bullish"
    assert ai["Confidence"] == 100.0
    assert ai["Decision"] == "BUY"


def test_strong_bearish_gives_sell():
    levels = _levels(100, 0.05, 50)  # near resistance -> -1
    ai = get_ai_decision(99, 100, 35, "🔴 Bearish", levels, _no_spike(),
                         {"Pattern": "Shooting Star", "Bias": "Bearish"})
    assert ai["Bias"] == "Bearish"
    assert ai["Decision"] == "SELL"


def test_conflicting_signals_no_trade():
    levels = _levels(100, 50, 50)  # neutral
    # ema bullish (+1), rsi weak (0), structure sideways (0), levels 0, candle neutral 0
    ai = get_ai_decision(101, 100, 50, "🟡 Sideways", levels, _no_spike(), _neutral_candle())
    assert ai["Confidence"] < 60
    assert ai["Decision"] == "NO TRADE"


def test_volume_spike_boosts_confidence():
    levels = _levels(100, 50, 50)  # neutral (0)
    spike = {"Average Volume": 1000, "Volume Ratio": 2.0, "Spike": True}
    # ema +1, rsi +1, structure +1, levels 0, candle 0 -> total 3, conf 60, +10 spike = 70
    ai = get_ai_decision(101, 100, 65, "🟢 Bullish", levels, spike, _neutral_candle())
    assert ai["Confidence"] == 70.0


def test_confidence_capped_at_100():
    levels = _levels(100, 50, 0.05)  # +1 (all five bullish -> 100 already)
    spike = {"Average Volume": 1000, "Volume Ratio": 2.0, "Spike": True}
    ai = get_ai_decision(101, 100, 65, "🟢 Bullish", levels, spike,
                         {"Pattern": "Hammer", "Bias": "Bullish"})
    assert ai["Confidence"] == 100.0  # not 110
