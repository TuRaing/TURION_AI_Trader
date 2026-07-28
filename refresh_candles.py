import sys

sys.stdout.reconfigure(encoding="utf-8")

import json
import os
from datetime import datetime

from data.watchlist import INDICES
from strategy.candle_data_engine import fetch_candles
from strategy.paper_trading import PORTFOLIO_FILE as WATCHLIST_PORTFOLIO_FILE
from strategy.best_trade_paper_trading import PORTFOLIO_FILE as BEST_TRADE_PORTFOLIO_FILE

CANDLES_FILE = "reports/candles.json"

# Updated: 2026-07-28 - only refreshes candles for symbols that actually
# appear in a portfolio (open or closed) rather than the full 50-stock
# watchlist, to keep this workflow step's yfinance load small and fast -
# the app only ever needs a chart for a trade the user can actually tap on.
_INDEX_NAMES = set(INDICES.keys())


def _load_json(path):

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def _to_yf_symbol(name_or_symbol):
    """
    Best-effort mapping from a portfolio entry's stored Name/Symbol to a
    yfinance ticker - watchlist paper trades store bare names ("HDFCBANK"),
    best-trade paper trades store the full ticker ("ULTRACEMCO.NS") in
    Symbol and the bare name in Name. Indices go through data.watchlist's
    INDICES mapping instead of guessing a ".NS" suffix.
    """

    if name_or_symbol in INDICES:
        return INDICES[name_or_symbol]

    if name_or_symbol.startswith("^") or name_or_symbol.endswith(".NS"):
        return name_or_symbol

    return f"{name_or_symbol}.NS"


def _collect_symbols():
    """
    Union of every symbol referenced anywhere in either paper portfolio -
    open positions and closed trades, Watchlist (Swing) and Best Trade
    (Intraday) alike.

    Returns
    -------
    dict of {display_name: yfinance_symbol}
    """

    symbols = {}

    watchlist_portfolio = _load_json(WATCHLIST_PORTFOLIO_FILE)

    for name in watchlist_portfolio.get("Positions", {}):
        symbols[name] = _to_yf_symbol(name)

    for trade in watchlist_portfolio.get("Closed Trades", []):
        name = trade.get("Symbol") or trade.get("Name")
        if name:
            symbols[name] = _to_yf_symbol(name)

    best_trade_portfolio = _load_json(BEST_TRADE_PORTFOLIO_FILE)

    position = best_trade_portfolio.get("Position")

    if position:
        name = position.get("Name") or position.get("Symbol")
        if name:
            symbols[name] = _to_yf_symbol(position.get("Symbol") or name)

    for trade in best_trade_portfolio.get("Closed Trades", []):
        name = trade.get("Name") or trade.get("Symbol")
        if name:
            symbols[name] = _to_yf_symbol(trade.get("Symbol") or name)

    return symbols


def main():

    symbols = _collect_symbols()

    print(f"Refreshing candles for {len(symbols)} symbol(s): {', '.join(sorted(symbols))}")

    candles_by_symbol = {}

    for display_name, yf_symbol in symbols.items():

        try:
            candles_by_symbol[display_name] = fetch_candles(yf_symbol)
        except Exception as e:
            # One bad symbol (delisted ticker, temporary fetch failure)
            # must never take down the chart data for every other symbol.
            print(f"  {display_name} ({yf_symbol}): fetch failed - {e}")
            continue

    os.makedirs("reports", exist_ok=True)

    with open(CANDLES_FILE, "w") as f:
        json.dump({
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Candles": candles_by_symbol,
        }, f, indent=2)

    print(f"Wrote candles for {len(candles_by_symbol)} symbol(s) to {CANDLES_FILE}")


if __name__ == "__main__":
    main()
