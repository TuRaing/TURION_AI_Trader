import os
import json

from strategy.best_trade_paper_trading import (
    open_best_trade,
    check_open_position,
    square_off_best_trade,
    INITIAL_CAPITAL,
    QUANTITY,
)

# Added 04-Aug-2026 - Fyers-sourced counterpart to strategy/
# best_trade_paper_trading.py, per this repo's engine-separation rule.
# open_best_trade/check_open_position/square_off_best_trade are pure
# logic (portfolio dict + a price in, portfolio dict + action out) with
# no data-source dependency at all, so they're reused completely
# unchanged - only the portfolio FILE differs, keeping this test
# portfolio fully independent of the live one.

PORTFOLIO_FILE = "reports/fyers_best_trade_portfolio.json"


def load_best_trade_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Position": None,
            "Closed Trades": [],
            "Data Source": "Fyers",
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_best_trade_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)
