import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

import yfinance as yf

from strategy.best_trade_paper_trading import (
    load_best_trade_portfolio,
    save_best_trade_portfolio,
    square_off_best_trade,
)
from strategy.report_engine import print_best_trade_squareoff, format_best_trade_squareoff_message

from report.telegram_notifier import send_telegram_message


def main():

    portfolio = load_best_trade_portfolio()

    if portfolio["Position"] is None:

        print_best_trade_squareoff(None, "NO POSITION")
        return

    symbol = portfolio["Position"]["Symbol"]

    data = yf.download(symbol, period="5d", interval="15m", progress=False)

    if data.empty:

        print(f"Could not fetch a current price for {symbol} - skipping square-off this run.")
        return

    current_price = float(data["Close"].iloc[-1])

    portfolio, action = square_off_best_trade(portfolio, current_price)

    save_best_trade_portfolio(portfolio)

    closed_trade = portfolio["Closed Trades"][-1]

    print_best_trade_squareoff(closed_trade, action)

    message = format_best_trade_squareoff_message(closed_trade)
    send_telegram_message(message)


if __name__ == "__main__":
    main()
