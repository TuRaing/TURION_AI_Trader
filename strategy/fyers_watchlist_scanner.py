import time

from strategy.fyers_data import fyers_download
from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES

# Small pause between per-symbol Fyers calls - proactively avoids the
# rate-limiting seen 04-Aug scanning the full 52-symbol watchlist back-
# to-back (on top of fyers_data.py's own retry-with-backoff safety net).
REQUEST_DELAY_SECONDS = 0.3

# Added 04-Aug-2026 - Fyers-sourced counterpart to strategy/
# watchlist_scanner.py, per this repo's "never modify a working module,
# add new functionality as a separate engine" rule. analyze_symbol/
# MIN_CANDLES are imported and reused as-is (they only ever touch the
# DataFrame, never the data source) - the ONLY thing that changes here
# is where the OHLCV data comes from. See strategy/fyers_data.py for
# the actual Fyers <-> yfinance-shape adapter.
#
# yfinance's yf.download() can batch many tickers in one call; Fyers'
# history endpoint is one symbol per call, so this loops instead - a
# real behavioral difference (more HTTP calls, so somewhat slower), but
# functionally equivalent output.

__all__ = ["download_watchlist", "analyze_symbol", "MIN_CANDLES"]


def download_watchlist(symbols, period="6mo", interval="1d"):
    """
    Same contract as strategy.watchlist_scanner.download_watchlist -
    {display_name: yfinance_ticker} in, {display_name: DataFrame or
    None} out - just sourced from Fyers instead of yfinance.
    """

    frames = {}

    for name, ticker in symbols.items():

        try:
            frame = fyers_download(ticker, period, interval)

        except Exception as error:

            print(f"Fyers fetch failed for {name} ({ticker}): {error}")
            frame = None

        if frame is not None and frame.empty:
            frame = None

        frames[name] = frame

        time.sleep(REQUEST_DELAY_SECONDS)

    return frames


def scan_watchlist(symbols, period="6mo", interval="1d"):
    """
    Same contract as strategy.watchlist_scanner.scan_watchlist, sourced
    from Fyers.
    """

    frames = download_watchlist(symbols, period, interval)

    results = []

    for name, ticker in symbols.items():

        try:

            frame = frames[name]

            if frame is None or len(frame) < MIN_CANDLES:
                continue

            analysis = analyze_symbol(frame)

            results.append({
                "Name": name,
                "Symbol": ticker,
                "Price": analysis["Price"],
                "Decision": analysis["Decision"],
                "Bias": analysis["Bias"],
                "Confidence": analysis["Confidence"],
                "ATR": analysis["ATR"],
                "Candle Pattern": analysis["Candle Pattern"],
            })

        except Exception as error:

            print(f"Skipped {name} ({ticker}): {error}")

    results.sort(key=lambda r: r["Confidence"], reverse=True)

    return results
