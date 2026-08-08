import yfinance as yf
import pandas as pd

from indicators.atr import calculate_atr
from indicators.market_structure import (
    find_swing_points,
    MarketStructureTracker,
    detect_order_block,
    detect_fair_value_gap,
)
from strategy.risk_engine import calculate_atr_levels
from strategy.orb_vwap_backtest import _flatten, close_trade, summarize_trades, ATR_PERIOD

# Added 08-Aug-2026 - ICT/Smart Money Concepts, one of the 5 candidates
# from the ChatGPT strategy list the user pasted 07-Aug. Evaluated first
# (see doc/PROJECT_STATUS.md's 08-Aug entry) against this project's own
# already-tested candidates: VWAP+EMA+Volume and ORB were both
# CONCLUSIVELY REJECTED 22-Jul (48-combo sweep, every combo net-negative),
# and Option Chain/PCR/Max Pain was already built but shelved for lack of
# historical data. ICT/SMC was the one genuinely untested idea on the
# list - user asked to build and backtest it despite the recommendation
# to wait, so this is that build. Analysis only - not wired into any
# paper trading or live automation, same as every other *_backtest.py in
# this codebase.
#
# SCOPE: implements the 4 concepts the user actually named (Liquidity via
# swing points, Break of Structure, Change of Character, Order Blocks,
# Fair Value Gaps) - NOT the full ICT framework (no kill zones, no
# premium/discount arrays, no dealing ranges). See indicators/market_
# structure.py for the pure building blocks this wires together.
#
# ENTRY RULE: wait for a CHOCH (the first sign of a structure shift) ->
# an Order Block AND/OR Fair Value Gap forms during the impulsive move
# right after the CHOCH -> enter when price retraces back INTO that
# zone, in the CHOCH's new direction. Stop-Loss/Target are ATR-based
# (calculate_atr_levels), same convention as every other backtest here,
# for an apples-to-apples comparison against the already-rejected
# candidates rather than inventing a new R:R scheme just for this one.

SWING_LOOKBACK = 2
ATR_LOOKAHEAD_FOR_ZONE = 10  # how many candles after a CHOCH to look for
                              # an Order Block/FVG before giving up on
                              # that structure shift entirely
ZONE_VALID_CANDLES = 20      # how many candles a formed zone stays valid
                              # (price must retrace into it within this
                              # window, or it's considered stale)


def run_ict_smc_backtest(
    symbol="^NSEI",
    period="60d",
    interval="5m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    allow_short=True,
    swing_lookback=SWING_LOOKBACK,
):
    """
    Backtests the ICT-lite CHOCH -> Order Block/FVG retracement entry
    described above. No look-ahead: swings are only trusted once
    `swing_lookback` candles past them have closed; a zone (OB/FVG) is
    only usable for entries on candles AFTER the candle that formed it.

    Returns
    -------
    dict (see strategy.orb_vwap_backtest.summarize_trades), or
    {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    return _run_on_data(data, atr_sl_mult, atr_target_mult, allow_short, swing_lookback)


def _run_on_data(data, atr_sl_mult, atr_target_mult, allow_short, swing_lookback):

    open_ = _flatten(data["Open"]).tolist()
    high = _flatten(data["High"]).tolist()
    low = _flatten(data["Low"]).tolist()
    close = _flatten(data["Close"]).tolist()
    atr = calculate_atr(data, period=ATR_PERIOD)
    timestamps = data.index

    swings = find_swing_points(high, low, lookback=swing_lookback)
    # index -> list of swings confirmed exactly at that index (a candle
    # can be both a swing high AND swing low in rare flat-range cases)
    swings_by_confirm_index = {}
    for s in swings:
        confirm_at = s["index"] + swing_lookback
        swings_by_confirm_index.setdefault(confirm_at, []).append(s)

    tracker = MarketStructureTracker()
    pending_zone = None  # {"direction", "top", "bottom", "expires_at"} - the
                          # most recent unfilled OB/FVG zone from a CHOCH,
                          # waiting for price to retrace into it

    trades = []
    position = None

    n = len(close)

    for i in range(n):

        timestamp = timestamps[i]
        price = close[i]
        atr_now = atr.iloc[i]

        # Feed any swings confirmed as of this candle into the tracker
        # BEFORE using it this candle - matches the real-time order
        # (you'd only know about a swing once it's actually confirmed).
        for s in swings_by_confirm_index.get(i, []):
            tracker.add_swing(s["type"], s["price"])

        # --- manage an open position first ---
        if position is not None:

            bar_high = high[i]
            bar_low = low[i]

            if position["Direction"] == "BUY":

                if bar_low <= position["Stop Loss"]:
                    trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                elif bar_high >= position["Target"]:
                    trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                    position = None

            else:

                if bar_high >= position["Stop Loss"]:
                    trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                elif bar_low <= position["Target"]:
                    trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                    position = None

        if position is not None:
            continue

        # --- check for a fresh structure break on this candle's close ---
        event = tracker.check_break(price)

        if event == "CHOCH":

            direction = tracker.trend  # already flipped by check_break
            ob = detect_order_block(open_, close, direction, breakout_index=i)
            fvg = detect_fair_value_gap(high, low, index=max(0, i - 1)) if i >= 1 else None

            zone = None

            if ob is not None:
                zone = {"direction": direction, "top": ob["high_ref"], "bottom": ob["low_ref"]}
            elif fvg is not None and fvg["direction"] == direction:
                zone = {"direction": direction, "top": fvg["top"], "bottom": fvg["bottom"]}

            if zone is not None:
                zone["expires_at"] = i + ZONE_VALID_CANDLES
                pending_zone = zone

        # --- check for a retracement into a pending zone ---
        if pending_zone is not None:

            if i > pending_zone["expires_at"]:
                pending_zone = None

            elif pd.isna(atr_now):
                pass

            else:

                bar_high = high[i]
                bar_low = low[i]
                zone_touched = bar_low <= pending_zone["top"] and bar_high >= pending_zone["bottom"]

                if zone_touched:

                    direction = "BUY" if pending_zone["direction"] == "up" else "SELL"

                    if direction == "SELL" and not allow_short:
                        pending_zone = None
                    else:

                        stop_loss, target = calculate_atr_levels(
                            price, float(atr_now), direction,
                            sl_mult=atr_sl_mult, target_mult=atr_target_mult,
                        )

                        position = {
                            "Direction": direction,
                            "Entry Time": timestamp,
                            "Entry Price": price,
                            "Stop Loss": stop_loss,
                            "Target": target,
                        }

                        pending_zone = None

    # Force-close anything still open at the very end of the data window
    if position is not None:
        trades.append(close_trade(position, timestamps[-1], close[-1], "Data End Square-Off"))

    return summarize_trades(trades)
