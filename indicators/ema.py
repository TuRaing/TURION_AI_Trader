import pandas as pd

def calculate_ema(data, period):

    close = data["Close"]

    # yfinance new version support
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    ema = close.ewm(span=period, adjust=False).mean()

    return ema