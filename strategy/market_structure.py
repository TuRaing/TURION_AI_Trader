import pandas as pd


def find_swing_highs(data):
    """
    Find Swing Highs
    """

    highs = data["High"]

    # Support latest yfinance versions
    if isinstance(highs, pd.DataFrame):
        highs = highs.iloc[:, 0]

    swing_highs = []

    for i in range(1, len(highs) - 1):

        if highs.iloc[i] > highs.iloc[i - 1] and highs.iloc[i] > highs.iloc[i + 1]:

            swing_highs.append({
                "Index": highs.index[i],
                "Price": float(highs.iloc[i])
            })

    return swing_highs


def find_swing_lows(data):
    """
    Find Swing Lows
    """

    lows = data["Low"]

    if isinstance(lows, pd.DataFrame):
        lows = lows.iloc[:, 0]

    swing_lows = []

    for i in range(1, len(lows) - 1):

        if lows.iloc[i] < lows.iloc[i - 1] and lows.iloc[i] < lows.iloc[i + 1]:

            swing_lows.append({
                "Index": lows.index[i],
                "Price": float(lows.iloc[i])
            })

    return swing_lows


def get_market_structure(data):

    swing_highs = find_swing_highs(data)
    swing_lows = find_swing_lows(data)

    trend = detect_trend(
        swing_highs,
        swing_lows
    )

    return {

        "Swing Highs": swing_highs,

        "Swing Lows": swing_lows,

        "Trend Analysis": trend
    }

def detect_trend(swing_highs, swing_lows):
    """
    Detect HH, HL, LH, LL and Trend
    """

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            "Trend": "UNKNOWN",
            "Structure": "Not enough swing data"
        }

    previous_high = swing_highs[-2]["Price"]
    latest_high = swing_highs[-1]["Price"]

    previous_low = swing_lows[-2]["Price"]
    latest_low = swing_lows[-1]["Price"]

    higher_high = latest_high > previous_high
    lower_high = latest_high < previous_high

    higher_low = latest_low > previous_low
    lower_low = latest_low < previous_low

    if higher_high and higher_low:
        trend = "🟢 Bullish"

    elif lower_high and lower_low:
        trend = "🔴 Bearish"

    else:
        trend = "🟡 Sideways"

    return {

        "Previous High": previous_high,
        "Latest High": latest_high,

        "Previous Low": previous_low,
        "Latest Low": latest_low,

        "Higher High": higher_high,
        "Higher Low": higher_low,

        "Lower High": lower_high,
        "Lower Low": lower_low,

        "Trend": trend
    }