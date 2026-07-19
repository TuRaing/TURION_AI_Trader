import sys
import os
import json
from datetime import datetime

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import NIFTY_50_SYMBOLS, INDICES
from strategy.watchlist_scanner import scan_watchlist
from strategy.news_engine import get_market_news_sentiment, score_sentiment, classify_headline_sentiment
from strategy.option_chain_engine import get_option_chain_analysis
from strategy.options_decision_engine import get_options_decision

SHORTLIST_FILE = "reports/best_trade_shortlist.json"
SHORTLIST_SIZE = 6

OPTION_CHAIN_SYMBOLS = {
    "NIFTY 50": "NIFTY",
    "BANK NIFTY": "BANKNIFTY",
}


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


def score_symbol_news(name, headline_pool):

    return score_sentiment(headline_pool, keywords=[name])


def save_shortlist(shortlist):

    os.makedirs("reports", exist_ok=True)

    with open(SHORTLIST_FILE, "w") as f:
        json.dump(shortlist, f, indent=2)


def main():
    """
    Wide daily-interval scan across the whole Nifty 50 + index watchlist,
    news sentiment, and index option chain/decision - runs every ~30 min
    (see .github/workflows/best_trade_report.yml) and writes the result
    to reports/best_trade_shortlist.json for daily_best_trade.py (every
    ~5 min) to read. This context doesn't need to be fresher than 30
    min - it's the candidate universe, not the entry signal itself
    (that comes from live 15m/5m/1m alignment - see
    strategy/multi_timeframe_engine.py).
    """

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

    shortlisted_stocks = [c for c in stock_candidates if c["Decision"] in ("BUY", "SELL")][:SHORTLIST_SIZE]

    # Updated: 2026-07-19 - per-headline tags (not just the aggregate score
    # already in news_sentiment_by_symbol) so the mobile app's News tab can
    # show real headlines instead of only a per-stock number.
    market_headlines = [
        {"Headline": h, "Sentiment": classify_headline_sentiment(h)}
        for h in headline_pool
    ]

    shortlist = {
        "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Stocks": shortlisted_stocks,
        "Options": options_candidates,
        "News": news_sentiment_by_symbol,
        "Market Headlines": market_headlines,
    }

    save_shortlist(shortlist)

    print(f"Shortlist saved: {len(shortlisted_stocks)} stock candidates, {len(options_candidates)} option candidates.")


if __name__ == "__main__":
    main()
