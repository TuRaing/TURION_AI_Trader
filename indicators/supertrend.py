import pandas as pd

from indicators.atr import calculate_atr


def calculate_supertrend(data, period=10, multiplier=3.0):
    """
    Supertrend - ATR-based trend-following overlay. Reuses this repo's
    own ATR engine (indicators/atr.py) instead of recomputing True
    Range, so Supertrend agrees with the Risk Engine's stop-loss sizing
    and the ADX engine on the same ATR values.

    Parameters
    ----------
    data : DataFrame with High/Low/Close columns
    period : int
        ATR lookback period.
    multiplier : float
        Band distance from the HL2 midpoint, in ATR units.

    Returns
    -------
    DataFrame indexed the same as data, columns:
    Supertrend (the trend line level) and Direction ("up"/"down").
    First `period` rows are NaN/None (ATR needs a full window).
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

    atr = calculate_atr(data, period=period)

    hl2 = (high + low) / 2

    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()

    supertrend = pd.Series(index=data.index, dtype=float)
    direction = pd.Series(index=data.index, dtype=object)

    for i in range(len(data)):

        if i == 0 or pd.isna(atr.iloc[i]):
            continue

        if pd.isna(final_upper.iloc[i - 1]):
            final_upper.iloc[i] = basic_upper.iloc[i]
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:

            if close.iloc[i - 1] <= final_upper.iloc[i - 1]:
                final_upper.iloc[i] = min(basic_upper.iloc[i], final_upper.iloc[i - 1])
            else:
                final_upper.iloc[i] = basic_upper.iloc[i]

            if close.iloc[i - 1] >= final_lower.iloc[i - 1]:
                final_lower.iloc[i] = max(basic_lower.iloc[i], final_lower.iloc[i - 1])
            else:
                final_lower.iloc[i] = basic_lower.iloc[i]

        prev_direction = direction.iloc[i - 1]

        if prev_direction is None:
            direction.iloc[i] = "down" if close.iloc[i] < final_lower.iloc[i] else "up"

        elif prev_direction == "up":
            direction.iloc[i] = "down" if close.iloc[i] < final_lower.iloc[i] else "up"

        else:
            direction.iloc[i] = "up" if close.iloc[i] > final_upper.iloc[i] else "down"

        supertrend.iloc[i] = final_lower.iloc[i] if direction.iloc[i] == "up" else final_upper.iloc[i]

    return pd.DataFrame({"Supertrend": supertrend, "Direction": direction})
