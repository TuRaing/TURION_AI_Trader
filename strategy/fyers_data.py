import datetime
import time

import pandas as pd
import requests

from strategy.fyers_auth import _app_id, get_access_token

# Added 04-Aug-2026 - a thin adapter that fetches real candles from Fyers
# and returns them in the SAME shape yfinance's yf.download() does
# (DatetimeIndex, Open/High/Low/Close/Volume columns, tz-aware
# Asia/Kolkata for intraday) - so every existing analysis function
# (analyze_symbol, calculate_rsi, calculate_atr, get_market_structure,
# etc.) keeps working completely unchanged. This is the ONLY new piece
# needed to point the existing engines at Fyers instead of yfinance -
# see strategy/fyers_watchlist_scanner.py and strategy/
# fyers_multi_timeframe_engine.py, which are otherwise near-identical
# copies of their yfinance-based originals with just the download call
# swapped.

DATA_BASE_URL = "https://api-t1.fyers.in/data"

# Fyers' per-request day-limit for intraday resolutions (tested 04-Aug:
# 100 days ok, 120+ days "Invalid input"). UPDATED 05-Aug: "D" is NOT
# unlimited - Fyers caps it at 366 days/request too ("Date range cannot
# exceed 366 days for 1D, 1W, and 1M resolutions"). 04-Aug's "tested 20
# years, no issues" note was wrong - every daily test that day happened
# to use a <=366-day single request (e.g. one calendar year at a time),
# never an actual >366-day single call, so the real per-request limit
# went unnoticed until a real multi-year backtest hit it here.
MAX_DAYS_PER_REQUEST = {
    "1": 100, "3": 100, "5": 100, "10": 100, "15": 100, "30": 100, "60": 100,
    "D": 366,
}

RESOLUTION_MAP = {
    "1m": "1", "3m": "3", "5m": "5", "10m": "10", "15m": "15",
    "30m": "30", "60m": "60", "1h": "60", "1d": "D",
}

# Rough calendar-day equivalents for yfinance-style period strings, used
# to compute a range_from/range_to window. Slightly generous (calendar
# days, not trading days) - harmless, Fyers just returns however many
# real trading candles fall inside the window.
PERIOD_TO_DAYS = {
    "5d": 5, "7d": 7, "60d": 60, "1mo": 31, "3mo": 93, "6mo": 186,
    "1y": 366, "2y": 732, "5y": 1830,
}


def symbol_to_fyers(symbol):
    """
    Translates this repo's existing yfinance-style symbols to Fyers'
    format - so data/watchlist.py and every symbol dict already in the
    codebase can be reused as-is, no need to maintain a second symbol list.

    "RELIANCE.NS" -> "NSE:RELIANCE-EQ"
    "^NSEI"       -> "NSE:NIFTY50-INDEX"
    "^NSEBANK"    -> "NSE:NIFTYBANK-INDEX"
    """

    if symbol == "^NSEI":
        return "NSE:NIFTY50-INDEX"

    if symbol == "^NSEBANK":
        return "NSE:NIFTYBANK-INDEX"

    if symbol == "^INDIAVIX":
        return "NSE:INDIAVIX-INDEX"

    if symbol.endswith(".NS"):
        return f"NSE:{symbol[:-3]}-EQ"

    return symbol


def _headers():
    return {"Authorization": f"{_app_id()}:{get_access_token()}"}


def _fetch_range(fyers_symbol, resolution, range_from, range_to, attempts=3, backoff_seconds=2):
    """
    Same per-call resilience philosophy as strategy/multi_timeframe_
    engine.py's _fetch_with_retry - Fyers rate-limits (HTTP 200 with
    code -429/"request limit reached" in the body, not an HTTP 429)
    when many symbols are fetched back-to-back (seen 04-Aug scanning
    the full 52-symbol watchlist). Retries with backoff before giving
    up, rather than letting one rate-limited symbol abort the whole run.
    """

    last_error = None

    for attempt in range(attempts):

        response = requests.get(
            f"{DATA_BASE_URL}/history",
            headers=_headers(),
            params={
                "symbol": fyers_symbol,
                "resolution": resolution,
                "date_format": "1",
                "range_from": range_from.isoformat(),
                "range_to": range_to.isoformat(),
                "cont_flag": "1",
            },
            timeout=20,
        )

        data = response.json()

        if data.get("s") == "no_data":
            return []

        if data.get("s") == "ok":
            return data.get("candles", [])

        last_error = data

        if "limit" in str(data.get("message", "")).lower() and attempt < attempts - 1:
            time.sleep(backoff_seconds * (attempt + 1))
            continue

        break

    raise RuntimeError(f"Fyers history fetch failed for {fyers_symbol}: {last_error}")


def fyers_download(symbol, period="6mo", interval="1d"):
    """
    Drop-in replacement for `yf.download(symbol, period=period,
    interval=interval, progress=False)` for a SINGLE symbol - same
    output shape (DatetimeIndex named appropriately, Open/High/Low/
    Close/Volume float columns), sourced from real Fyers data instead.

    Paginates automatically past Fyers' 100-day-per-request limit for
    intraday resolutions, so a caller can ask for period="60d" the same
    way it always has.

    Returns
    -------
    pd.DataFrame, empty if no data (matches yfinance's behavior on a
    bad/delisted symbol rather than raising).
    """

    resolution = RESOLUTION_MAP.get(interval)

    if resolution is None:
        raise ValueError(f"Unsupported interval {interval!r} - add it to RESOLUTION_MAP")

    days = PERIOD_TO_DAYS.get(period)

    if days is None:
        raise ValueError(f"Unsupported period {period!r} - add it to PERIOD_TO_DAYS")

    fyers_symbol = symbol_to_fyers(symbol)

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    max_span = MAX_DAYS_PER_REQUEST.get(resolution, 100)

    all_candles = []
    chunk_start = start

    while chunk_start <= end:

        chunk_end = min(chunk_start + datetime.timedelta(days=max_span - 1), end)

        all_candles.extend(_fetch_range(fyers_symbol, resolution, chunk_start, chunk_end))

        chunk_start = chunk_end + datetime.timedelta(days=1)

    if not all_candles:
        return pd.DataFrame()

    frame = pd.DataFrame(all_candles, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
    frame = frame.drop_duplicates(subset="Timestamp").sort_values("Timestamp")

    frame.index = (
        pd.to_datetime(frame["Timestamp"], unit="s", utc=True)
        .dt.tz_convert("Asia/Kolkata")
    )
    frame.index.name = "Datetime" if resolution != "D" else "Date"

    return frame[["Open", "High", "Low", "Close", "Volume"]]
