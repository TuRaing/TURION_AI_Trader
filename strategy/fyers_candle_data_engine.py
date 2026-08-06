from strategy.fyers_data import fyers_download

# Added 06-Aug-2026 - Fyers-sourced counterpart to strategy/candle_
# data_engine.py, per this repo's engine-separation rule. Feeds the
# mobile app's candlestick chart when a Fyers trade (Swing, Intraday,
# or an options strategy's underlying) is tapped - candle_data_
# engine.py itself is untouched, still yfinance-only, still feeding
# the original chart via candles.json.


def fetch_candles(symbol, period="5d", interval="15m"):
    """
    Recent OHLC candles for a symbol, shaped for the mobile app's
    chart - same output shape as strategy.candle_data_engine.
    fetch_candles, sourced from Fyers instead of yfinance.

    Parameters
    ----------
    symbol : str
        A yfinance-style ticker (e.g. "RELIANCE.NS", "^NSEI") -
        strategy/fyers_data.py's symbol_to_fyers() converts it to the
        real Fyers symbol internally.
    period, interval : str
        Passed straight to fyers_download.

    Returns
    -------
    list of dict, oldest first: {"Timestamp", "Open", "High", "Low", "Close"}.
    Empty list if no data is available for this symbol.
    """

    data = fyers_download(symbol, period=period, interval=interval)

    if data is None or data.empty:
        return []

    candles = []

    for timestamp, row in data.iterrows():
        candles.append({
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Open": round(float(row["Open"]), 2),
            "High": round(float(row["High"]), 2),
            "Low": round(float(row["Low"]), 2),
            "Close": round(float(row["Close"]), 2),
        })

    return candles
