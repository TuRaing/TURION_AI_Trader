import yfinance as yf
import pandas as pd

from indicators.atr import calculate_atr
from indicators.supertrend import calculate_supertrend
from indicators.cpr import calculate_cpr
from strategy.risk_engine import calculate_atr_levels
from strategy.orb_vwap_backtest import _flatten, close_trade, summarize_trades

# Updated: 2026-07-25 - Supertrend trend-flip entry, optionally filtered by
# CPR bias (close vs. the trading day's Pivot), researched from the 22-Jul
# external strategy list. Analysis only - not wired into any paper trading
# or live automation, same pattern as this codebase's other
# *_backtest.py scripts.

SUPERTREND_PERIOD = 10
SUPERTREND_MULTIPLIER = 3.0
ATR_PERIOD = 14  # for Stop-Loss/Target sizing, independent of the Supertrend indicator's own ATR


def run_supertrend_cpr_backtest(
    symbol="^NSEI",
    period="60d",
    interval="5m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    allow_short=True,
    require_cpr_filter=True,
):
    """
    Backtests a Supertrend trend-flip entry - a fresh flip from "down" to
    "up" (or vice versa) - optionally filtered by CPR bias: close must be
    above the trading day's CPR Pivot for a long, below it for a short.
    CPR is computed from the previous *calendar* day's daily candle (the
    standard way CPR is read), not derived from the intraday data itself.

    require_cpr_filter=False tests plain Supertrend flips with no CPR
    bias filter, for comparison.

    Rules
    -----
    - Long entry: Supertrend direction flips "down" -> "up" on this
      candle, and (if require_cpr_filter) close is above the day's CPR
      Pivot.
    - Short entry: mirror image (flips "up" -> "down", close below
      Pivot). Only if allow_short.
    - Stop-Loss/Target: ATR-based, same calculate_atr_levels() used
      elsewhere in this codebase.
    - Any position still open at the last candle of its trading day is
      force-closed there ("Day End Square-Off") - intraday only, same
      convention as strategy/orb_vwap_backtest.py.

    No look-ahead: each day's CPR only ever uses the previous calendar
    day's already-closed daily candle; Supertrend at candle i only uses
    data up to and including candle i.

    Returns
    -------
    dict (see strategy.orb_vwap_backtest.summarize_trades), or
    {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    daily = yf.download(symbol, period=period, interval="1d", progress=False)

    if daily.empty:
        return {"Error": f"No usable daily data for {symbol} (needed for CPR)"}

    daily_cpr = calculate_cpr(daily)
    cpr_by_date = {ts.date(): row for ts, row in daily_cpr.iterrows()}

    close = _flatten(data["Close"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])

    supertrend = calculate_supertrend(data, period=SUPERTREND_PERIOD, multiplier=SUPERTREND_MULTIPLIER)
    direction = supertrend["Direction"]

    atr = calculate_atr(data, period=ATR_PERIOD)

    day = pd.Series(data.index.date, index=data.index)

    trades = []
    position = None

    for trading_day, day_index in data.groupby(day).groups.items():

        day_index = data.index[data.index.isin(day_index)]

        cpr_row = cpr_by_date.get(trading_day)
        pivot = None

        if cpr_row is not None and not pd.isna(cpr_row["Pivot"]):
            pivot = float(cpr_row["Pivot"])

        if require_cpr_filter and pivot is None:
            continue

        for i, timestamp in enumerate(day_index):

            is_last_of_day = (i == len(day_index) - 1)
            price = float(close.loc[timestamp])
            bar_high = float(high.loc[timestamp])
            bar_low = float(low.loc[timestamp])

            if position is not None:

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

            if position is not None and is_last_of_day:
                trades.append(close_trade(position, timestamp, price, "Day End Square-Off"))
                position = None

            if i == 0:
                continue

            dir_now = direction.iloc[data.index.get_loc(timestamp)]
            dir_prev = direction.iloc[data.index.get_loc(timestamp) - 1]
            atr_now = atr.loc[timestamp]

            if pd.isna(dir_now) or pd.isna(dir_prev) or pd.isna(atr_now) or dir_now == dir_prev:
                continue

            if position is None and not is_last_of_day:

                direction_signal = None

                if dir_now == "up" and (not require_cpr_filter or price > pivot):
                    direction_signal = "BUY"

                elif allow_short and dir_now == "down" and (not require_cpr_filter or price < pivot):
                    direction_signal = "SELL"

                if direction_signal is not None:

                    stop_loss, target = calculate_atr_levels(
                        price, float(atr_now), direction_signal,
                        sl_mult=atr_sl_mult, target_mult=atr_target_mult,
                    )

                    position = {
                        "Direction": direction_signal,
                        "Entry Time": timestamp,
                        "Entry Price": price,
                        "Stop Loss": stop_loss,
                        "Target": target,
                    }

    return summarize_trades(trades)
