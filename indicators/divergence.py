# Added 09-Aug-2026 - RSI Divergence detection, the "less commonly-
# followed technique" candidate identified while diagnosing why the
# plain RSI>=50/<50 signal is weak (see strategy/rsi_divergence_
# backtest.py for the full reasoning and the backtest that uses this).
#
# Bearish divergence: price makes a HIGHER high, but RSI makes a LOWER
# high at that same point - momentum is weakening even though price
# is still climbing, an early warning of a reversal DOWN.
# Bullish divergence: price makes a LOWER low, but RSI makes a HIGHER
# low - momentum improving even though price is still falling, an
# early warning of a reversal UP.
#
# Pure functions, deliberately separate from the swing-point DETECTION
# itself (reuses indicators/market_structure.py's find_swing_points()
# rather than re-implementing it - divergence only needs to compare
# RSI's value AT each already-found price swing, not find its own).


def is_bearish_divergence(prev_price, prev_rsi, curr_price, curr_rsi):
    """
    True if price made a higher high (curr > prev) while RSI made a
    lower high (curr < prev) at the same two swing points.
    """

    return curr_price > prev_price and curr_rsi < prev_rsi


def is_bullish_divergence(prev_price, prev_rsi, curr_price, curr_rsi):
    """
    True if price made a lower low (curr < prev) while RSI made a
    higher low (curr > prev) at the same two swing points.
    """

    return curr_price < prev_price and curr_rsi > prev_rsi
