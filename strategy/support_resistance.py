import pandas as pd


def get_support_resistance(data, lookback=20):
    """
    Detect nearest Support and Resistance

    Parameters
    ----------
    data : DataFrame

    lookback : int
        Number of candles

    Returns
    -------
    dict
    """

    highs = data["High"]
    lows = data["Low"]

    # Support latest yfinance
    if isinstance(highs, pd.DataFrame):
        highs = highs.iloc[:, 0]

    if isinstance(lows, pd.DataFrame):
        lows = lows.iloc[:, 0]

    recent_highs = highs.tail(lookback)
    recent_lows = lows.tail(lookback)

    resistance = recent_highs.max()
    support = recent_lows.min()

    current_price = data["Close"]

    if isinstance(current_price, pd.DataFrame):
        current_price = current_price.iloc[:, 0]

    current_price = current_price.iloc[-1]

    resistance_distance = resistance - current_price
    support_distance = current_price - support

    return {

        "Current Price": round(current_price, 2),

        "Resistance": round(resistance, 2),

        "Support": round(support, 2),

        "Distance To Resistance": round(resistance_distance, 2),

        "Distance To Support": round(support_distance, 2)

    }