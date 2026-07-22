import yfinance as yf
import pandas as pd

from indicators.atr import calculate_atr
from strategy.risk_engine import calculate_atr_levels
from strategy.candlestick_engine import get_candlestick_pattern
from strategy.orb_vwap_backtest import _flatten, _calculate_intraday_vwap, close_trade, summarize_trades, ATR_PERIOD, DEFAULT_COST_PER_TRADE

# Updated: 2026-07-22 - VWAP Pullback: price establishes a trend relative to
# VWAP, pulls back to touch VWAP, then bounces back in the trend direction -
# a mean-reversion-to-trend entry, distinct from the ORB breakout tested in
# orb_vwap_backtest.py. Analysis only - not wired into any paper trading.

TREND_LOOKBACK = 10
TREND_THRESHOLD = 0.7  # >=70% of the last TREND_LOOKBACK candles above/below VWAP


def run_vwap_pullback_backtest(
    symbol="^NSEI",
    period="60d",
    interval="5m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    cost_per_trade=DEFAULT_COST_PER_TRADE,
    allow_short=True,
    require_candlestick_confirm=False,
):
    """
    Backtests a VWAP Pullback entry: an established trend relative to VWAP
    (>= TREND_THRESHOLD of the last TREND_LOOKBACK candles closing on one
    side of VWAP), a pullback candle that touches VWAP, then the next
    candle closing back on the trend side of VWAP (the "bounce").

    - Long: uptrend (mostly above VWAP), a candle's low touches/crosses
      VWAP, the same or next candle closes back above VWAP -> BUY.
    - Short: mirror image. Only if allow_short.
    - Stop-Loss/Target: ATR-based, same as elsewhere in this codebase.
    - Any position still open at day-end is force-closed there - intraday
      only, matching orb_vwap_backtest.py's convention.

    No look-ahead: the trend classification and pullback touch only use
    candles up to and including the current one; VWAP is cumulative from
    the start of that trading day.

    Returns
    -------
    dict (see strategy.orb_vwap_backtest.summarize_trades), or
    {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    close = _flatten(data["Close"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])

    vwap = _calculate_intraday_vwap(data)
    atr = calculate_atr(data, period=ATR_PERIOD)

    above_vwap = (close > vwap).astype(float)
    pct_above = above_vwap.rolling(TREND_LOOKBACK).mean()

    day = pd.Series(data.index.date, index=data.index)

    trades = []
    position = None

    for trading_day, day_index in data.groupby(day).groups.items():

        day_index = data.index[data.index.isin(day_index)]

        if len(day_index) <= TREND_LOOKBACK + 1:
            continue

        was_pullback_up = False   # uptrend, saw a touch of VWAP, waiting for the bounce close
        was_pullback_down = False

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

            if i <= TREND_LOOKBACK:
                continue

            vwap_now = vwap.loc[timestamp]
            atr_now = atr.loc[timestamp]
            pct_now = pct_above.loc[timestamp]

            if pd.isna(vwap_now) or pd.isna(atr_now) or pd.isna(pct_now):
                continue

            uptrend = pct_now >= TREND_THRESHOLD
            downtrend = pct_now <= (1 - TREND_THRESHOLD)

            touched_vwap = bar_low <= vwap_now <= bar_high

            if position is None:

                # Track the pullback -> bounce sequence across consecutive candles
                if uptrend and touched_vwap:
                    was_pullback_up = True
                elif not uptrend:
                    was_pullback_up = False

                if downtrend and touched_vwap:
                    was_pullback_down = True
                elif not downtrend:
                    was_pullback_down = False

                direction = None

                if was_pullback_up and uptrend and price > vwap_now and not is_last_of_day:
                    direction = "BUY"
                    was_pullback_up = False

                elif allow_short and was_pullback_down and downtrend and price < vwap_now and not is_last_of_day:
                    direction = "SELL"
                    was_pullback_down = False

                if direction is not None and require_candlestick_confirm:

                    global_pos = data.index.get_loc(timestamp)

                    if global_pos >= 1:
                        candle_bias = get_candlestick_pattern(data.iloc[global_pos - 1:global_pos + 1])["Bias"]
                        expected_bias = "Bullish" if direction == "BUY" else "Bearish"

                        if candle_bias != expected_bias:
                            direction = None

                if direction is not None:

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
