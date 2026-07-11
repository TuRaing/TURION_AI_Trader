import pandas as pd


def _to_series(column):

    if isinstance(column, pd.DataFrame):
        return column.iloc[:, 0]

    return column


def is_doji(open_, high, low, close, threshold=0.1):

    candle_range = high - low

    if candle_range == 0:
        return False

    body = abs(close - open_)

    return (body / candle_range) <= threshold


def is_hammer(open_, high, low, close):

    candle_range = high - low

    if candle_range == 0:
        return False

    body = abs(close - open_)
    lower_wick = min(open_, close) - low
    upper_wick = high - max(open_, close)

    return (
        lower_wick >= body * 2
        and upper_wick <= body * 0.5
        and body / candle_range <= 0.4
    )


def is_shooting_star(open_, high, low, close):

    candle_range = high - low

    if candle_range == 0:
        return False

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    return (
        upper_wick >= body * 2
        and lower_wick <= body * 0.5
        and body / candle_range <= 0.4
    )


def is_bullish_engulfing(prev_open, prev_close, open_, close):

    prev_bearish = prev_close < prev_open
    curr_bullish = close > open_

    return prev_bearish and curr_bullish and close >= prev_open and open_ <= prev_close


def is_bearish_engulfing(prev_open, prev_close, open_, close):

    prev_bullish = prev_close > prev_open
    curr_bearish = close < open_

    return prev_bullish and curr_bearish and open_ >= prev_close and close <= prev_open


def get_candlestick_pattern(data):
    """
    Detect the Candlestick Pattern on the most recent candle,
    checked against Doji, Hammer, Shooting Star and Engulfing shapes.

    Returns
    -------
    dict
    """

    open_col = _to_series(data["Open"])
    high_col = _to_series(data["High"])
    low_col = _to_series(data["Low"])
    close_col = _to_series(data["Close"])

    open_ = float(open_col.iloc[-1])
    high = float(high_col.iloc[-1])
    low = float(low_col.iloc[-1])
    close = float(close_col.iloc[-1])

    prev_open = float(open_col.iloc[-2])
    prev_close = float(close_col.iloc[-2])

    if is_bullish_engulfing(prev_open, prev_close, open_, close):
        pattern, bias = "Bullish Engulfing", "Bullish"

    elif is_bearish_engulfing(prev_open, prev_close, open_, close):
        pattern, bias = "Bearish Engulfing", "Bearish"

    elif is_hammer(open_, high, low, close):
        pattern, bias = "Hammer", "Bullish"

    elif is_shooting_star(open_, high, low, close):
        pattern, bias = "Shooting Star", "Bearish"

    elif is_doji(open_, high, low, close):
        pattern, bias = "Doji", "Neutral"

    else:
        pattern, bias = "No Pattern", "Neutral"

    return {
        "Pattern": pattern,
        "Bias": bias
    }
