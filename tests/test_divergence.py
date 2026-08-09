from indicators.divergence import is_bearish_divergence, is_bullish_divergence


def test_bearish_divergence_price_higher_high_rsi_lower_high():
    # Price: 24500 -> 24600 (higher high). RSI: 75 -> 68 (lower high).
    assert is_bearish_divergence(prev_price=24500, prev_rsi=75, curr_price=24600, curr_rsi=68) is True


def test_bearish_divergence_false_when_rsi_also_makes_higher_high():
    # No divergence - RSI confirms the higher high, doesn't diverge.
    assert is_bearish_divergence(prev_price=24500, prev_rsi=65, curr_price=24600, curr_rsi=72) is False


def test_bearish_divergence_false_when_price_does_not_make_higher_high():
    assert is_bearish_divergence(prev_price=24500, prev_rsi=75, curr_price=24400, curr_rsi=68) is False


def test_bullish_divergence_price_lower_low_rsi_higher_low():
    # Price: 24500 -> 24400 (lower low). RSI: 25 -> 32 (higher low).
    assert is_bullish_divergence(prev_price=24500, prev_rsi=25, curr_price=24400, curr_rsi=32) is True


def test_bullish_divergence_false_when_rsi_also_makes_lower_low():
    assert is_bullish_divergence(prev_price=24500, prev_rsi=35, curr_price=24400, curr_rsi=28) is False


def test_bullish_divergence_false_when_price_does_not_make_lower_low():
    assert is_bullish_divergence(prev_price=24500, prev_rsi=25, curr_price=24600, curr_rsi=32) is False
