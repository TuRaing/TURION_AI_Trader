import yfinance as yf
import pandas as pd

from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from strategy.risk_engine import calculate_atr_levels
from strategy.futures_transaction_costs import calculate_futures_round_trip_cost

# Added 09-Aug-2026 - tests whether the SAME RSI-momentum signal
# simple_st1/st2/st3 already use (RSI>=50 -> bullish, <50 -> bearish)
# has any real edge on its own, isolated from options-specific costs
# (theta decay, IV changes) that have muddied every options-buying
# result so far this project. Futures P&L is LINEAR (just price
# difference x quantity) - no premium, no IV, no strike selection -
# so this backtest answers "is the signal itself good?" cleanly.
#
# CAVEAT (same honesty convention as strategy/momentum_vix_backtest.py,
# which did the same simplification): this backtests the signal
# against the UNDERLYING INDEX SPOT price, not a real historical
# futures contract series. Futures track spot closely (small cost-of-
# carry basis, not a directional-accuracy difference), and Fyers'
# option/futures historical API would need contract-rollover stitching
# across monthly expiries that isn't built - spot is a reasonable,
# honestly-flagged proxy for "would this signal have caught the same
# moves", not a claim of exact real futures P&L.
#
# SAFETY DESIGN (the user's explicit request, 09-Aug): a real futures
# position can lose MORE than the capital behind it (unlike buying an
# option, capped at the premium paid) if a fast move outruns the
# Stop-Loss before it can execute - a gap-down open being the worst
# case. Position sizing here is deliberately NOT based on margin
# (which would allow much bigger positions - see the ~12% margin
# figures already discussed) - it's based on WORST_CASE_MOVE_PCT, a
# conservative assumed instant adverse move, so this strategy's
# capital can NEVER go negative from one trade even if the Stop-Loss
# completely failed to execute. This is deliberately much smaller than
# margin-based sizing would allow - safety over capital efficiency.
# Also intraday-only (forced square-off before close, same convention
# as simple_st1/st4/gapfill) - no position is ever held through an
# overnight gap in the first place, the single biggest source of the
# "account goes negative" risk being guarded against here.

RSI_PERIOD = 14
ATR_PERIOD = 14
WORST_CASE_MOVE_PCT = 10.0   # conservative assumed instant adverse move
                              # (historically extreme single-day NIFTY
                              # moves have reached 8-13% in crisis
                              # events) - sizing guarantees capital
                              # survives even this, not just a normal
                              # Stop-Loss-level move
SQUAREOFF_HOUR_MINUTE = (15, 15)  # IST, same convention as every
                                    # options strategy here


def _flatten(series):

    if hasattr(series, "columns"):
        return series.iloc[:, 0]

    return series


def calculate_worst_case_lots(capital, spot, lot_size, worst_case_move_pct=WORST_CASE_MOVE_PCT):
    """
    Pure function - the safety-first position sizing rule. Sizes so
    that even an INSTANT worst_case_move_pct adverse move (bigger than
    any real Stop-Loss should ever slip to) costs at most `capital` -
    capital can never go negative from this one position, regardless
    of whether the Stop-Loss executes at all.

    Returns
    -------
    int - number of lots (>= 0)
    """

    worst_case_loss_per_lot = spot * (worst_case_move_pct / 100) * lot_size

    if worst_case_loss_per_lot <= 0:
        return 0

    return int(capital // worst_case_loss_per_lot)


def close_trade(position, exit_time, exit_price, reason):

    quantity = position["Quantity"]

    if position["Direction"] == "BUY":
        pnl = (exit_price - position["Entry Price"]) * quantity
    else:
        pnl = (position["Entry Price"] - exit_price) * quantity

    cost = calculate_futures_round_trip_cost(position["Entry Price"], exit_price, quantity)

    return {
        "Direction": position["Direction"],
        "Entry Time": position["Entry Time"],
        "Entry Price": position["Entry Price"],
        "Exit Time": exit_time,
        "Exit Price": exit_price,
        "Exit Reason": reason,
        "Quantity": quantity,
        "PnL": round(pnl, 2),
        "Cost": round(cost, 2),
        "Net PnL": round(pnl - cost, 2),
    }


def summarize_trades(trades, starting_capital):

    total_trades = len(trades)

    gross_pnl = sum(t["PnL"] for t in trades)
    total_cost = sum(t["Cost"] for t in trades)
    net_pnl = sum(t["Net PnL"] for t in trades)

    wins = [t for t in trades if t["Net PnL"] > 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades else 0

    # Safety check, not just a metric: confirms the worst-case sizing
    # rule actually held - capital (starting + running Net PnL) should
    # never have gone negative at any point.
    running_capital = starting_capital
    min_capital_seen = starting_capital

    for t in trades:
        running_capital += t["Net PnL"]
        min_capital_seen = min(min_capital_seen, running_capital)

    exit_reasons = {}

    for t in trades:
        exit_reasons[t["Exit Reason"]] = exit_reasons.get(t["Exit Reason"], 0) + 1

    return {
        "Total Trades": total_trades,
        "Win Rate": round(win_rate, 2),
        "Gross PnL": round(gross_pnl, 2),
        "Total Cost": round(total_cost, 2),
        "Net PnL": round(net_pnl, 2),
        "Ending Capital": round(running_capital, 2),
        "Minimum Capital Seen": round(min_capital_seen, 2),
        "Capital Ever Negative": min_capital_seen < 0,
        "Exit Reasons": exit_reasons,
        "Trades": trades,
    }


def run_futures_signal_backtest(
    symbol="^NSEI",
    lot_size=75,
    period="60d",
    interval="5m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    starting_capital=100000,
    worst_case_move_pct=WORST_CASE_MOVE_PCT,
    allow_short=True,
):
    """
    Backtests the same RSI>=50/<50 directional signal simple_st1 uses,
    as a linear (futures-style) position instead of an options premium
    purchase - see module docstring for the full reasoning and safety
    design.

    Returns
    -------
    dict (see summarize_trades), or {"Error": str} if no usable data.
    """

    data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    return _run_on_data(data, lot_size, atr_sl_mult, atr_target_mult, starting_capital, worst_case_move_pct, allow_short)


def _run_on_data(data, lot_size, atr_sl_mult, atr_target_mult, starting_capital, worst_case_move_pct, allow_short):

    close = _flatten(data["Close"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])

    rsi = calculate_rsi(data, period=RSI_PERIOD)
    atr = calculate_atr(data, period=ATR_PERIOD)

    day = pd.Series(data.index.date, index=data.index)

    trades = []
    position = None
    capital = starting_capital

    for trading_day, day_index in data.groupby(day).groups.items():

        day_index = data.index[data.index.isin(day_index)]

        for i, timestamp in enumerate(day_index):

            is_last_of_day = (i == len(day_index) - 1)
            price = float(close.loc[timestamp])

            if position is not None:

                bar_high = float(high.loc[timestamp])
                bar_low = float(low.loc[timestamp])

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

            if position is None and not is_last_of_day:

                rsi_now = rsi.loc[timestamp]
                atr_now = atr.loc[timestamp]

                if pd.isna(rsi_now) or pd.isna(atr_now):
                    continue

                direction = "BUY" if float(rsi_now) >= 50 else "SELL"

                if direction == "SELL" and not allow_short:
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
