import yfinance as yf
import pandas as pd

from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from indicators.market_structure import find_swing_points
from indicators.divergence import is_bearish_divergence, is_bullish_divergence
from strategy.risk_engine import calculate_atr_levels
from strategy.futures_transaction_costs import calculate_futures_round_trip_cost
from strategy.futures_signal_backtest import calculate_worst_case_lots, close_trade, summarize_trades

# Added 09-Aug-2026 - RSI Divergence, the "less commonly-followed
# technique" candidate identified after the plain RSI>=50/<50 signal
# was found to lack edge (see strategy/futures_signal_backtest.py) and
# after combining it with ADX>25 also failed to help at scale. Same
# instrument (index spot as a futures proxy, same honest caveat), same
# safety design (worst-case-move-based position sizing, intraday-only
# square-off - see futures_signal_backtest.py's module docstring for
# the full reasoning) - reused here rather than duplicated.
#
# SIGNAL: price makes a swing high/low that RSI does NOT confirm -
# see indicators/divergence.py. Swing points come from indicators/
# market_structure.py's find_swing_points() (already built for ICT/
# SMC, reused here) - a candle is only trusted as a swing once
# SWING_LOOKBACK candles on both sides have confirmed it, so this
# still has no look-ahead: a divergence is only acted on once BOTH
# swings it compares are fully confirmed.
#
#   Bearish divergence (price higher high, RSI lower high) -> SELL
#   Bullish divergence (price lower low, RSI higher low) -> BUY
#
# Only the MOST RECENT pair of same-type swings is compared (the
# classic 2-point divergence check) - not a 3+ point pattern.

RSI_PERIOD = 14
ATR_PERIOD = 14
SWING_LOOKBACK = 3   # candles needed on each side to confirm a swing -
                      # slightly wider than ICT/SMC's default (2) since
                      # divergence needs cleaner, less noisy swings to
                      # compare meaningfully


def _flatten(series):

    if hasattr(series, "columns"):
        return series.iloc[:, 0]

    return series


def run_rsi_divergence_backtest(
    symbol="^NSEI",
    lot_size=75,
    period="60d",
    interval="5m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    starting_capital=250000,
    worst_case_move_pct=10.0,
    allow_short=True,
    swing_lookback=SWING_LOOKBACK,
):
    """
    Backtests an RSI Divergence entry (see module docstring) as a
    linear (futures-style) position - same safety-first position
    sizing and intraday-only convention as strategy/futures_signal_
    backtest.py, reused rather than duplicated.

    Returns
    -------
    dict (see strategy.futures_signal_backtest.summarize_trades), or
    {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    return _run_on_data(
        data, lot_size, atr_sl_mult, atr_target_mult, starting_capital, worst_case_move_pct, allow_short, swing_lookback,
    )


def _run_on_data(data, lot_size, atr_sl_mult, atr_target_mult, starting_capital, worst_case_move_pct, allow_short, swing_lookback):

    close = _flatten(data["Close"]).tolist()
    high = _flatten(data["High"]).tolist()
    low = _flatten(data["Low"]).tolist()
    atr = calculate_atr(data, period=ATR_PERIOD)
    rsi = calculate_rsi(data, period=RSI_PERIOD)
    timestamps = data.index

    swings = find_swing_points(high, low, lookback=swing_lookback)

    swings_by_confirm_index = {}
    for s in swings:
        confirm_at = s["index"] + swing_lookback
        swings_by_confirm_index.setdefault(confirm_at, []).append(s)

    last_swing_high = None  # {"price", "rsi"}
    last_swing_low = None

    trades = []
    position = None
    capital = starting_capital

    n = len(close)

    day = pd.Series(data.index.date, index=data.index)
    day_index_map = {}
    for trading_day, idx in data.groupby(day).groups.items():
        idx = data.index[data.index.isin(idx)]
        for pos, ts in enumerate(idx):
            day_index_map[ts] = (pos == len(idx) - 1)

    for i in range(n):

        timestamp = timestamps[i]
        price = close[i]
        is_last_of_day = day_index_map.get(timestamp, False)

        # --- confirm any swings due at this candle, check divergence ---
        divergence_signal = None

        for s in swings_by_confirm_index.get(i, []):

            rsi_at_swing = rsi.iloc[s["index"]]

            if pd.isna(rsi_at_swing):
                continue

            rsi_at_swing = float(rsi_at_swing)

            if s["type"] == "high":

                if last_swing_high is not None and is_bearish_divergence(
                    last_swing_high["price"], last_swing_high["rsi"], s["price"], rsi_at_swing
                ):
                    divergence_signal = "SELL"

                last_swing_high = {"price": s["price"], "rsi": rsi_at_swing}

            else:

                if last_swing_low is not None and is_bullish_divergence(
                    last_swing_low["price"], last_swing_low["rsi"], s["price"], rsi_at_swing
                ):
                    divergence_signal = "BUY"

                last_swing_low = {"price": s["price"], "rsi": rsi_at_swing}

        # --- manage an open position first ---
        if position is not None:

            bar_high = high[i]
            bar_low = low[i]

            exit_price, reason = None, None

            if position["Direction"] == "BUY":

                if bar_low <= position["Stop Loss"]:
                    exit_price, reason = position["Stop Loss"], "Stop Loss"
                elif bar_high >= position["Target"]:
                    exit_price, reason = position["Target"], "Target"

            else:

                if bar_high >= position["Stop Loss"]:
                    exit_price, reason = position["Stop Loss"], "Stop Loss"
                elif bar_low <= position["Target"]:
                    exit_price, reason = position["Target"], "Target"

            if exit_price is None and is_last_of_day:
                exit_price, reason = price, "Intraday Square-Off"

            if exit_price is not None:
                trade = close_trade(position, timestamp, exit_price, reason)
                trades.append(trade)
                capital += trade["Net PnL"]
                position = None

        # --- open on a fresh divergence signal ---
        if position is None and divergence_signal is not None and not is_last_of_day:

            direction = divergence_signal

            if direction == "SELL" and not allow_short:
                continue

            atr_now = atr.iloc[i]

            if pd.isna(atr_now):
                continue

            lots = calculate_worst_case_lots(capital, price, lot_size, worst_case_move_pct)

            if lots < 1:
                continue

            stop_loss, target = calculate_atr_levels(
                price, float(atr_now), direction, sl_mult=atr_sl_mult, target_mult=atr_target_mult,
            )

            position = {
                "Direction": direction,
                "Entry Time": timestamp,
                "Entry Price": price,
                "Stop Loss": stop_loss,
                "Target": target,
                "Quantity": lots * lot_size,
            }

    return summarize_trades(trades, starting_capital)
