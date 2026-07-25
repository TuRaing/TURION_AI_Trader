import pandas as pd


def calculate_cpr(data):
    """
    Central Pivot Range - Pivot, Top Central (TC), Bottom Central (BC),
    plus the standard R1-R3/S1-S3 levels. Each row's CPR is derived from
    the *previous* row's High/Low/Close, matching how CPR is normally
    read (today's range drawn from yesterday's candle) - pass daily
    candles for the traditional daily CPR, or resample first if a
    different anchor period is needed.

    Note: TC can land below BC on some days ("inverted CPR") - that is
    expected CPR behavior, not a bug in this calculation.

    Parameters
    ----------
    data : DataFrame with High/Low/Close columns

    Returns
    -------
    DataFrame indexed the same as data, columns:
    Pivot, TC, BC, R1, R2, R3, S1, S2, S3.
    First row is NaN - no previous row to derive it from.
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

    pivot = (prev_high + prev_low + prev_close) / 3
    bc = (prev_high + prev_low) / 2
    tc = (2 * pivot) - bc

    prev_range = prev_high - prev_low

    r1 = (2 * pivot) - prev_low
    s1 = (2 * pivot) - prev_high

    r2 = pivot + prev_range
    s2 = pivot - prev_range

    r3 = prev_high + 2 * (pivot - prev_low)
    s3 = prev_low - 2 * (prev_high - pivot)

    return pd.DataFrame({
        "Pivot": pivot,
        "TC": tc,
        "BC": bc,
        "R1": r1,
        "R2": r2,
        "R3": r3,
        "S1": s1,
        "S2": s2,
        "S3": s3,
    })
