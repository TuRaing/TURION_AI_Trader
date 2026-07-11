import yfinance as yf

from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from strategy.signal_engine import generate_signal, generate_filtered_signal
from strategy.market_structure import get_market_structure
from strategy.support_resistance import get_support_resistance
from strategy.risk_engine import calculate_atr_levels

# Candles looked back for Market Structure / Support-Resistance filters,
# kept bounded so per-candle recomputation in the backtest loop stays fast
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
    Run Backtest

    Parameters
    ----------
    symbol : str
    period : str
    interval : str
    stop_loss_pct : float
        Stop-loss distance from entry price, in percent (used unless use_atr_stops)
    target_pct : float
        Target distance from entry price, in percent (used unless use_atr_stops)
    use_filters : bool
        Apply Market Structure / Support-Resistance filters to each signal
    use_atr_stops : bool
        Size Stop-Loss/Target off ATR instead of a fixed percent
    atr_sl_mult : float
        Stop-loss distance as a multiple of ATR
    atr_target_mult : float
        Target distance as a multiple of ATR

    Returns
    -------
    dict
    """

    data = yf.download(symbol, period=period, interval=interval)

    close = data["Close"]
    high = data["High"]
    low = data["Low"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    if hasattr(high, "columns"):
        high = high.iloc[:, 0]

    if hasattr(low, "columns"):
        low = low.iloc[:, 0]

    ema20 = calculate_ema(data, 20)
    ema50 = calculate_ema(data, 50)
    rsi = calculate_rsi(data)
    atr = calculate_atr(data)

    warmup = 50

    trades = []
    position = None

    for i in range(warmup, len(data)):

        time = close.index[i]
        price = close.iloc[i]

        # Check Stop-Loss / Target on the open position first
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

            signal, _ = generate_filtered_signal(
                ema20.iloc[i],
                ema50.iloc[i],
                rsi.iloc[i],
                structure["Trend Analysis"]["Trend"],
                levels
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

    # Close any position still open at the end of the data
    if position is not None:

        time = close.index[-1]
        price = close.iloc[-1]

        trades.append(close_trade(position, time, price, "End Of Data"))

    return summarize_trades(trades)


def close_trade(position, exit_time, exit_price, reason):

    return {
        "Entry Time": position["Entry Time"],
        "Entry Price": position["Entry Price"],
        "Exit Time": exit_time,
        "Exit Price": exit_price,
        "Exit Reason": reason,
        "PnL": exit_price - position["Entry Price"]
    }


def summarize_trades(trades):

    total_trades = len(trades)

    wins = [t for t in trades if t["PnL"] > 0]
    losses = [t for t in trades if t["PnL"] <= 0]

    total_pnl = sum(t["PnL"] for t in trades)

    win_rate = (len(wins) / total_trades * 100) if total_trades else 0

    equity = 0
    peak = 0
    max_drawdown = 0

    for t in trades:

        equity += t["PnL"]

        if equity > peak:
            peak = equity

        drawdown = peak - equity

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    exit_reasons = {}

    for t in trades:
        exit_reasons[t["Exit Reason"]] = exit_reasons.get(t["Exit Reason"], 0) + 1

    return {
        "Total Trades": total_trades,
        "Wins": len(wins),
        "Losses": len(losses),
        "Win Rate": round(win_rate, 2),
        "Total PnL": round(total_pnl, 2),
        "Max Drawdown": round(max_drawdown, 2),
        "Exit Reasons": exit_reasons,
        "Trades": trades
    }
