import yfinance as yf
import pandas as pd

# Updated: 2026-07-28 - feeds the mobile app's candlestick chart (tap a
# trade -> see its symbol's recent candles). Periodic-refresh data, not a
# true live/tick feed - see refresh_candles.py for the cadence. Kept as its
# own engine (one responsibility: fetch + shape candles) rather than folded
# into an existing engine.


def fetch_candles(symbol, period="5d", interval="15m"):
    """
    Recent OHLC candles for a symbol, shaped for the mobile app's chart.

    Parameters
    ----------
    symbol : str
        A yfinance ticker (e.g. "RELIANCE.NS", "^NSEI").
    period, interval : str
        Passed straight to yfinance - same 60d/5m-class limits as every
        other intraday backtest in this codebase apply here too.

    Returns
    -------
    list of dict, oldest first: {"Timestamp", "Open", "High", "Low", "Close"}.
    Empty list if no data is available for this symbol.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return []

    open_ = data["Open"]
    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    if isinstance(open_, pd.DataFrame):
        open_ = open_.iloc[:, 0]

    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]

    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    candles = []

    for timestamp in data.index:
        candles.append({
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Open": round(float(open_.loc[timestamp]), 2),
            "High": round(float(high.loc[timestamp]), 2),
            "Low": round(float(low.loc[timestamp]), 2),
            "Close": round(float(close.loc[timestamp]), 2),
        })

    return candles
