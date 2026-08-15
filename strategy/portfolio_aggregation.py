# Added 15-Aug-2026 - Portfolio-level Aggregation, first cut (view-only,
# per the user's explicit "एकत्रित PnL/Risk view आधी बांधू" decision).
# Purely additive - reads existing portfolio JSON files, never writes to
# them, never touches any strategy's live logic. Answers: across all of
# options_strategies.ALL_STRATEGIES, how many books are actually
# INDEPENDENT bets vs how many are near-duplicates of each other (the
# 0.99-1.00 BANKNIFTY-RSI-family correlation finding from 14-Aug), and
# what does the TRUE combined equity curve look like once that's
# accounted for.

import json
from collections import defaultdict

import pandas as pd

from strategy.options_strategies import ALL_STRATEGIES

MIN_OVERLAPPING_DAYS = 5   # below this, a correlation number is noise, not signal
CORRELATION_THRESHOLD = 0.9  # matches the 14-Aug finding's own "0.99-1.00" bar, loosened slightly


def book_key(cfg):

    return f"{cfg['name']}_{cfg['index'].lower()}"


def load_daily_pnl(portfolio_file):
    """
    Real Net PnL per calendar day, from a book's Closed Trades - one
    number per day it actually exited a trade, nothing interpolated or
    assumed for quiet days.
    """

    try:
        with open(portfolio_file, "r") as f:
            portfolio = json.load(f)
    except FileNotFoundError:
        return {}

    daily_pnl = defaultdict(float)

    for trade in portfolio.get("Closed Trades", []):

        exit_time = trade.get("Exit Time")

        if not exit_time:
            continue

        date = exit_time[:10]
        pnl = trade.get("Net PnL", trade.get("PnL", 0.0))
        daily_pnl[date] += pnl

    return dict(daily_pnl)


def load_all_books_daily_pnl():
    """
    {book_key: {date: pnl}} for every book in ALL_STRATEGIES, real data
    only - books with zero closed trades come back as an empty dict,
    not fabricated.
    """

    result = {}

    for _, cfg in ALL_STRATEGIES:

        result[book_key(cfg)] = load_daily_pnl(cfg["portfolio_file"])

    return result


def compute_correlation_matrix(daily_pnl_by_book, min_overlapping_days=MIN_OVERLAPPING_DAYS):
    """
    Pairwise correlation of daily PnL between books that have enough
    REAL overlapping trading days - pandas' own pairwise-complete
    correlation, but books with fewer than min_overlapping_days total
    data points anywhere are dropped entirely first (a 2-day-old book
    correlating "1.00" with anything is noise, not a finding).
    """

    eligible = {k: v for k, v in daily_pnl_by_book.items() if len(v) >= min_overlapping_days}

    if len(eligible) < 2:
        return pd.DataFrame(), sorted(set(daily_pnl_by_book) - set(eligible))

    frame = pd.DataFrame(eligible)
    corr = frame.corr(min_periods=min_overlapping_days)

    return corr, sorted(set(daily_pnl_by_book) - set(eligible))


def cluster_correlated_books(correlation_matrix, threshold=CORRELATION_THRESHOLD):
    """
    Union-find over the correlation matrix: any two books correlated
    at/above `threshold` land in the same cluster. Returns clusters
    sorted largest-first; a book with no high-correlation partner is
    still returned as its own single-book cluster (it IS an
    independent bet, that's the point of this whole function).
    """

    books = list(correlation_matrix.columns)
    parent = {b: b for b in books}

    def find(b):
        while parent[b] != b:
            parent[b] = parent[parent[b]]
            b = parent[b]
        return b

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, a in enumerate(books):
        for b in books[i + 1:]:
            value = correlation_matrix.loc[a, b]
            if pd.notna(value) and value >= threshold:
                union(a, b)

    clusters = defaultdict(list)
    for b in books:
        clusters[find(b)].append(b)

    return sorted(clusters.values(), key=len, reverse=True)


def compute_portfolio_summary(initial_capital_per_book=100000.0):
    """
    Top-level numbers for a Portfolio Aggregation view: real combined
    Cash/PnL across every book (this part needs no correlation
    reasoning, plain addition is correct), plus the "true independent
    bet count" from clustering - the number that plain addition can't
    tell you.
    """

    total_cash = 0.0
    total_initial = 0.0
    books_with_data = 0

    for _, cfg in ALL_STRATEGIES:

        try:
            with open(cfg["portfolio_file"], "r") as f:
                portfolio = json.load(f)
            cash = portfolio.get("Cash", initial_capital_per_book)
            if portfolio.get("Closed Trades") or portfolio.get("Positions"):
                books_with_data += 1
        except FileNotFoundError:
            cash = initial_capital_per_book

        total_cash += cash
        total_initial += initial_capital_per_book

    daily_pnl_by_book = load_all_books_daily_pnl()
    corr, insufficient_data = compute_correlation_matrix(daily_pnl_by_book)

    clusters = cluster_correlated_books(corr) if not corr.empty else []

    return {
        "total_books": len(ALL_STRATEGIES),
        "books_with_data": books_with_data,
        "total_cash": round(total_cash, 2),
        "total_initial": round(total_initial, 2),
        "total_pnl": round(total_cash - total_initial, 2),
        "eligible_for_correlation": len(daily_pnl_by_book) - len(insufficient_data),
        "insufficient_data_count": len(insufficient_data),
        "clusters": clusters,
        "independent_bet_count": len(clusters) + len(insufficient_data),
    }
