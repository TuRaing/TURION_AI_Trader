import yfinance as yf

from strategy.watchlist_scanner import analyze_symbol, MIN_CANDLES
from strategy.risk_engine import calculate_atr_levels
from strategy.transaction_costs import calculate_round_trip_cost

# Updated: 2026-07-30 - Partial profit booking on the proven Daily-timeframe
# strategy (August-plan candidate #4, see PROJECT_STATUS.md Priority 2):
# instead of a single all-or-nothing 3x-ATR Target like the live engine
# (strategy/paper_trading.py) and its backtest (strategy/backtest_engine.py,
# never modified - this is a separate analysis-only file, same pattern as
# every other *_backtest.py here), book half the position at a nearer 1x-ATR
# partial target and let the other half ride with a trailing Stop-Loss
# instead of waiting for the full target. Same entry signal as the proven
# strategy (analyze_symbol's filtered "Signal", not the AI Decision Engine's
# separately-scored "Decision") so this is a fair like-for-like exit-
# management comparison, not a different strategy.

WINDOW = 250  # ~1 trading year of daily candles - generous for Market Structure/S-R on daily bars
WARMUP = 60
QUANTITY_PER_LEG = 1  # 2 units total (1 partial-booked, 1 trailed) - matches this codebase's 1-share convention per leg


def _close_leg(entry_price, exit_time, exit_price, reason, entry_time, quantity=QUANTITY_PER_LEG):

    pnl = (exit_price - entry_price) * quantity
    cost = calculate_round_trip_cost(entry_price, exit_price, quantity)

    return {
        "Entry Time": entry_time,
        "Entry Price": entry_price,
        "Exit Time": exit_time,
        "Exit Price": exit_price,
        "Exit Reason": reason,
        "Quantity": quantity,
        "PnL": round(pnl, 2),
        "Cost": round(cost, 2),
        "Net PnL": round(pnl - cost, 2),
    }


def run_daily_partial_booking_backtest(
    symbol="^NSEI",
    period="2y",
    interval="1d",
    atr_sl_mult=1.5,
    partial_atr_mult=1.0,
    trailing_atr_mult=None,
):
    """
    Backtests partial profit booking against the proven Daily-timeframe
    strategy's own entry signal: book half the position (1 of 2 units) at
    a nearer partial_atr_mult x ATR target, then trail the remaining unit's
    Stop-Loss instead of waiting for a single distant all-or-nothing target.

    Rules
    -----
    - Entry: same as the live Watchlist strategy - analyze_symbol()'s
      filtered "Signal" == "BUY", 2 units, initial Stop-Loss at
      atr_sl_mult x ATR (default 1.5x, matching calculate_atr_levels'
      own default so this is the same initial risk as live).
    - Before the partial target is hit: both units share the same fixed
      Stop-Loss. If hit, both units close there together ("Stop Loss").
    - Partial target (partial_atr_mult x ATR, default 1.0x - nearer than
      the live strategy's 3x full target): books 1 unit there
      ("Partial Target"), the other unit's Stop-Loss starts trailing from
      that point on (trailing_atr_mult x ATR, defaults to atr_sl_mult).
    - After the partial books, a SELL signal or Stop-Loss closes the
      remaining unit ("Signal Exit (Trail)" / "Trailing Stop").
    - Same no-look-ahead walk-forward pattern as every other backtest in
      this codebase - each day's analysis only ever sees data up to and
      including that day.

    Returns
    -------
    dict (Total Trades/Wins/Win Rate/Gross PnL/Total Cost/Net PnL/
    Exit Reasons/Trades), or {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty or len(data) < MIN_CANDLES:
        return {"Error": f"No usable {interval} data for {symbol}"}

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    high = data["High"]
    low = data["Low"]

    if hasattr(high, "columns"):
        high = high.iloc[:, 0]

    if hasattr(low, "columns"):
        low = low.iloc[:, 0]

    trades = []
    position = None

    for i in range(WARMUP, len(data)):

        timestamp = data.index[i]
        price = float(close.iloc[i])
        bar_high = float(high.iloc[i])
        bar_low = float(low.iloc[i])

        if position is not None:

            if not position["Partial Booked"]:

                if bar_low <= position["Stop Loss"]:

                    trades.append(_close_leg(
                        position["Entry Price"], timestamp, position["Stop Loss"], "Stop Loss",
                        position["Entry Time"], quantity=2,
                    ))
                    position = None
                    continue

                if bar_high >= position["Partial Target"]:

                    trades.append(_close_leg(
                        position["Entry Price"], timestamp, position["Partial Target"], "Partial Target",
                        position["Entry Time"], quantity=1,
                    ))
                    position["Partial Booked"] = True
                    position["Highest Price"] = max(position["Entry Price"], bar_high)
                    trailed_stop = position["Highest Price"] - position["Trail Distance"]
                    position["Stop Loss"] = max(position["Stop Loss"], trailed_stop)

            else:

                position["Highest Price"] = max(position["Highest Price"], bar_high)
                trailed_stop = position["Highest Price"] - position["Trail Distance"]
                position["Stop Loss"] = max(position["Stop Loss"], trailed_stop)

                if bar_low <= position["Stop Loss"]:

                    trades.append(_close_leg(
                        position["Entry Price"], timestamp, position["Stop Loss"], "Trailing Stop",
                        position["Entry Time"], quantity=1,
                    ))
                    position = None
                    continue

        window = data.iloc[max(0, i - WINDOW):i + 1]

        try:
            analysis = analyze_symbol(window)
        except Exception:
            continue

        signal = analysis["Signal"]

        if position is None and signal == "BUY":

            atr = analysis["ATR"]

            stop_loss, _ = calculate_atr_levels(price, atr, "BUY", sl_mult=atr_sl_mult)

            position = {
                "Entry Time": timestamp,
                "Entry Price": price,
                "Stop Loss": stop_loss,
                "Partial Target": price + atr * partial_atr_mult,
                "Partial Booked": False,
                "Trail Distance": atr * (trailing_atr_mult if trailing_atr_mult is not None else atr_sl_mult),
            }

        elif position is not None and signal == "SELL":

            remaining_qty = 1 if position["Partial Booked"] else 2
            reason = "Signal Exit (Trail)" if position["Partial Booked"] else "Signal Exit"

            trades.append(_close_leg(
                position["Entry Price"], timestamp, price, reason,
                position["Entry Time"], quantity=remaining_qty,
            ))
            position = None

    if position is not None:

        last_timestamp = data.index[-1]
        last_price = float(close.iloc[-1])
        remaining_qty = 1 if position["Partial Booked"] else 2

        trades.append(_close_leg(
            position["Entry Price"], last_timestamp, last_price, "End Of Data",
            position["Entry Time"], quantity=remaining_qty,
        ))

    total_trades = len(trades)
    wins = [t for t in trades if t["Net PnL"] > 0]
    gross_pnl = sum(t["PnL"] for t in trades)
    total_cost = sum(t["Cost"] for t in trades)
    net_pnl = sum(t["Net PnL"] for t in trades)

    exit_reasons = {}

    for t in trades:
        exit_reasons[t["Exit Reason"]] = exit_reasons.get(t["Exit Reason"], 0) + 1

    return {
        "Total Trades": total_trades,
        "Wins (Net of Costs)": len(wins),
        "Win Rate (Net of Costs)": round(len(wins) / total_trades * 100, 2) if total_trades else 0,
        "Gross PnL": round(gross_pnl, 2),
        "Total Cost": round(total_cost, 2),
        "Net PnL": round(net_pnl, 2),
        "Exit Reasons": exit_reasons,
        "Trades": trades,
    }
