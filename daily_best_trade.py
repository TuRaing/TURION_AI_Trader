import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

import yfinance as yf

from strategy.best_trade_engine import rank_trade_candidates, pick_best_trade
from strategy.best_trade_paper_trading import (
    load_best_trade_portfolio,
    save_best_trade_portfolio,
    open_best_trade,
    check_open_position,
)
from strategy.multi_timeframe_engine import get_multi_timeframe_signal
from strategy.risk_engine import calculate_atr_levels
from strategy.report_engine import (
    print_best_trade_report,
    format_best_trade_message,
    print_best_trade_squareoff,
    format_best_trade_squareoff_message,
)

from report.notifier import notify
from report.excel_report import save_best_trade

from refresh_shortlist import SHORTLIST_FILE

IST = timezone(timedelta(hours=5, minutes=30))

BEST_TRADE_PICK_FILE = "reports/best_trade_pick.json"


def save_best_trade_pick(result):
    """
    Persist the latest pick_best_trade() result to JSON - Excel/Telegram
    already got it, but neither is machine-readable for the mobile app's
    Best Trade tab. Overwritten every scan (every ~5 min), so this always
    reflects the most recent check, not a history of past picks.
    """

    os.makedirs("reports", exist_ok=True)

    payload = dict(result)
    payload["Checked At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(BEST_TRADE_PICK_FILE, "w") as f:
        json.dump(payload, f, indent=2, default=str)

# Don't open a position in the first 45 min after NSE opens (09:15 IST) -
# opening-range volatility settles by then. Analysis/shortlist-checking
# still runs before this - only the actual entry waits.
ENTRY_START = (10, 0)

# Stop opening new positions this close to the 14:45 IST square-off (see
# square_off_best_trade.py / best_trade_squareoff.yml, itself 45 min before
# NSE's 15:30 close) - a trade opened with only a few minutes of runway
# before it gets force-closed isn't a real intraday trade, it's noise.
LAST_ENTRY_CUTOFF = (14, 15)


def _before_entry_start():

    now_ist = datetime.now(IST)
    start_hour, start_minute = ENTRY_START

    return (now_ist.hour, now_ist.minute) < (start_hour, start_minute)


def _past_entry_cutoff():

    now_ist = datetime.now(IST)
    cutoff_hour, cutoff_minute = LAST_ENTRY_CUTOFF

    return (now_ist.hour, now_ist.minute) >= (cutoff_hour, cutoff_minute)


def _fetch_current_price(symbol):

    data = yf.download(symbol, period="5d", interval="1m", progress=False)

    if data is None or data.empty:
        return None

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    return float(close.iloc[-1])


def main():
    """
    Runs every ~5 min through market hours (see .github/workflows/
    best_trade_entry_scan.yml) - GitHub's actual schedule floor, and
    also the cadence of the entry timeframe itself (5m), so there's no
    benefit to checking more often for *new* entries. Each run either:

    1. Checks today's already-open Best Trade position against a fresh
       price and closes it the moment Stop Loss/Target is hit (instead
       of only discovering that at the 14:45 IST square-off), or

    2. If no position is open and it's before the entry cutoff, reads
       the shortlist reports/best_trade_shortlist.json (written every
       ~30 min by refresh_shortlist.py) and checks each shortlisted
       stock's 15m/5m/1m alignment (strategy/multi_timeframe_engine.py)
       - 15m sets the trend, 5m is the entry decision, 1m confirms
       timing. Only aligned candidates are ranked; the day's index
       options candidate (computed by refresh_shortlist.py, reused
       as-is here - option chain/OI data is slow-moving and often
       unavailable on cloud anyway) competes on the same scale.

    A position closing early via Stop Loss/Target leaves the door open
    for the very next run to find a new entry (still before the entry
    cutoff) - "one locked pick" doesn't mean "one attempt no matter how
    fast it resolves."

    The alignment analysis itself runs on every eligible run regardless
    of time of day, but the actual position only opens between
    ENTRY_START (10:00 IST, 45 min after NSE opens - lets opening-range
    volatility settle) and LAST_ENTRY_CUTOFF (14:15 IST, 30 min before
    the 14:45 IST square-off).
    """

    portfolio = load_best_trade_portfolio()

    if portfolio["Position"] is not None:
        monitor_open_position(portfolio)
        return

    if _past_entry_cutoff():

        print(f"Past {LAST_ENTRY_CUTOFF[0]:02d}:{LAST_ENTRY_CUTOFF[1]:02d} IST entry cutoff - skipping scan this run.")
        return

    shortlist = load_shortlist()

    if shortlist is None:

        print(f"No shortlist yet at {SHORTLIST_FILE} - skipping this run (refresh_shortlist.py hasn't run yet today).")
        return

    scan_for_entry(portfolio, shortlist)


def monitor_open_position(portfolio):

    symbol = portfolio["Position"]["Symbol"]
    current_price = _fetch_current_price(symbol)

    if current_price is None:

        print(f"Could not fetch a current price for {symbol} - skipping this run.")
        return

    portfolio, action = check_open_position(portfolio, current_price)

    if action == "HOLD":

        print(f"Best Trade position ({portfolio['Position']['Name']}) holding - no Stop Loss/Target hit yet.")
        return

    save_best_trade_portfolio(portfolio)

    closed_trade = portfolio["Closed Trades"][-1]

    print_best_trade_squareoff(closed_trade, action)

    message = format_best_trade_squareoff_message(closed_trade)
    notify(message)


def load_shortlist():

    if not os.path.exists(SHORTLIST_FILE):
        return None

    with open(SHORTLIST_FILE, "r") as f:
        return json.load(f)


def scan_for_entry(portfolio, shortlist):

    print(f"Checking {len(shortlist['Stocks'])} shortlisted symbols for 15m/5m/1m alignment...")

    aligned_candidates = []

    for candidate in shortlist["Stocks"]:

        signal = get_multi_timeframe_signal(candidate["Name"], candidate["Symbol"])

        if not signal["Aligned"]:
            continue

        aligned_candidates.append({
            "Name": signal["Name"],
            "Symbol": signal["Symbol"],
            "Decision": signal["Decision"],
            "Bias": signal["Bias"],
            "Confidence": signal["Confidence"],
            "Price": signal["Price"],
            "ATR": signal["ATR"],
            "Candle Pattern": signal["5m"]["Candle Pattern"],
        })

    ranked = rank_trade_candidates(aligned_candidates, shortlist["Options"], shortlist["News"])
    result = pick_best_trade(ranked)

    print_best_trade_report(result)

    # Always logged to Excel for a full audit trail of every check, but
    # Telegram is reserved for an actual event (see below) so a 5-min
    # cadence doesn't turn into dozens of "nothing happened" pings a day.
    save_best_trade(result)
    save_best_trade_pick(result)

    if _before_entry_start():

        print(f"Before {ENTRY_START[0]:02d}:{ENTRY_START[1]:02d} IST entry start - analysis only, not opening a position yet.")
        return

    position_note, opened = open_equity_paper_position(portfolio, result["Best Trade"])

    if opened:

        message = format_best_trade_message(result, position_note)
        notify(message)

    else:

        print("No position opened this run - Telegram skipped (avoids repeat pings every ~5 min).")


def open_equity_paper_position(portfolio, best):
    """
    If today's locked pick is an equity trade, open it as today's single
    Best Trade paper position (auto square-off ~14:45 IST via
    square_off_best_trade.py - see strategy/best_trade_paper_trading.py).
    Index option picks are never opened here - no reliable live premium
    feed exists to mark P&L against, so they stay recommendation-only.

    Returns
    -------
    position_note : str or None
    opened : bool - True only when a new position was actually opened
        this run (caller uses this to decide whether to notify).
    """

    if best is None:
        return None, False

    if best["Type"] != "Equity Intraday":
        return "Index option pick - recommendation only, no live premium feed to track P&L.", False

    stop_loss, target = calculate_atr_levels(best["Price"], best["ATR"], best["Decision"])

    portfolio, action = open_best_trade(
        portfolio, best["Name"], best["Symbol"], best["Decision"],
        best["Price"], stop_loss, target
    )

    save_best_trade_portfolio(portfolio)

    print(f"Best Trade paper position: {action}")

    if action == "OPENED":
        return (
            f"Paper position OPENED @ {best['Price']} (SL {stop_loss:.2f} / Target {target:.2f}) "
            "- checked every ~5 min, auto square-off ~14:45 IST if still open.",
            True,
        )

    return "A Best Trade position is already open today - not opening another.", False


if __name__ == "__main__":
    main()
