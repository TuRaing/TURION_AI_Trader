import os
import json
from datetime import datetime

PORTFOLIO_FILE = "reports/best_trade_portfolio.json"
INITIAL_CAPITAL = 100000
QUANTITY = 1


def load_best_trade_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Position": None,
            "Closed Trades": []
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_best_trade_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def open_best_trade(portfolio, name, symbol, direction, price, stop_loss, target, quantity=QUANTITY):
    """
    Open today's single locked Best Trade position, if none is already
    open. Kept in its own file/portfolio, separate from the swing-style
    watchlist paper trading in strategy/paper_trading.py - that one is
    a working module and stays untouched; this is a distinct daily
    intraday-only position with its own square-off rule (see
    square_off_best_trade below).

    Only equity picks should be opened here - index option picks have
    no reliable live premium feed to mark P&L against (see
    strategy/option_chain_engine.py's NSE-block caveat), so those stay
    recommendation-only and never reach this function.

    Returns
    -------
    portfolio : dict
    action : str
    """

    if portfolio["Position"] is not None:
        return portfolio, "ALREADY OPEN"

    portfolio["Position"] = {
        "Name": name,
        "Symbol": symbol,
        "Direction": direction,
        "Entry Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Price": price,
        "Quantity": quantity,
        "Stop Loss": stop_loss,
        "Target": target
    }

    return portfolio, "OPENED"


def _exit_price_and_reason(position, current_price, force_close):

    direction = position["Direction"]

    if direction == "BUY":

        if current_price <= position["Stop Loss"]:
            return position["Stop Loss"], "Stop Loss"

        if current_price >= position["Target"]:
            return position["Target"], "Target"

    else:

        if current_price >= position["Stop Loss"]:
            return position["Stop Loss"], "Stop Loss"

        if current_price <= position["Target"]:
            return position["Target"], "Target"

    if force_close:
        return current_price, "Intraday Square-Off"

    return None, None


def _close_position(portfolio, position, exit_price, reason):

    if position["Direction"] == "BUY":
        pnl = (exit_price - position["Entry Price"]) * position["Quantity"]

    else:
        pnl = (position["Entry Price"] - exit_price) * position["Quantity"]

    portfolio["Cash"] += pnl

    portfolio["Closed Trades"].append({
        "Name": position["Name"],
        "Symbol": position["Symbol"],
        "Direction": position["Direction"],
        "Entry Time": position["Entry Time"],
        "Entry Price": position["Entry Price"],
        "Exit Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Price": exit_price,
        "Quantity": position["Quantity"],
        "Exit Reason": reason,
        "PnL": round(pnl, 2)
    })

    portfolio["Position"] = None

    return portfolio, f"CLOSED ({reason})"


def check_open_position(portfolio, current_price):
    """
    Check today's open Best Trade position against the current price -
    closes it only if Stop Loss/Target has actually been breached,
    otherwise leaves it open ("HOLD"). Unlike square_off_best_trade,
    this never force-closes at market price - it's meant to be called
    often through the day (every ~5 min - see daily_best_trade.py) so a
    Stop Loss/Target hit is caught close to when it actually happens,
    instead of only being discovered at the 14:45 IST square-off.

    Returns
    -------
    portfolio : dict
    action : str
    """

    position = portfolio["Position"]

    if position is None:
        return portfolio, "NO POSITION"

    exit_price, reason = _exit_price_and_reason(position, current_price, force_close=False)

    if exit_price is None:
        return portfolio, "HOLD"

    return _close_position(portfolio, position, exit_price, reason)


def square_off_best_trade(portfolio, current_price):
    """
    Close today's open Best Trade position before market close - at
    Stop Loss/Target if already breached, otherwise at the current
    market price ("Intraday Square-Off"). This is what makes the Best
    Trade pick a genuine same-day intraday trade instead of silently
    carrying over to the next day.

    Returns
    -------
    portfolio : dict
    action : str
    """

    position = portfolio["Position"]

    if position is None:
        return portfolio, "NO POSITION"

    exit_price, reason = _exit_price_and_reason(position, current_price, force_close=True)

    return _close_position(portfolio, position, exit_price, reason)
