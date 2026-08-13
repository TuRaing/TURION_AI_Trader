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
    "5d": 5, "7d": 7, "10d": 10, "60d": 60, "1mo": 31, "3mo": 93, "6mo": 186,
    "1y": 366, "2y": 732, "5y": 1830,
}


# Added 08-Aug-2026 - two symbols in data/watchlist.py have genuinely
# changed on Fyers since this project started, both from real corporate
# actions, not a mapping bug (verified against Fyers' public symbol
# master, https://public.fyers.in/sym_details/NSE_CM.csv and NSE_FO.csv):
#   - TATAMOTORS demerged into two listed entities - "TATA MOTORS
#     LIMITED" (NSE:TMCV-EQ, Commercial Vehicles) and "TATA MOTORS PASS
#     VEH LTD" (NSE:TMPV-EQ, Passenger Vehicles). Only TMPV is F&O-
#     eligible (confirmed against NSE_FO.csv's underlying list), so
#     that's the one this project's Watchlist/Best Trade engines should
#     track as "Tata Motors" going forward.
#   - LTIM (LTIMindtree) is now listed on Fyers as "LTM LIMITED"
#     (NSE:LTM-EQ) - the old "LTIM" ticker no longer resolves.
# These are explicit overrides (checked BEFORE the generic ".NS" rule
# below) rather than changes to data/watchlist.py's own symbol list -
# that list is shared with the yfinance-based engines too, and this
# fix is Fyers-side only.
_SYMBOL_OVERRIDES = {
    "TATAMOTORS.NS": "NSE:TMPV-EQ",
    "LTIM.NS": "NSE:LTM-EQ",
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

    if symbol in _SYMBOL_OVERRIDES:
        return _SYMBOL_OVERRIDES[symbol]

    if symbol.endswith(".NS"):
        return f"NSE:{symbol[:-3]}-EQ"

    return symbol


# Added 13-Aug-2026 - the missing piece for a real per-trade Delta/
# Theta split (see indicators/black_scholes.py's implied_volatility()/
# black_scholes_greeks(), added the same day) - both need time-to-
# expiry, which isn't stored on a trade directly but IS encoded in the
# option's own Fyers symbol. Two different formats in real use here,
# confirmed against actual live trade symbols (not guessed):
#   Weekly (NIFTY): "NSE:NIFTY2681124600PE" -> YY(26) + single-char
#     month code (1-9 for Jan-Sep, O/N/D for Oct/Nov/Dec - the
#     standard NSE derivatives symbol convention) + DD(11) + strike +
#     CE/PE. The exact expiry date is spelled out directly, no need to
#     compute which weekday it falls on.
#   Monthly (BANKNIFTY - weekly BANKNIFTY options were discontinued by
#     SEBI/NSE in Nov-2024, monthly-only since): "NSE:BANKNIFTY26AUG
#     58000CE" -> YY(26) + 3-letter month (AUG) + strike + CE/PE. The
#     exact day isn't in the symbol - NSE's monthly index-derivatives
#     expiry moved from Thursday to Tuesday, effective 01-Sep-2025, so
#     this computes the LAST TUESDAY of that month (confirmed current
#     as of 2026, not the pre-Sep-2025 Thursday convention).
_MONTH_CODE = {str(i): i for i in range(1, 10)}
_MONTH_CODE.update({"O": 10, "N": 11, "D": 12})
_MONTH_ABBR = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _last_tuesday(year, month):

    last_day = (datetime.date(year + (month == 12), month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    d = datetime.date(year, month, last_day)

    while d.weekday() != 1:  # Monday=0, Tuesday=1
        d -= datetime.timedelta(days=1)

    return d


def parse_option_expiry(fyers_option_symbol):
    """
    Extracts the expiry date from a Fyers NSE index-option symbol -
    handles both the weekly (exact date encoded) and monthly (last
    Tuesday of the month) formats described above.

    Returns
    -------
    datetime.date, or None if the symbol doesn't match either known
    format (a real possibility - don't guess, let the caller decide
    what to do with an unparseable symbol).
    """

    s = fyers_option_symbol.split(":")[-1]

    if s.endswith("CE") or s.endswith("PE"):
        s = s[:-2]

    i = 0
    while i < len(s) and s[i].isalpha():
        i += 1

    name, rest = s[:i], s[i:]

    if not name or len(rest) < 2 or not rest[:2].isdigit():
        return None

    year = 2000 + int(rest[:2])
    remainder = rest[2:]

    if len(remainder) >= 3 and remainder[:3] in _MONTH_ABBR:
        return _last_tuesday(year, _MONTH_ABBR[remainder[:3]])

    if len(remainder) >= 3 and remainder[0] in _MONTH_CODE and remainder[1:3].isdigit():

        month = _MONTH_CODE[remainder[0]]
        day = int(remainder[1:3])

        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None

    return None


def time_to_expiry_years(from_datetime, expiry_date, expiry_hour=15, expiry_minute=30):
    """
    Fraction of a year remaining from from_datetime (a naive datetime,
    matching this project's Entry/Exit Time storage convention) to the
    given expiry_date's market close (15:30 IST by default - NSE's
    regular close). Calendar-day convention (/365), matching the
    existing black_scholes_price() usage elsewhere in this project.
    Floors at 0 - never negative, for an already-expired option.
    """

    expiry_dt = datetime.datetime.combine(expiry_date, datetime.time(expiry_hour, expiry_minute))
    delta_seconds = (expiry_dt - from_datetime).total_seconds()

    return max(delta_seconds, 0) / (365 * 24 * 3600)


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
