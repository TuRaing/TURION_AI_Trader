import sys

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

    position_note = open_equity_paper_position(result["Best Trade"])

    save_best_trade(result)

    message = format_best_trade_message(result, position_note)
    send_telegram_message(message)


def open_equity_paper_position(best):
    """
    If today's locked pick is an equity trade, open it as today's single
    Best Trade paper position (auto square-off ~15:15 IST via
    square_off_best_trade.py - see strategy/best_trade_paper_trading.py).
    Index option picks are never opened here - no reliable live premium
    feed exists to mark P&L against, so they stay recommendation-only.
    """

    if best is None:
        return None

    if best["Type"] != "Equity Intraday":
        return "Index option pick - recommendation only, no live premium feed to track P&L."

    portfolio = load_best_trade_portfolio()

    stop_loss, target = calculate_atr_levels(best["Price"], best["ATR"], best["Decision"])

    portfolio, action = open_best_trade(
        portfolio, best["Name"], best["Symbol"], best["Decision"],
        best["Price"], stop_loss, target
    )

    save_best_trade_portfolio(portfolio)

    print(f"Best Trade paper position: {action}")

    if action == "OPENED":
        return f"Paper position OPENED @ {best['Price']} (SL {stop_loss:.2f} / Target {target:.2f}) - auto square-off ~15:15 IST if still open."

    return "A Best Trade position is already open today - not opening another."


def score_symbol_news(name, headline_pool):

    return score_sentiment(headline_pool, keywords=[name])


if __name__ == "__main__":
    main()
