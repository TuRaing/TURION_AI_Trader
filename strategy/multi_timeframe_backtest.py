import datetime

import yfinance as yf
import pandas as pd

from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES
from strategy.risk_engine import calculate_atr_levels
from strategy.backtest_engine import close_trade, summarize_trades
from strategy.transaction_costs import calculate_round_trip_cost
from indicators.adx import calculate_adx
from strategy.crash_protection_engine import detect_crash_state

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
    use_trailing_stop=False,
    trailing_atr_mult=None,
    require_adx_above=None,
    adx_period=14,
    intraday_squareoff_time=None,
    squareoff_trailing_atr_mult=None,
    block_reentry_after_loss_squareoff=True,
    require_vix_in_band=False,
    vix_symbol="^INDIAVIX",
    vix_percentile_low=0.20,
    vix_percentile_high=0.80,
    vix_lookback_candles=125,
    require_no_crash_state=False,
    crash_single_day_pct=-4.0,
    crash_rolling_days=5,
    crash_rolling_pct=-10.0,
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

    use_trailing_stop : bool
        Updated: 2026-07-24 - if True, replaces the fixed Target with a
        trailing Stop-Loss: as the trade's high makes new highs, the
        Stop-Loss ratchets up to (highest high so far - trail distance),
        but never moves down. Lets a strong trend run further than a
        fixed ATR-multiple Target would allow, at the cost of giving back
        more of the peak before exiting. Only ever moves the Stop-Loss in
        the trade's favor - no look-ahead, since it only reacts to highs
        already seen.
    trailing_atr_mult : float or None
        Trail distance as a multiple of the entry candle's ATR. Defaults
        to stop_loss_atr_mult (same distance as the initial Stop-Loss)
        when None.

    require_adx_above : float or None
        Updated: 2026-07-24 - if set, also require the 15m trend
        timeframe's ADX (indicators/adx.py - trend STRENGTH, not
        direction) to be above this value before entering. Researched
        at the user's suggestion to filter out weak/choppy conditions,
        the kind that whipsawed a too-tight trailing stop. ADX is an
        EWM-based calculation (no look-ahead by construction - each
        value only ever depends on candles up to and including it).

    intraday_squareoff_time : str or None
        Updated: 2026-07-29 - if set (e.g. "14:45"), mirrors the live
        Best Trade Engine's forced-intraday square-off, researched at
        the user's suggestion after asking why positions weren't
        closing on time (see the 29-Jul cron under-firing fix - this
        parameter is the *strategy* question that prompted, separate
        from that *infrastructure* bug). At the first candle at or
        after this time each day: if the position is currently in
        profit, it is NOT force-closed - instead it switches to a
        trailing Stop-Loss (squareoff_trailing_atr_mult) for the rest
        of that day, protecting the gain already made while leaving
        room to run. If it's flat or in loss, it is force-closed
        immediately ("Square-Off (Loss)"), and if
        block_reentry_after_loss_squareoff is True, no new entry is
        allowed for the remainder of that trading day. Any position
        still open at the actual last candle of the day is force-
        closed there regardless ("Day End Square-Off") - the
        intraday-only guarantee always wins. No effect when None
        (matches every existing backtest's behavior exactly).
    squareoff_trailing_atr_mult : float or None
        Trail distance (ATR multiple) used only for the post-cutoff
        trailing Stop-Loss above. Defaults to trailing_atr_mult, then
        stop_loss_atr_mult, when None.
    block_reentry_after_loss_squareoff : bool
        See intraday_squareoff_time. Only matters when
        intraday_squareoff_time is set.

    require_vix_in_band : bool
        Updated: 2026-07-30 - if True, also require India VIX to be
        inside its own recent [vix_percentile_low, vix_percentile_high]
        rolling percentile band (same methodology as
        strategy/momentum_vix_backtest.py's 22-Jul BANKNIFTY options
        finding, applied here to this file's *equity* entries instead -
        researched at the user's suggestion to test the same regime-
        filter idea on what's already a proven signal, rather than only
        on a new one). Uses the most recently *completed* 15m VIX
        candle relative to each entry candle (backward as-of join, same
        no-look-ahead pattern as every other filter here).
    vix_symbol : str
    vix_percentile_low, vix_percentile_high : float
        Rolling percentile band edges (0-1). Defaults match
        momentum_vix_backtest.py's VIX_PERCENTILE_LOW/HIGH.
    vix_lookback_candles : int
        Rolling window (in 15m candles) the percentile band is computed
        over. Default 125 (~5 trading days), matching
        momentum_vix_backtest.py's VIX_LOOKBACK_CANDLES.

    require_no_crash_state : bool
        Updated: 2026-07-31 - if True, also require the symbol's own
        daily price action to NOT be in a "crash state" (strategy/
        crash_protection_engine.py) before entering - researched at the
        user's suggestion after asking whether anything protects
        against a sudden market crash (nothing did - every existing
        safeguard limits one trade's/one day's loss, nothing pauses new
        entries during a crash itself). Does not touch any position
        already open - existing Stop-Losses still apply as-is, this
        only gates new entries. Uses the most recently *completed*
        daily candle, same no-look-ahead backward join as every other
        daily-timeframe filter here.
    crash_single_day_pct, crash_rolling_days, crash_rolling_pct :
        See strategy/crash_protection_engine.py - defaults calibrated
        against 19 years of real NIFTY daily history, not a guess.

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

    if require_adx_above is not None:

        adx_series = calculate_adx(trend_data, period=adx_period)
        adx_series.name = "ADX"
        adx_series.index.name = "Timestamp"

        merged = pd.merge_asof(
            merged.reset_index(),
            adx_series.reset_index(),
            on="Timestamp",
            direction="backward",
        ).set_index("Timestamp")

    if require_vix_in_band:

        vix_data = _download(vix_symbol, "15m", trend_period)

        if vix_data.empty or len(vix_data) < vix_lookback_candles:
            return {"Error": f"No usable 15m data for {vix_symbol} (needed for the VIX filter)"}

        vix_close = _flatten_close(vix_data)
        vix_low_band = vix_close.rolling(vix_lookback_candles).quantile(vix_percentile_low)
        vix_high_band = vix_close.rolling(vix_lookback_candles).quantile(vix_percentile_high)

        vix_frame = pd.DataFrame({
            "VIX": vix_close,
            "VIX Low Band": vix_low_band,
            "VIX High Band": vix_high_band,
        })
        vix_frame.index.name = "Timestamp"

        merged = pd.merge_asof(
            merged.reset_index(),
            vix_frame.reset_index(),
            on="Timestamp",
            direction="backward",
        ).set_index("Timestamp")

    daily_data = None

    if require_daily_alignment or require_no_crash_state:

        daily_data = _download(symbol, "1d", daily_period)

        if daily_data.empty or len(daily_data) < MIN_CANDLES:
            return {"Error": f"No usable 1d data for {symbol}"}

        # Daily candles come back tz-naive from yfinance while intraday
        # candles are tz-aware (Asia/Kolkata) - merge_asof requires matching
        # dtypes, so localize daily to the same tz as the intraday data.
        if daily_data.index.tz is None:
            daily_data.index = daily_data.index.tz_localize(entry_data.index.tz)

    if require_daily_alignment:

        daily_signals = _analyze_series(daily_data)

        if daily_signals.empty:
            return {"Error": "Not enough daily candles after warmup to analyze"}

        merged = pd.merge_asof(
            merged.reset_index(),
            daily_signals.reset_index().rename(columns={"Bias": "Daily Bias"})[["Timestamp", "Daily Bias"]],
            on="Timestamp",
            direction="backward",
        ).set_index("Timestamp")

    if require_no_crash_state:

        daily_close = _flatten_close(daily_data)

        crash_state = detect_crash_state(
            daily_close,
            single_day_pct=crash_single_day_pct,
            rolling_days=crash_rolling_days,
            rolling_pct=crash_rolling_pct,
        )
        crash_frame = crash_state.rename("Crash State").to_frame()
        crash_frame.index.name = "Timestamp"

        merged = pd.merge_asof(
            merged.reset_index(),
            crash_frame.reset_index(),
            on="Timestamp",
            direction="backward",
        ).set_index("Timestamp")

    cutoff_time = None

    if intraday_squareoff_time is not None:
        hh, mm = (int(part) for part in intraday_squareoff_time.split(":"))
        cutoff_time = datetime.time(hh, mm)

    day_last_timestamp = set()

    if cutoff_time is not None:
        day_series = pd.Series(merged.index.date, index=merged.index)
        day_last_timestamp = {g.index[-1] for _, g in merged.groupby(day_series)}

    trades = []
    position = None
    aligned_candles = 0
    current_day = None
    blocked_today = False

    for timestamp, row in merged.iterrows():

        if timestamp not in entry_close.index:
            continue

        if cutoff_time is not None:

            this_day = timestamp.date()

            if this_day != current_day:
                current_day = this_day
                blocked_today = False

        price = float(entry_close.loc[timestamp])
        high = float(entry_high.loc[timestamp])
        low = float(entry_low.loc[timestamp])

        if position is not None:

            position["Highest Price"] = max(position.get("Highest Price", position["Entry Price"]), high)

            trailing_active = use_trailing_stop or position.get("Post Cutoff Trailing", False)

            if trailing_active:

                trailed_stop = position["Highest Price"] - position["Trail Distance"]
                position["Stop Loss"] = max(position["Stop Loss"], trailed_stop)

            if low <= position["Stop Loss"]:

                reason = "Trailing Stop" if trailing_active else "Stop Loss"
                trades.append(close_trade(position, timestamp, position["Stop Loss"], reason))
                position = None
                continue

            if not trailing_active and high >= position["Target"]:

                trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                position = None
                continue

            if (
                cutoff_time is not None
                and not position.get("Squareoff Processed", False)
                and timestamp.time() >= cutoff_time
            ):

                position["Squareoff Processed"] = True

                if price > position["Entry Price"]:

                    trail_mult = (
                        squareoff_trailing_atr_mult
                        if squareoff_trailing_atr_mult is not None
                        else (trailing_atr_mult if trailing_atr_mult is not None else stop_loss_atr_mult)
                    )

                    position["Post Cutoff Trailing"] = True
                    position["Trail Distance"] = position["Entry ATR"] * trail_mult

                    trailed_stop = position["Highest Price"] - position["Trail Distance"]
                    position["Stop Loss"] = max(position["Stop Loss"], trailed_stop)

                else:

                    trades.append(close_trade(position, timestamp, price, "Square-Off (Loss)"))
                    position = None

                    if block_reentry_after_loss_squareoff:
                        blocked_today = True

                    continue

            if cutoff_time is not None and position is not None and timestamp in day_last_timestamp:

                trades.append(close_trade(position, timestamp, price, "Day End Square-Off"))
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

        if aligned and require_adx_above is not None:

            adx_value = row["ADX"]
            aligned = pd.notna(adx_value) and adx_value > require_adx_above

        if aligned and require_vix_in_band:

            vix_value = row["VIX"]
            vix_low = row["VIX Low Band"]
            vix_high = row["VIX High Band"]
            aligned = (
                pd.notna(vix_value) and pd.notna(vix_low) and pd.notna(vix_high)
                and vix_low <= vix_value <= vix_high
            )

        if aligned and require_no_crash_state:

            crash_state = row["Crash State"]
            aligned = pd.notna(crash_state) and not bool(crash_state)

        if aligned:
            aligned_candles += 1

        if position is None and aligned and row["Entry Decision"] == "BUY" and not blocked_today:

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
                "Highest Price": price,
                "Entry ATR": atr,
            }

            if use_trailing_stop:

                position["Trail Distance"] = atr * (trailing_atr_mult if trailing_atr_mult is not None else stop_loss_atr_mult)

        elif (
            exit_on_alignment_break
            and position is not None
            and not position.get("Post Cutoff Trailing", False)
            and (not aligned or row["Entry Decision"] == "SELL")
        ):

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
