import pandas as pd


def calculate_atr(data, period=14):

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]

    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = true_range.rolling(window=period).mean()

    return atr
