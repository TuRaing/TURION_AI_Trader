import os
import json
from datetime import datetime

from strategy.watchlist_scanner import download_watchlist, analyze_symbol, MIN_CANDLES
from strategy.risk_engine import calculate_atr_levels

PORTFOLIO_FILE = "reports/paper_portfolio.json"
INITIAL_CAPITAL = 100000
QUANTITY = 1

# Updated: 2026-07-19 - position sizing / portfolio-risk limits for the
# Daily-timeframe watchlist strategy (the one with a proven backtest edge -
# see doc/PROJECT_STATUS.md). Both only affect new entries; every already-
# open position keeps whatever quantity it was opened with.
BASE_RISK_PCT = 2.0
CONFIDENCE_FLOOR = 60
CONFIDENCE_CEILING = 100
MAX_CONCURRENT_POSITIONS = 15


def calculate_position_size(confidence, price, equity, base_risk_pct=BASE_RISK_PCT):
    """
    Risk a slice of current account equity per trade, scaled by how far
    above the AI Decision Engine's 60% entry threshold the confidence is:
    60% confidence risks half of base_risk_pct, 100% confidence risks the
    full base_risk_pct. Equity (not the fixed starting capital) is used so
    risk compounds with realized gains/losses, same as standard account
    risk management.

    Always returns at least 1 share - this is paper money, so the point
    is behavioral realism about scaling risk with confidence, not
    silently skipping a signal just because the stock is expensive.

    Returns
    -------
    int
    """

    fraction = max(0.0, min(1.0, (confidence - CONFIDENCE_FLOOR) / (CONFIDENCE_CEILING - CONFIDENCE_FLOOR)))
    scale = 0.5 + 0.5 * fraction

    risk_amount = equity * (base_risk_pct / 100) * scale

    return max(1, int(risk_amount // price))


def load_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Positions": {},
            "Closed Trades": []
        }

    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)

    # Updated: 2026-07-11 - migrate the old single-position schema (one NIFTY
    # trade at a time) to a multi-symbol "Positions" dict keyed by symbol name
    if "Positions" not in portfolio:

        old_position = portfolio.pop("Position", None)
        portfolio["Positions"] = {"NIFTY 50": old_position} if old_position else {}

    return portfolio


def save_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def process_signal(portfolio, symbol, signal, price, stop_loss=None, target=None, quantity=QUANTITY):
    """
    Update one symbol's position in the Paper Portfolio based on its
    latest signal and price. Mirrors the backtest engine's Stop-Loss/
    Target/Signal-Exit rules, but against one live price check per call
    instead of every candle. Each symbol is tracked independently so
    multiple positions can be open across the watchlist at once.

    Parameters
    ----------
    portfolio : dict
    symbol : str
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

    position = portfolio["Positions"].get(symbol)
    action = "HOLD"

    if position is None:

        if signal == "BUY":

            portfolio["Positions"][symbol] = {
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
                "Symbol": symbol,
                "Entry Time": position["Entry Time"],
                "Entry Price": position["Entry Price"],
                "Exit Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Exit Price": exit_price,
                "Quantity": position["Quantity"],
                "Exit Reason": reason,
                "PnL": round(pnl, 2)
            })

            del portfolio["Positions"][symbol]

            action = f"CLOSED ({reason})"

        else:

            # Updated: 2026-07-19 - stash the last-seen price on the position
            # itself (checked every 15 min by run_watchlist_paper_trading)
            # so the mobile app can show live up/down without a separate
            # live-price feed.
            position["Last Price"] = price
            position["Last Checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, action


def run_watchlist_paper_trading(symbols, period="6mo", interval="1d"):
    """
    Scan every symbol in the watchlist and update the paper portfolio -
    opens a new position on a BUY signal (if none open for that symbol
    and the portfolio is under MAX_CONCURRENT_POSITIONS), sized by
    calculate_position_size(), or closes an existing one on Stop-Loss/
    Target/SELL. Each symbol's position is independent, so several can
    be open at once.

    Parameters
    ----------
    symbols : dict
        {display_name: yfinance_ticker}
    period : str
    interval : str

    Returns
    -------
    portfolio : dict
    events : list of dict {"Name", "Action", "Price"}
    """

    frames = download_watchlist(symbols, period, interval)

    portfolio = load_portfolio()
    events = []

    for name in symbols:

        try:

            frame = frames.get(name)

            if frame is None or len(frame) < MIN_CANDLES:
                continue

            analysis = analyze_symbol(frame)

            price = analysis["Price"]
            signal = analysis["Signal"]

            is_new_entry = portfolio["Positions"].get(name) is None and signal == "BUY"

            if is_new_entry and len(portfolio["Positions"]) >= MAX_CONCURRENT_POSITIONS:

                # At the portfolio-risk cap - skip this new entry (existing
                # positions above/below still get checked normally).
                continue

            if is_new_entry:

                stop_loss, target = calculate_atr_levels(price, analysis["ATR"], "BUY")
                quantity = calculate_position_size(analysis["Confidence"], price, portfolio["Cash"])

            else:

                stop_loss, target, quantity = None, None, QUANTITY

            portfolio, action = process_signal(portfolio, name, signal, price, stop_loss, target, quantity)

            if action != "HOLD":
                events.append({"Name": name, "Action": action, "Price": price})

        except Exception as error:

            print(f"Skipped {name}: {error}")

    save_portfolio(portfolio)

    return portfolio, events
