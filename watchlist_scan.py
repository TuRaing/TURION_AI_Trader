import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.watchlist_scanner import scan_watchlist
from strategy.report_engine import print_watchlist_report, format_watchlist_message

from report.notifier import notify


def main():

    symbols = dict(INDICES)

    for ticker in NIFTY_50_SYMBOLS:
        symbols[ticker.replace(".NS", "")] = ticker

    print(f"Scanning {len(symbols)} symbols (NIFTY 50 + BankNifty + NIFTY 50 index)...")

    results = scan_watchlist(symbols, period="6mo", interval="1d")

    print_watchlist_report(results)

    message = format_watchlist_message(results)

    notify(message)


if __name__ == "__main__":
    main()
