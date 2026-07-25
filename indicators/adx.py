import pandas as pd


def calculate_adx(data, period=14):
    """
    Average Directional Index - measures trend STRENGTH (not direction).
    Standard Wilder's smoothing method.

    High ADX (typically >25) = a strong trend is underway (up or down).
    Low ADX (typically <20) = weak/choppy, range-bound conditions.

    Returns
    -------
    Series indexed the same as data
    """

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]

    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move.clip(lower=0)
    minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move.clip(lower=0)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing (equivalent to an EMA with alpha=1/period)
    smoothed_tr = true_range.ewm(alpha=1 / period, adjust=False).mean()
    smoothed_plus_dm = plus_dm.ewm(alpha=1 / period, adjust=False).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=1 / period, adjust=False).mean()

    plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx
