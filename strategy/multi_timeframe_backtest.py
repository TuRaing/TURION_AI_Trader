import yfinance as yf
import pandas as pd

from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES
from strategy.risk_engine import calculate_atr_levels
from strategy.backtest_engine import close_trade, summarize_trades
from strategy.transaction_costs import calculate_round_trip_cost

# Same windowed-recompute pattern as strategy/backtest_engine.py's
# STRUCTURE_WINDOW - bounds Market Structure/Support-Resistance cost per
# candle so this stays runnable for a 60-day scan, and guarantees no
# look-ahead (only candles up to and including the current one are used).
WINDOW = 100
WARMUP = 60


def _flatten_close(data):

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    return close


def _download(symbol, interval, period):

    return yf.download(symbol, period=period, interval=interval, progress=False)


def _analyze_series(data):
    """
    Walk-forward analyze_symbol() (EMA/RSI/ATR/Structure/S-R/Volume/
    Candlestick -> Signal + AI Decision Bias/Confidence) for every candle
    from WARMUP onward, each using only data up to and including that
    candle - identical no-look-ahead approach as backtest_engine.py.

    Returns
    -------
    DataFrame indexed by candle timestamp, columns: Bias, Decision,
    Confidence, Price, ATR
    """

    rows = []

    for i in range(WARMUP, len(data)):

        window = data.iloc[max(0, i - WINDOW):i + 1]

        try:
            analysis = analyze_symbol(window)

        except Exception:
            continue

        rows.append({
            "Timestamp": data.index[i],
            "Bias": analysis["Bias"],
            "Decision": analysis["Decision"],
            "Confidence": analysis["Confidence"],
            "Price": analysis["Price"],
            "ATR": analysis["ATR"],
        })

    return pd.DataFrame(rows).set_index("Timestamp") if rows else pd.DataFrame()


def run_multi_timeframe_backtest(
    symbol="^NSEI",
    trend_period="60d",
    entry_period="60d",
    stop_loss_atr_mult=1.5,
    target_atr_mult=3.0,
    exit_on_alignment_break=True,
    require_daily_alignment=False,
    daily_period="2y",
):
    """
    Backtests the 15m(trend)/5m(entry) core of the alignment rule used
    live by strategy/multi_timeframe_engine.py (15m sets the trend, 5m is
    the entry decision - both must agree and be non-Neutral).

    The live engine also requires 1-minute confirmation before entering.
    That third leg cannot be meaningfully backtested here - Yahoo Finance
    only retains about 7 days of 1-minute history, too short a window for
    a statistically useful trade sample. Since 1m only ever narrows the
    live entries down further (it can block a 15m/5m-aligned setup, never
    create one on its own), this backtest is a reasonable upper bound on
    how often the live engine gets a real entry opportunity, and a valid
    read on whether the 15m/5m alignment idea itself has an edge.

    exit_on_alignment_break : bool
        If True (matches the live engine's spirit - only hold while 15m
        and 5m still agree), exit as soon as the two timeframes stop
        agreeing, even if neither Stop Loss nor Target has been hit yet.
        If False, once in a trade, only Stop Loss/Target/End Of Data
        closes it - alignment breaking is ignored.

    require_daily_alignment : bool
        Updated: 2026-07-23 - if True, also require the Daily (1d)
        timeframe's Bias to agree (non-Neutral, matching 15m/5m) before
        entering - researched at the user's suggestion, since Daily is
        the one timeframe with a proven backtest edge. Uses the most
        recently *completed* daily candle (yesterday's close onward, via
        the same as-of/backward join as 15m->5m) - never today's
        still-forming daily candle, so no look-ahead.

    Returns
    -------
    dict (same shape as strategy.backtest_engine.summarize_trades, plus
    an "Aligned Candles" diagnostic count), or {"Error": str} if any
    required timeframe returned no data.
    """

    trend_data = _download(symbol, "15m", trend_period)
    entry_data = _download(symbol, "5m", entry_period)

    if trend_data.empty or len(trend_data) < MIN_CANDLES:
        return {"Error": f"No usable 15m data for {symbol}"}

    if entry_data.empty or len(entry_data) < MIN_CANDLES:
        return {"Error": f"No usable 5m data for {symbol}"}

    trend_signals = _analyze_series(trend_data)
    entry_signals = _analyze_series(entry_data)

    if trend_signals.empty or entry_signals.empty:
        return {"Error": "Not enough candles after warmup to analyze either timeframe"}

    entry_close = _flatten_close(entry_data)
    entry_high = entry_data["High"]
    entry_low = entry_data["Low"]

    if hasattr(entry_high, "columns"):
        entry_high = entry_high.iloc[:, 0]

    if hasattr(entry_low, "columns"):
        entry_low = entry_low.iloc[:, 0]

    # As-of join: for each 5m candle, find the most recently *completed*
    # 15m candle at or before it - this is what a live check at that
    # moment would actually have seen, no look-ahead into a still-forming
    # 15m candle.
    merged = pd.merge_asof(
        entry_signals.reset_index().rename(columns={"Bias": "Entry Bias", "Decision": "Entry Decision", "Confidence": "Entry Confidence", "Price": "Entry Price_", "ATR": "Entry ATR"}),
        trend_signals.reset_index().rename(columns={"Bias": "Trend Bias"})[["Timestamp", "Trend Bias"]],
        on="Timestamp",
        direction="backward",
    ).set_index("Timestamp")

    if require_daily_alignment:

        daily_data = _download(symbol, "1d", daily_period)

        if daily_data.empty or len(daily_data) < MIN_CANDLES:
            return {"Error": f"No usable 1d data for {symbol}"}

        # Daily candles come back tz-naive from yfinance while intraday
        # candles are tz-aware (Asia/Kolkata) - merge_asof requires matching
        # dtypes, so localize daily to the same tz as the intraday data.
        if daily_data.index.tz is None:
            daily_data.index = daily_data.index.tz_localize(entry_data.index.tz)

        daily_signals = _analyze_series(daily_data)

        if daily_signals.empty:
            return {"Error": "Not enough daily candles after warmup to analyze"}

        merged = pd.merge_asof(
            merged.reset_index(),
            daily_signals.reset_index().rename(columns={"Bias": "Daily Bias"})[["Timestamp", "Daily Bias"]],
            on="Timestamp",
            direction="backward",
        ).set_index("Timestamp")

    trades = []
    position = None
    aligned_candles = 0

    for timestamp, row in merged.iterrows():

        if timestamp not in entry_close.index:
            continue

        price = float(entry_close.loc[timestamp])
        high = float(entry_high.loc[timestamp])
        low = float(entry_low.loc[timestamp])

        if position is not None:

            if low <= position["Stop Loss"]:

                trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                position = None
                continue

            if high >= position["Target"]:

                trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                position = None
                continue

        trend_bias = row["Trend Bias"]
        entry_bias = row["Entry Bias"]

        aligned = (
            pd.notna(trend_bias)
            and trend_bias != "Neutral"
            and trend_bias == entry_bias
        )

        if aligned and require_daily_alignment:

            daily_bias = row["Daily Bias"]
            aligned = pd.notna(daily_bias) and daily_bias == trend_bias

        if aligned:
            aligned_candles += 1

        if position is None and aligned and row["Entry Decision"] == "BUY":

            atr = row["Entry ATR"]

            stop_loss, target = calculate_atr_levels(
                price, atr, "BUY",
                sl_mult=stop_loss_atr_mult,
                target_mult=target_atr_mult,
            )

            position = {
                "Entry Time": timestamp,
                "Entry Price": price,
                "Quantity": 1,
                "Stop Loss": stop_loss,
                "Target": target,
            }

        elif exit_on_alignment_break and position is not None and (not aligned or row["Entry Decision"] == "SELL"):

            trades.append(close_trade(position, timestamp, price, "Alignment Broke"))
            position = None

    if position is not None:

        last_timestamp = entry_close.index[-1]
        trades.append(close_trade(position, last_timestamp, float(entry_close.iloc[-1]), "End Of Data"))

    summary = summarize_trades(trades)

    # Updated: 2026-07-23 - real percentage-based cost (strategy/
    # transaction_costs.py), not the flat guess used by the earlier
    # ORB/VWAP-Pullback backtests before this same date's correction.
    total_cost = sum(calculate_round_trip_cost(t["Entry Price"], t["Exit Price"], 1) for t in trades)
    summary["Total Cost"] = round(total_cost, 2)
    summary["Net PnL"] = round(summary["Total PnL"] - total_cost, 2)

    summary["Aligned Candles"] = aligned_candles
    summary["Total Entry Candles"] = len(merged)

    return summary
