import sys
from datetime import datetime, timedelta, timezone

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.watchlist_scanner import scan_watchlist
from strategy.news_engine import get_market_news_sentiment, score_sentiment
from strategy.option_chain_engine import get_option_chain_analysis
from strategy.options_decision_engine import get_options_decision
from strategy.best_trade_engine import rank_trade_candidates, pick_best_trade
from strategy.best_trade_paper_trading import (
    load_best_trade_portfolio,
    save_best_trade_portfolio,
    open_best_trade,
)
from strategy.risk_engine import calculate_atr_levels
from strategy.report_engine import print_best_trade_report, format_best_trade_message

from report.telegram_notifier import send_telegram_message
from report.excel_report import save_best_trade

OPTION_CHAIN_SYMBOLS = {
    "NIFTY 50": "NIFTY",
    "BANK NIFTY": "BANKNIFTY",
}

IST = timezone(timedelta(hours=5, minutes=30))

# Stop locking new positions this close to the 15:15 IST square-off - a
# trade opened with only a few minutes of runway before it gets force-closed
# isn't a real intraday trade, it's noise.
LAST_ENTRY_CUTOFF = (14, 45)


def _past_entry_cutoff():

    now_ist = datetime.now(IST)
    cutoff_hour, cutoff_minute = LAST_ENTRY_CUTOFF

    return (now_ist.hour, now_ist.minute) >= (cutoff_hour, cutoff_minute)


def build_options_candidates(index_results):
    """
    For every index in the watchlist scan (NIFTY 50, BANK NIFTY), pull
    its option chain and turn (price-action bias + option chain) into
    a CE/PE decision. Kept separate from equity scoring throughout -
    see strategy/options_decision_engine.py.
    """

    candidates = []

    for name, result in index_results.items():

        option_symbol = OPTION_CHAIN_SYMBOLS.get(name)

        if option_symbol is None:
            continue

        chain_analysis = get_option_chain_analysis(option_symbol)

        decision = get_options_decision(
            result["Bias"],
            result["Confidence"],
            chain_analysis,
        )

        candidates.append({
            "Name": name,
            "Bias": result["Bias"],
            "Decision": decision["Decision"],
            "Confidence": decision["Confidence"],
            "Reason": decision["Reason"],
        })

    return candidates


def main():
    """
    Runs every ~30 min through market hours (see
    .github/workflows/best_trade_report.yml), not just once - as soon as
    a good enough candidate shows up with no position currently open, it
    gets locked in and opened right then, instead of waiting for a fixed
    10:00 IST check. Two guards keep this cheap and sane:

    1. If a Best Trade position is already open today, skip the whole
       scan - one locked pick per day, same as before.
    2. Stop opening new positions within LAST_ENTRY_CUTOFF of the 15:15
       IST square-off - too little runway left to call it intraday.
    """

    portfolio = load_best_trade_portfolio()

    if portfolio["Position"] is not None:

        print(f"Best Trade position already open ({portfolio['Position']['Name']}) - skipping scan this run.")
        return

    if _past_entry_cutoff():

        print(f"Past {LAST_ENTRY_CUTOFF[0]:02d}:{LAST_ENTRY_CUTOFF[1]:02d} IST entry cutoff - skipping scan this run.")
        return

    symbols = dict(INDICES)

    for ticker in NIFTY_50_SYMBOLS:
        symbols[ticker.replace(".NS", "")] = ticker

    print(f"Analyzing {len(symbols)} symbols (NIFTY 50 + BankNifty + Nifty50 companies)...")

    results = scan_watchlist(symbols, period="6mo", interval="1d")

    index_results = {r["Name"]: r for r in results if r["Name"] in INDICES}
    stock_candidates = [r for r in results if r["Name"] not in INDICES]

    print("Fetching news headlines...")

    market_news = get_market_news_sentiment(limit=50)
    headline_pool = market_news["Headlines"]

    news_sentiment_by_symbol = {}

    for candidate in stock_candidates:
        news_sentiment_by_symbol[candidate["Name"]] = score_symbol_news(candidate["Name"], headline_pool)

    for name in index_results:
        news_sentiment_by_symbol[name] = score_symbol_news(name, headline_pool)

    print("Fetching option chain analysis (NIFTY / BANKNIFTY)...")

    options_candidates = build_options_candidates(index_results)

    ranked = rank_trade_candidates(stock_candidates, options_candidates, news_sentiment_by_symbol)
    result = pick_best_trade(ranked)

    print_best_trade_report(result)

    # Always logged to Excel for a full audit trail of every check, but
    # Telegram is reserved for an actual event (see below) so a 30-min
    # cadence doesn't turn into a dozen "nothing happened" pings a day.
    save_best_trade(result)

    position_note, opened = open_equity_paper_position(portfolio, result["Best Trade"])

    if opened:

        message = format_best_trade_message(result, position_note)
        send_telegram_message(message)

    else:

        print("No position opened this run - Telegram skipped (avoids repeat pings every ~30 min).")


def open_equity_paper_position(portfolio, best):
    """
    If today's locked pick is an equity trade, open it as today's single
    Best Trade paper position (auto square-off ~15:15 IST via
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
            "- auto square-off ~15:15 IST if still open.",
            True,
        )

    return "A Best Trade position is already open today - not opening another.", False


def score_symbol_news(name, headline_pool):

    return score_sentiment(headline_pool, keywords=[name])


if __name__ == "__main__":
    main()
