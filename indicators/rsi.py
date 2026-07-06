import pandas as pd

def calculate_rsi(data, period=14):

    close = data["Close"]

    # Support new yfinance versions
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi