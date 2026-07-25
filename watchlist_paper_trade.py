import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.paper_trading import run_watchlist_paper_trading
from strategy.report_engine import print_watchlist_paper_trade_report, format_watchlist_paper_trade_message

from report.notifier import notify


def main():

    symbols = dict(INDICES)

    for ticker in NIFTY_50_SYMBOLS:
        symbols[ticker.replace(".NS", "")] = ticker

    print(f"Running Watchlist Paper Trading on {len(symbols)} symbols...")

    portfolio, events = run_watchlist_paper_trading(symbols, period="6mo", interval="1d")

    print_watchlist_paper_trade_report(portfolio, events)

    message = format_watchlist_paper_trade_message(portfolio, events)

    notify(message)


if __name__ == "__main__":
    main()
