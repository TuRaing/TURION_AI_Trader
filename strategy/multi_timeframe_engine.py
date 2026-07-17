import time

import yfinance as yf

from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES

# Yahoo's real ceilings for these intervals - 1m data is only available for
# roughly the last 7 days, 5m/15m for roughly the last 60 days.
TIMEFRAMES = {
    "15m": {"interval": "15m", "period": "60d"},
    "5m": {"interval": "5m", "period": "60d"},
    "1m": {"interval": "1m", "period": "5d"},
}

# 15m sets the trend, 5m is the entry timeframe (its Decision/Confidence/
# Price/ATR become the trade's), 1m only confirms timing.
TREND_TIMEFRAME = "15m"
ENTRY_TIMEFRAME = "5m"
TIMING_TIMEFRAME = "1m"


def _fetch_with_retry(ticker, period, interval, attempts=2, delay=2):
    """
    A single bad/rate-limited request should never take down the whole
    run - retry once with a short delay, then give up and return None
    rather than raising (same per-symbol resilience philosophy as
    strategy/watchlist_scanner.py's scan_watchlist).
    """

    for attempt in range(attempts):

        try:

            frame = yf.download(ticker, period=period, interval=interval, progress=False)

            if frame is not None and not frame.empty:
                return frame

        except Exception as error:

            print(f"Fetch failed for {ticker} ({interval}, attempt {attempt + 1}/{attempts}): {error}")

        if attempt < attempts - 1:
            time.sleep(delay)

    return None


def analyze_timeframes(analyses):
    """
    Pure alignment check across three already-analyzed timeframes.

    Parameters
    ----------
    analyses : dict
        {"15m": analyze_symbol_result_or_None, "5m": ..., "1m": ...}
        (each value is the dict strategy.watchlist_scanner.analyze_symbol
        returns, or None if that timeframe had no/too little data).

    Returns
    -------
    dict
    """

    trend = analyses.get(TREND_TIMEFRAME)
    entry = analyses.get(ENTRY_TIMEFRAME)
    timing = analyses.get(TIMING_TIMEFRAME)

    if trend is None or entry is None or timing is None:

        return {
            "Aligned": False,
            "Reason": "Missing data on one or more timeframes",
            "15m": trend, "5m": entry, "1m": timing,
        }

    aligned = trend["Bias"] != "Neutral" and trend["Bias"] == entry["Bias"] == timing["Bias"]

    if not aligned:

        return {
            "Aligned": False,
            "Reason": f"Not aligned - 15m {trend['Bias']}, 5m {entry['Bias']}, 1m {timing['Bias']}",
            "15m": trend, "5m": entry, "1m": timing,
        }

    return {
        "Aligned": True,
        "Reason": f"15m/5m/1m all {trend['Bias']}",
        "Bias": trend["Bias"],
        "Decision": entry["Decision"],
        "Confidence": entry["Confidence"],
        "Price": entry["Price"],
        "ATR": entry["ATR"],
        "15m": trend, "5m": entry, "1m": timing,
    }


def get_multi_timeframe_signal(name, ticker):
    """
    I/O wrapper: fetch all three timeframes for one symbol and run the
    alignment check.

    Returns
    -------
    dict (see analyze_timeframes), with "Name"/"Symbol" added.
    """

    analyses = {}

    for timeframe, params in TIMEFRAMES.items():

        frame = _fetch_with_retry(ticker, params["period"], params["interval"])

        if frame is None or len(frame) < MIN_CANDLES:

            analyses[timeframe] = None
            continue

        try:
            analyses[timeframe] = analyze_symbol(frame)

        except Exception as error:

            print(f"Analysis failed for {ticker} ({timeframe}): {error}")
            analyses[timeframe] = None

    result = analyze_timeframes(analyses)
    result["Name"] = name
    result["Symbol"] = ticker

    return result
