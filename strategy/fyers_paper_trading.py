from strategy.fyers_watchlist_scanner import download_watchlist, analyze_symbol, MIN_CANDLES
from strategy.paper_trading import (
    calculate_position_size,
    process_signal,
    INITIAL_CAPITAL,
    QUANTITY,
    BASE_RISK_PCT,
    CONFIDENCE_FLOOR,
    CONFIDENCE_CEILING,
    MAX_CONCURRENT_POSITIONS,
)
from strategy.risk_engine import calculate_atr_levels

import os
import json

# Added 04-Aug-2026 - Fyers-sourced counterpart to strategy/
# paper_trading.py, per this repo's engine-separation rule. Reuses
# calculate_position_size/process_signal/risk-cap constants unchanged
# (pure logic, no data-source dependency) - only the data source and
# the portfolio FILE are different, so this can run completely
# independently of (and in parallel with) the live yfinance-based
# Watchlist paper trading, never touching its state.
#
# TEST-ONLY portfolio - deliberately not wired into any GitHub Actions
# automation yet (per 04-Aug's plan: manual runs first, decide on
# automation - including the daily Fyers-token-refresh problem - later).

PORTFOLIO_FILE = "reports/fyers_test_portfolio.json"


def load_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Positions": {},
            "Closed Trades": [],
            "Data Source": "Fyers",
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def run_watchlist_paper_trading(symbols, period="6mo", interval="1d"):
    """
    Same contract/logic as strategy.paper_trading.run_watchlist_paper_trading,
    sourced from Fyers and written to its own PORTFOLIO_FILE.
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
