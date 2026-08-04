from strategy.fyers_data import fyers_download
from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES
from strategy.multi_timeframe_engine import analyze_timeframes

# Added 04-Aug-2026 - Fyers-sourced counterpart to strategy/
# multi_timeframe_engine.py, per this repo's engine-separation rule.
# analyze_timeframes (the pure alignment-check logic) is reused as-is;
# only the data-fetching changes. Fyers' real intraday history depth
# (tested 04-Aug: ~9y for 1m/5m/15m, vs. yfinance's ~5-60 day ceiling)
# means TIMEFRAMES' periods below can be far more generous than the
# yfinance original's Yahoo-ceiling-constrained values - kept modest
# here (matching yfinance's periods) since a live signal only ever
# needs recent candles for its indicator warmup, not deep history.

TIMEFRAMES = {
    "15m": {"interval": "15m", "period": "60d"},
    "5m": {"interval": "5m", "period": "60d"},
    "1m": {"interval": "1m", "period": "5d"},
}

TREND_TIMEFRAME = "15m"
ENTRY_TIMEFRAME = "5m"
TIMING_TIMEFRAME = "1m"


def get_multi_timeframe_signal(name, ticker):
    """
    Same contract as strategy.multi_timeframe_engine.get_multi_timeframe_signal,
    sourced from Fyers.
    """

    analyses = {}

    for timeframe, params in TIMEFRAMES.items():

        try:
            frame = fyers_download(ticker, params["period"], params["interval"])

        except Exception as error:

            print(f"Fyers fetch failed for {ticker} ({timeframe}): {error}")
            frame = None

        if frame is None or frame.empty or len(frame) < MIN_CANDLES:

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
