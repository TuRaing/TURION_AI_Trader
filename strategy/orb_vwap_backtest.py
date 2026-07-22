import yfinance as yf
import pandas as pd

from indicators.atr import calculate_atr
from strategy.risk_engine import calculate_atr_levels
from strategy.volume_engine import calculate_average_volume, build_volume_analysis
from strategy.candlestick_engine import get_candlestick_pattern

# Updated: 2026-07-22 - Opening Range Breakout (ORB) entry, filtered by VWAP
# direction and a volume spike, researched 21-Jul as the intraday candidate
# for the Best Trade Engine. Analysis only - not wired into any paper
# trading or live automation, same as strategy/multi_timeframe_backtest.py.

ORB_MINUTES = 15
VOLUME_SPIKE_MULT = 1.5
ATR_PERIOD = 14
VOLUME_AVG_PERIOD = 20

# Rough real round-trip cost estimate (brokerage + STT + exchange charges +
# GST + stamp duty) even with a discount broker - see doc/PROJECT_STATUS.md's
# "Before any real capital is used" note, 21-Jul.
DEFAULT_COST_PER_TRADE = 30.0


def _flatten(series):

    if hasattr(series, "columns"):
        return series.iloc[:, 0]

    return series


def _interval_minutes(interval):

    if interval.endswith("m"):
        return int(interval[:-1])

    if interval.endswith("h"):
        return int(interval[:-1]) * 60

    raise ValueError(f"Unsupported interval: {interval}")


def _calculate_intraday_vwap(data):
    """
    Volume-Weighted Average Price, resetting at the start of every trading
    day - a real VWAP never carries over from one day to the next.

    Returns
    -------
    Series indexed the same as data
    """

    close = _flatten(data["Close"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])
    volume = _flatten(data["Volume"])

    typical_price = (high + low + close) / 3
    day = pd.Series(data.index.date, index=data.index)

    cum_pv = (typical_price * volume).groupby(day).cumsum()
    cum_volume = volume.groupby(day).cumsum().astype(float).replace(0.0, float("nan"))

    return cum_pv / cum_volume


def close_trade(position, exit_time, exit_price, reason):

    if position["Direction"] == "BUY":
        pnl = exit_price - position["Entry Price"]
    else:
        pnl = position["Entry Price"] - exit_price

    return {
        "Direction": position["Direction"],
        "Entry Time": position["Entry Time"],
        "Entry Price": position["Entry Price"],
        "Exit Time": exit_time,
        "Exit Price": exit_price,
        "Exit Reason": reason,
        "PnL": round(pnl, 2),
    }


def summarize_trades(trades, cost_per_trade=DEFAULT_COST_PER_TRADE):

    total_trades = len(trades)

    gross_pnl = sum(t["PnL"] for t in trades)
    net_pnl = gross_pnl - (total_trades * cost_per_trade)

    wins = [t for t in trades if t["PnL"] > 0]
    net_wins = [t for t in trades if t["PnL"] > cost_per_trade]

    win_rate = (len(wins) / total_trades * 100) if total_trades else 0
    net_win_rate = (len(net_wins) / total_trades * 100) if total_trades else 0

    exit_reasons = {}

    for t in trades:
        exit_reasons[t["Exit Reason"]] = exit_reasons.get(t["Exit Reason"], 0) + 1

    return {
        "Total Trades": total_trades,
        "Wins (Gross)": len(wins),
        "Win Rate (Gross)": round(win_rate, 2),
        "Gross PnL": round(gross_pnl, 2),
        "Cost Per Trade": cost_per_trade,
        "Net PnL": round(net_pnl, 2),
        "Wins (Net of Costs)": len(net_wins),
        "Win Rate (Net of Costs)": round(net_win_rate, 2),
        "Exit Reasons": exit_reasons,
        "Trades": trades,
    }


def run_orb_vwap_backtest(
    symbol="^NSEI",
    period="60d",
    interval="5m",
    orb_minutes=ORB_MINUTES,
    volume_spike_mult=VOLUME_SPIKE_MULT,
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    cost_per_trade=DEFAULT_COST_PER_TRADE,
    allow_short=True,
    require_vwap_filter=True,
    require_volume_filter=True,
    require_candlestick_confirm=False,
):
    """
    Backtests an Opening Range Breakout entry, filtered by VWAP direction
    and a volume spike, researched 21-Jul as the candidate replacement/
    addition to the Best Trade Engine's intraday entry logic. Every
    building block (ATR, Volume) already exists in this codebase - this
    just wires them into new entry/exit rules, no new engine.

    require_vwap_filter / require_volume_filter : bool
        Set either to False to test plain ORB without that filter - e.g.
        require_vwap_filter=False, require_volume_filter=False tests a
        pure Opening Range Breakout with no VWAP or volume confirmation,
        for comparison against the combined approach.

    Rules
    -----
    - Opening Range: the high/low of the first `orb_minutes` of each
      trading day.
    - Long entry: close breaks above the Opening Range high, close is
      above VWAP, and volume is a spike (>= volume_spike_mult x the
      trailing average) - all on the same candle.
    - Short entry: mirror image (break below Opening Range low, close
      below VWAP, volume spike). Only if allow_short.
    - Stop-Loss/Target: ATR-based, same calculate_atr_levels() used
      elsewhere in this codebase.
    - Any position still open at the last candle of its trading day is
      force-closed there ("Day End Square-Off") - this is an intraday-
      only strategy, positions never carry overnight.

    No look-ahead: the Opening Range for a day is only used once its
    candles have actually completed; VWAP is cumulative from the start
    of that day up to and including the current candle, never beyond it.

    Returns
    -------
    dict (see summarize_trades), or {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    return _run_on_data(
        data, interval, orb_minutes, volume_spike_mult,
        atr_sl_mult, atr_target_mult, cost_per_trade, allow_short,
        require_vwap_filter, require_volume_filter, require_candlestick_confirm,
    )


def _run_on_data(
    data, interval, orb_minutes, volume_spike_mult,
    atr_sl_mult, atr_target_mult, cost_per_trade, allow_short,
    require_vwap_filter=True, require_volume_filter=True, require_candlestick_confirm=False,
):
    """
    Core backtest loop, split out from run_orb_vwap_backtest() so a tuning
    sweep can download each symbol's data once and re-run this against many
    parameter combinations instead of re-fetching per combination.
    """

    candle_minutes = _interval_minutes(interval)
    orb_candles = max(1, orb_minutes // candle_minutes)

    close = _flatten(data["Close"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])
    volume = _flatten(data["Volume"])

    vwap = _calculate_intraday_vwap(data)
    atr = calculate_atr(data, period=ATR_PERIOD)
    avg_volume = calculate_average_volume(data, period=VOLUME_AVG_PERIOD)

    day = pd.Series(data.index.date, index=data.index)

    trades = []
    position = None

    for trading_day, day_index in data.groupby(day).groups.items():

        day_index = data.index[data.index.isin(day_index)]

        if len(day_index) <= orb_candles:
            continue

        orb_high = float(high.loc[day_index[:orb_candles]].max())
        orb_low = float(low.loc[day_index[:orb_candles]].min())

        for i, timestamp in enumerate(day_index):

            is_last_of_day = (i == len(day_index) - 1)
            price = float(close.loc[timestamp])

            if position is not None:

                bar_high = float(high.loc[timestamp])
                bar_low = float(low.loc[timestamp])

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

            if position is not None or i < orb_candles:
                continue

            vwap_now = vwap.loc[timestamp]
            atr_now = atr.loc[timestamp]

            if pd.isna(atr_now) or (require_vwap_filter and pd.isna(vwap_now)):
                continue

            if require_volume_filter:

                volume_analysis = build_volume_analysis(
                    float(volume.loc[timestamp]), avg_volume.loc[timestamp], volume_spike_mult
                )

                if not volume_analysis["Spike"]:
                    continue

            direction = None
            vwap_ok_long = (not require_vwap_filter) or price > vwap_now
            vwap_ok_short = (not require_vwap_filter) or price < vwap_now

            if price > orb_high and vwap_ok_long:
                direction = "BUY"

            elif allow_short and price < orb_low and vwap_ok_short:
                direction = "SELL"

            if direction is not None and require_candlestick_confirm and i >= 1:

                global_pos = data.index.get_loc(timestamp)
                candle_bias = get_candlestick_pattern(data.iloc[global_pos - 1:global_pos + 1])["Bias"]
                expected_bias = "Bullish" if direction == "BUY" else "Bearish"

                if candle_bias != expected_bias:
                    direction = None

            if direction is not None and not is_last_of_day:

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

    return summarize_trades(trades, cost_per_trade)
