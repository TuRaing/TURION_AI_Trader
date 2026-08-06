import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import NIFTY_50_SYMBOLS
from strategy.fyers_data import fyers_download
from strategy.fyers_multi_timeframe_engine import get_multi_timeframe_signal
from strategy.fyers_best_trade_paper_trading import (
    load_best_trade_portfolio,
    save_best_trade_portfolio,
    open_best_trade,
    check_open_position,
    square_off_best_trade,
)
from strategy.risk_engine import calculate_atr_levels

# Added 04-Aug-2026 - Fyers-sourced counterpart to daily_best_trade.py,
# per this repo's engine-separation rule. Deliberately SIMPLER than the
# original: scans the NIFTY 50 watchlist directly for 15m/5m/1m
# alignment (no shortlist pre-filter, no news/option-chain ranking, no
# Excel/Telegram notification) - a manual-run test of the core
# intraday-equity mechanism on real Fyers data, not a full production
# replacement yet. Options picks are handled by the separate strategy/
# fyers_options_collector.py track, not this file.

IST = timezone(timedelta(hours=5, minutes=30))

ENTRY_START = (10, 0)
LAST_ENTRY_CUTOFF = (14, 15)
SQUAREOFF_TIME = (14, 45)


def _now_ist_hm():
    now = datetime.now(IST)
    return (now.hour, now.minute)


def _fetch_current_price(symbol):

    frame = fyers_download(symbol, period="5d", interval="1m")

    if frame is None or frame.empty:
        return None

    return float(frame["Close"].iloc[-1])


def monitor_open_position(portfolio):

    symbol = portfolio["Position"]["Symbol"]
    name = portfolio["Position"].get("Name", symbol)
    current_price = _fetch_current_price(symbol)

    if current_price is None:
        print(f"Could not fetch a current price for {symbol} - skipping.")
        return portfolio

    if _now_ist_hm() >= SQUAREOFF_TIME:
        portfolio, action = square_off_best_trade(portfolio, current_price)
    else:
        portfolio, action = check_open_position(portfolio, current_price)

    # A close sets portfolio["Position"] = None - dict.get()'s default only
    # applies when the KEY is missing, not when its value is None, so
    # `portfolio.get("Position", {}).get(...)` crashed here on every close
    # (caught upstream, but AFTER save_best_trade_portfolio never ran -
    # the close was computed correctly every time but never persisted).
    # Read the name from before the call instead of after.
    print(f"Open position ({name}): {action}")

    save_best_trade_portfolio(portfolio)

    return portfolio


def scan_for_entry(portfolio, symbols=NIFTY_50_SYMBOLS):

    print(f"Checking {len(symbols)} symbols for 15m/5m/1m alignment...")

    aligned = []

    for ticker in symbols:

        name = ticker.replace(".NS", "")
        signal = get_multi_timeframe_signal(name, ticker)

        if signal["Aligned"] and signal["Decision"] == "BUY":
            aligned.append(signal)
            print(f"  ALIGNED: {name} - {signal['Reason']}")

    if not aligned:
        print("No aligned BUY candidates this run.")
        return portfolio

    aligned.sort(key=lambda s: s["Confidence"], reverse=True)
    best = aligned[0]

    stop_loss, target = calculate_atr_levels(best["Price"], best["ATR"], best["Decision"])

    portfolio, action = open_best_trade(
        portfolio, best["Name"], best["Symbol"], best["Decision"],
        best["Price"], stop_loss, target,
    )

    print(f"Best Trade paper position: {action}")

    save_best_trade_portfolio(portfolio)

    return portfolio


def main():

    portfolio = load_best_trade_portfolio()

    if portfolio["Position"] is not None:
        monitor_open_position(portfolio)
        return

    hm = _now_ist_hm()

    if hm >= LAST_ENTRY_CUTOFF:
        print(f"Past {LAST_ENTRY_CUTOFF[0]:02d}:{LAST_ENTRY_CUTOFF[1]:02d} IST entry cutoff - not scanning for new entries.")
        return

    if hm < ENTRY_START:
        print(f"Before {ENTRY_START[0]:02d}:{ENTRY_START[1]:02d} IST entry start - not scanning for new entries yet.")
        return

    scan_for_entry(portfolio)


if __name__ == "__main__":
    main()
