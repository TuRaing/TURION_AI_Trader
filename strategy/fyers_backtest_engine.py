from strategy.fyers_data import fyers_download
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from strategy.signal_engine import generate_signal, generate_filtered_signal
from strategy.market_structure import get_market_structure
from strategy.support_resistance import get_support_resistance
from strategy.risk_engine import calculate_atr_levels
from strategy.volume_engine import calculate_average_volume, build_volume_analysis
from strategy.candlestick_engine import get_candlestick_pattern
from strategy.backtest_engine import close_trade, summarize_trades

# Added 05-Aug-2026 - Fyers-sourced counterpart to strategy/
# backtest_engine.py, per this repo's engine-separation rule. Unlike
# strategy/multi_timeframe_backtest.py (which had a small, cleanly
# monkey-patchable _download() helper), this file's yf.download() call
# is inline in run_backtest() itself, so this is a near-duplicate with
# just that one line swapped, not a runtime patch. close_trade/
# summarize_trades (pure logic, no data-source dependency) are reused
# unchanged from the original.
#
# The point: Fyers' real daily history (confirmed 04-Aug: ~20 years,
# though a single request caps at 366 days - fyers_data.py already
# paginates past that) replaces yfinance for the SAME proven Daily-
# timeframe strategy PROJECT_STATUS.md already tracks as the one with
# a real backtest edge - this lets that finding be re-checked against
# real Fyers daily candles instead of yfinance's.

STRUCTURE_WINDOW = 100


def run_backtest(
    symbol="^NSEI",
    period="60d",
    interval="15m",
    stop_loss_pct=0.2,
    target_pct=0.9,
    use_filters=True,
    use_atr_stops=False,
    atr_sl_mult=1.5,
    atr_target_mult=3.0
):
    """
    Same contract as strategy.backtest_engine.run_backtest, sourced from
    Fyers instead of yfinance.
    """

    data = fyers_download(symbol, period=period, interval=interval)

    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    if hasattr(high, "columns"):
        high = high.iloc[:, 0]

    if hasattr(low, "columns"):
        low = low.iloc[:, 0]

    if hasattr(volume, "columns"):
        volume = volume.iloc[:, 0]

    ema20 = calculate_ema(data, 20)
    ema50 = calculate_ema(data, 50)
    rsi = calculate_rsi(data)
    atr = calculate_atr(data)
    avg_volume = calculate_average_volume(data, 20)

    warmup = 50

    trades = []
    position = None

    for i in range(warmup, len(data)):

        time = close.index[i]
        price = close.iloc[i]

        if position is not None:

            if low.iloc[i] <= position["Stop Loss"]:

                trades.append(close_trade(position, time, position["Stop Loss"], "Stop Loss"))
                position = None
                continue

            if high.iloc[i] >= position["Target"]:

                trades.append(close_trade(position, time, position["Target"], "Target"))
                position = None
                continue

        if use_filters:

            window = data.iloc[max(0, i - STRUCTURE_WINDOW):i + 1]

            structure = get_market_structure(window)
            levels = get_support_resistance(window)
            volume_analysis = build_volume_analysis(volume.iloc[i], avg_volume.iloc[i])
            candle_pattern = get_candlestick_pattern(data.iloc[i - 1:i + 1])

            signal, _ = generate_filtered_signal(
                ema20.iloc[i],
                ema50.iloc[i],
                rsi.iloc[i],
                structure["Trend Analysis"]["Trend"],
                levels,
                volume_analysis,
                candle_pattern
            )

        else:

            signal = generate_signal(
                ema20.iloc[i],
                ema50.iloc[i],
                rsi.iloc[i]
            )

        if position is None and signal == "BUY":

            if use_atr_stops:

                stop_loss, target = calculate_atr_levels(
                    price,
                    atr.iloc[i],
                    "BUY",
                    sl_mult=atr_sl_mult,
                    target_mult=atr_target_mult
                )

            else:

                stop_loss = price * (1 - stop_loss_pct / 100)
                target = price * (1 + target_pct / 100)

            position = {
                "Entry Time": time,
                "Entry Price": price,
                "Stop Loss": stop_loss,
                "Target": target
            }

        elif position is not None and signal == "SELL":

            trades.append(close_trade(position, time, price, "Signal Exit"))

            position = None

    if position is not None:

        time = close.index[-1]
        price = close.iloc[-1]

        trades.append(close_trade(position, time, price, "End Of Data"))

    return summarize_trades(trades)
