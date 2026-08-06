import sys

sys.stdout.reconfigure(encoding="utf-8")

import json
import os
from datetime import datetime

from data.watchlist import INDICES
from strategy.fyers_candle_data_engine import fetch_candles
from strategy.fyers_paper_trading import PORTFOLIO_FILE as SWING_PORTFOLIO_FILE
from strategy.fyers_best_trade_paper_trading import PORTFOLIO_FILE as INTRADAY_PORTFOLIO_FILE
from strategy.options_strategies import ALL_STRATEGIES

CANDLES_FILE = "reports/fyers_candles.json"

# Added 06-Aug-2026 - Fyers-sourced counterpart to refresh_candles.py,
# per this repo's engine-separation rule - own file, own output
# (reports/fyers_candles.json), never touches the yfinance one.
#
# Options strategies trade a specific CONTRACT (e.g. NIFTY 24650 CE)
# that has no reliable candle history of its own (Fyers doesn't serve
# per-contract intraday history the way it does for the underlying -
# and premium/spot are different scales anyway, so overlaying a
# premium reference line on an index-points chart would be
# meaningless). Chart the UNDERLYING INDEX instead, with "Entry Spot"
# (and, for st4, "Peak Spot") as the reference line(s) - shows the
# real price action the trade's decision was actually based on.

_INDEX_TICKERS = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}


def _load_json(path):

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def _to_yf_symbol(name_or_symbol):
    """
    Same mapping as refresh_candles.py's _to_yf_symbol - indices go
    through data.watchlist's INDICES mapping instead of guessing a
    ".NS" suffix (which would build an invalid symbol like
    "NIFTY 50.NS").
    """

    if name_or_symbol in INDICES:
        return INDICES[name_or_symbol]

    if name_or_symbol.startswith("^") or name_or_symbol.endswith(".NS"):
        return name_or_symbol

    return f"{name_or_symbol}.NS"


def _collect_equity_symbols():
    """
    Every symbol referenced in the Fyers Swing/Intraday portfolios -
    same union-of-open-and-closed approach as refresh_candles.py's
    _collect_symbols(), sourced from the Fyers files instead.

    Returns
    -------
    dict of {display_name: yfinance_style_symbol}
    """

    symbols = {}

    swing_portfolio = _load_json(SWING_PORTFOLIO_FILE)

    for name in swing_portfolio.get("Positions", {}):
        symbols[name] = _to_yf_symbol(name)

    for trade in swing_portfolio.get("Closed Trades", []):
        name = trade.get("Symbol") or trade.get("Name")
        if name:
            symbols[name] = _to_yf_symbol(name)

    intraday_portfolio = _load_json(INTRADAY_PORTFOLIO_FILE)

    position = intraday_portfolio.get("Position")

    if position:
        name = position.get("Name") or position.get("Symbol")
        if name:
            symbols[name] = _to_yf_symbol(position.get("Symbol") or name)

    for trade in intraday_portfolio.get("Closed Trades", []):
        name = trade.get("Name") or trade.get("Symbol")
        if name:
            symbols[name] = _to_yf_symbol(trade.get("Symbol") or name)

    return symbols


def _any_options_strategy_has_activity(index):
    """
    True if any of the 4 named strategies has ever opened a position
    on this index (open now, or at least one closed trade) - no point
    fetching an index's candles if nothing has ever traded it.
    """

    for _, cfg in ALL_STRATEGIES:

        if cfg["index"] != index:
            continue

        portfolio = _load_json(cfg["portfolio_file"])

        if portfolio.get("Position") is not None or portfolio.get("Closed Trades"):
            return True

    return False


def main():

    symbols = _collect_equity_symbols()

    for index, ticker in _INDEX_TICKERS.items():
        if _any_options_strategy_has_activity(index):
            symbols[index] = ticker

    print(f"Refreshing Fyers candles for {len(symbols)} symbol(s): {', '.join(sorted(symbols))}")

    candles_by_symbol = {}

    for display_name, symbol in symbols.items():

        try:
            candles_by_symbol[display_name] = fetch_candles(symbol)
        except Exception as e:
            # One bad symbol must never take down the chart data for
            # every other symbol.
            print(f"  {display_name} ({symbol}): fetch failed - {e}")
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
