import os
import json
from datetime import datetime

PORTFOLIO_FILE = "reports/paper_portfolio.json"
INITIAL_CAPITAL = 100000
QUANTITY = 1


def load_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Position": None,
            "Closed Trades": []
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def process_signal(portfolio, signal, price, stop_loss=None, target=None, quantity=QUANTITY):
    """
    Update the Paper Portfolio based on the latest signal and price.
    Mirrors the backtest engine's Stop-Loss/Target/Signal-Exit rules,
    but against one live price check per call instead of every candle.

    Parameters
    ----------
    portfolio : dict
    signal : str
    price : float
    stop_loss : float or None
        Required only when opening a new BUY
    target : float or None
        Required only when opening a new BUY
    quantity : int

    Returns
    -------
    portfolio : dict
    action : str
    """

    position = portfolio["Position"]
    action = "HOLD"

    if position is None:

        if signal == "BUY":

            portfolio["Position"] = {
                "Entry Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Entry Price": price,
                "Quantity": quantity,
                "Stop Loss": stop_loss,
                "Target": target
            }

            action = "OPENED BUY"

    else:

        exit_price = None
        reason = None

        if price <= position["Stop Loss"]:
            exit_price = position["Stop Loss"]
            reason = "Stop Loss"

        elif price >= position["Target"]:
            exit_price = position["Target"]
            reason = "Target"

        elif signal == "SELL":
            exit_price = price
            reason = "Signal Exit"

        if exit_price is not None:

            pnl = (exit_price - position["Entry Price"]) * position["Quantity"]

            portfolio["Cash"] += pnl

            portfolio["Closed Trades"].append({
                "Entry Time": position["Entry Time"],
                "Entry Price": position["Entry Price"],
                "Exit Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Exit Price": exit_price,
                "Quantity": position["Quantity"],
                "Exit Reason": reason,
                "PnL": round(pnl, 2)
            })

            portfolio["Position"] = None

            action = f"CLOSED ({reason})"

    return portfolio, action
