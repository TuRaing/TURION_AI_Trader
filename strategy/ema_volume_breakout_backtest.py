import yfinance as yf
import pandas as pd

from indicators.ema import calculate_ema
from indicators.atr import calculate_atr
from strategy.risk_engine import calculate_atr_levels
from strategy.volume_engine import calculate_average_volume, build_volume_analysis
from strategy.orb_vwap_backtest import _flatten, close_trade, summarize_trades, DEFAULT_COST_PER_TRADE

# Updated: 2026-07-22 - 50 EMA + Volume Breakout, a swing (daily-candle)
# setup: long-only entry when price is above its 50 EMA (established
# uptrend) and breaks out above its recent N-day high on a volume spike.
# Researched from an external strategy list the user shared 22-Jul, worth
# comparing against the already-proven Daily/Watchlist swing strategy.
# Analysis only - not wired into any paper trading.

BREAKOUT_LOOKBACK = 20
EMA_PERIOD = 50
VOLUME_SPIKE_MULT = 1.5
VOLUME_AVG_PERIOD = 20


def run_ema_volume_breakout_backtest(
    symbol="^NSEI",
    period="2y",
    interval="1d",
    breakout_lookback=BREAKOUT_LOOKBACK,
    ema_period=EMA_PERIOD,
    volume_spike_mult=VOLUME_SPIKE_MULT,
    atr_sl_mult=1.5,
    atr_target_mult=3.0,
    cost_per_trade=DEFAULT_COST_PER_TRADE,
):
    """
    Backtests a 50 EMA + Volume Breakout swing setup: long-only, enters
    when close > EMA(ema_period) (established uptrend) AND close breaks
    above the highest high of the prior breakout_lookback candles AND
    volume is a spike (>= volume_spike_mult x trailing average).

    Exit: ATR-based Stop-Loss/Target, or if close falls back below the
    EMA (trend broken) - whichever comes first. No forced end-of-day
    square-off (this is a swing setup, positions can span multiple days,
    like the existing Daily/Watchlist strategy).

    No look-ahead: the breakout level only uses the breakout_lookback
    candles strictly before the current one (shifted by 1).

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
    volume = _flatten(data["Volume"])

    ema = calculate_ema(data, ema_period)
    atr = calculate_atr(data)
    avg_volume = calculate_average_volume(data, VOLUME_AVG_PERIOD)

    # Prior N-day high, excluding the current candle - no look-ahead
    breakout_level = high.shift(1).rolling(breakout_lookback).max()

    warmup = max(ema_period, breakout_lookback, VOLUME_AVG_PERIOD) + 1

    trades = []
    position = None

    for i in range(warmup, len(data)):

        timestamp = close.index[i]
        price = float(close.iloc[i])

        if position is not None:

            if float(low.iloc[i]) <= position["Stop Loss"]:
                trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                position = None

            elif float(high.iloc[i]) >= position["Target"]:
                trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                position = None

            elif price < float(ema.iloc[i]):
                trades.append(close_trade(position, timestamp, price, "Trend Broken (below EMA)"))
                position = None

        if position is None:

            level = breakout_level.iloc[i]
            atr_now = atr.iloc[i]

            if pd.isna(level) or pd.isna(atr_now):
                continue

            volume_analysis = build_volume_analysis(
                float(volume.iloc[i]), avg_volume.iloc[i], volume_spike_mult
            )

            if price > float(ema.iloc[i]) and price > level and volume_analysis["Spike"]:

                stop_loss, target = calculate_atr_levels(
                    price, float(atr_now), "BUY",
                    sl_mult=atr_sl_mult, target_mult=atr_target_mult,
                )

                position = {
                    "Direction": "BUY",
                    "Entry Time": timestamp,
                    "Entry Price": price,
                    "Stop Loss": stop_loss,
                    "Target": target,
                }

    if position is not None:
        trades.append(close_trade(position, close.index[-1], float(close.iloc[-1]), "End Of Data"))

    return summarize_trades(trades, cost_per_trade)
