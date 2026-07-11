from strategy.signal_engine import (
    generate_signal,
    apply_market_structure_filter,
    apply_support_resistance_filter,
    apply_volume_filter,
    apply_candlestick_filter,
    generate_filtered_signal,
)


# ---------------- generate_signal ----------------

def test_buy_signal():
    assert generate_signal(101, 100, 65) == "BUY"


def test_sell_signal():
    assert generate_signal(99, 100, 35) == "SELL"


def test_no_trade_when_rsi_neutral():
    assert generate_signal(101, 100, 50) == "NO TRADE"


def test_no_trade_when_trend_and_momentum_disagree():
    # ema bullish but rsi weak
    assert generate_signal(101, 100, 30) == "NO TRADE"


# ---------------- market structure filter ----------------

def test_structure_blocks_buy_against_trend():
    signal, note = apply_market_structure_filter("BUY", "🔴 Bearish")
    assert signal == "NO TRADE"
    assert note is not None


def test_structure_allows_buy_with_trend():
    signal, note = apply_market_structure_filter("BUY", "🟢 Bullish")
    assert signal == "BUY"
    assert note is None


# ---------------- support / resistance filter ----------------

def _levels(price, dist_res, dist_sup):
    return {
        "Current Price": price,
        "Resistance": price + dist_res,
        "Support": price - dist_sup,
        "Distance To Resistance": dist_res,
        "Distance To Support": dist_sup,
    }


def test_sr_blocks_buy_near_resistance():
    # buffer = 100 * 0.1/100 = 0.1; resistance distance 0.05 <= buffer -> blocked
    signal, note = apply_support_resistance_filter("BUY", _levels(100, 0.05, 50))
    assert signal == "NO TRADE"
    assert note is not None


def test_sr_allows_buy_far_from_resistance():
    signal, note = apply_support_resistance_filter("BUY", _levels(100, 50, 50))
    assert signal == "BUY"
    assert note is None


# ---------------- volume filter ----------------

def test_volume_filter_skipped_when_no_volume():
    # index tickers report zero avg volume - filter must not block
    va = {"Average Volume": 0, "Volume Ratio": 0, "Spike": False}
    signal, note = apply_volume_filter("BUY", va)
    assert signal == "BUY"
    assert note is None


def test_volume_filter_blocks_low_volume():
    va = {"Average Volume": 1000, "Volume Ratio": 0.2, "Spike": False}
    signal, note = apply_volume_filter("BUY", va)
    assert signal == "NO TRADE"
    assert note is not None


def test_volume_filter_allows_healthy_volume():
    va = {"Average Volume": 1000, "Volume Ratio": 1.2, "Spike": True}
    signal, note = apply_volume_filter("BUY", va)
    assert signal == "BUY"
    assert note is None


# ---------------- candlestick filter ----------------

def test_candle_blocks_buy_on_bearish_pattern():
    signal, note = apply_candlestick_filter("BUY", {"Pattern": "Shooting Star", "Bias": "Bearish"})
    assert signal == "NO TRADE"
    assert note is not None


def test_candle_allows_buy_on_neutral_pattern():
    signal, note = apply_candlestick_filter("BUY", {"Pattern": "No Pattern", "Bias": "Neutral"})
    assert signal == "BUY"
    assert note is None


# ---------------- full pipeline ----------------

def test_filtered_signal_passes_all_filters():
    levels = _levels(100, 50, 50)
    va = {"Average Volume": 1000, "Volume Ratio": 1.2, "Spike": False}
    candle = {"Pattern": "No Pattern", "Bias": "Neutral"}

    signal, notes = generate_filtered_signal(101, 100, 65, "🟢 Bullish", levels, va, candle)

    assert signal == "BUY"
    assert notes == []


def test_filtered_signal_blocked_by_one_filter():
    levels = _levels(100, 0.05, 50)  # too close to resistance
    va = {"Average Volume": 1000, "Volume Ratio": 1.2, "Spike": False}
    candle = {"Pattern": "No Pattern", "Bias": "Neutral"}

    signal, notes = generate_filtered_signal(101, 100, 65, "🟢 Bullish", levels, va, candle)

    assert signal == "NO TRADE"
    assert len(notes) >= 1
