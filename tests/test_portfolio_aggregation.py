import json

import pandas as pd

from strategy.portfolio_aggregation import (
    cluster_correlated_books,
    compute_correlation_matrix,
    load_daily_pnl,
)


def _write_portfolio(path, closed_trades):
    path.write_text(json.dumps({"Cash": 100000, "Closed Trades": closed_trades}))


def test_load_daily_pnl_sums_same_day_trades(tmp_path):
    portfolio_file = tmp_path / "book_portfolio.json"
    _write_portfolio(portfolio_file, [
        {"Exit Time": "2026-08-10 10:00:00", "Net PnL": 100.0},
        {"Exit Time": "2026-08-10 14:00:00", "Net PnL": -30.0},
        {"Exit Time": "2026-08-11 09:00:00", "Net PnL": 50.0},
    ])

    daily_pnl = load_daily_pnl(str(portfolio_file))

    assert daily_pnl == {"2026-08-10": 70.0, "2026-08-11": 50.0}


def test_load_daily_pnl_missing_file_returns_empty_dict():
    assert load_daily_pnl("reports/does_not_exist_portfolio.json") == {}


def test_load_daily_pnl_falls_back_to_pnl_when_net_pnl_absent(tmp_path):
    portfolio_file = tmp_path / "book_portfolio.json"
    _write_portfolio(portfolio_file, [{"Exit Time": "2026-08-10 10:00:00", "PnL": 42.0}])

    assert load_daily_pnl(str(portfolio_file)) == {"2026-08-10": 42.0}


def test_correlation_matrix_drops_books_with_too_little_data():
    daily_pnl_by_book = {
        "book_a": {f"2026-08-{d:02d}": d for d in range(1, 8)},
        "book_b": {f"2026-08-{d:02d}": d for d in range(1, 8)},
        "book_c": {"2026-08-01": 5, "2026-08-02": -3},  # only 2 days, below the minimum
    }

    corr, insufficient = compute_correlation_matrix(daily_pnl_by_book, min_overlapping_days=5)

    assert set(corr.columns) == {"book_a", "book_b"}
    assert insufficient == ["book_c"]


def test_correlation_matrix_finds_perfectly_correlated_books():
    daily_pnl_by_book = {
        "book_a": {f"2026-08-{d:02d}": d * 10 for d in range(1, 8)},
        "book_b": {f"2026-08-{d:02d}": d * 10 for d in range(1, 8)},  # identical series
    }

    corr, _ = compute_correlation_matrix(daily_pnl_by_book, min_overlapping_days=5)

    assert corr.loc["book_a", "book_b"] == 1.0


def test_cluster_correlated_books_groups_high_correlation_pairs():
    corr = pd.DataFrame(
        [[1.0, 0.99, 0.1], [0.99, 1.0, 0.05], [0.1, 0.05, 1.0]],
        index=["a", "b", "c"],
        columns=["a", "b", "c"],
    )

    clusters = cluster_correlated_books(corr, threshold=0.9)

    assert sorted(clusters, key=len) == [["c"], sorted(["a", "b"])]


def test_cluster_correlated_books_transitive_grouping():
    # a-b correlated, b-c correlated, a-c not directly checked above
    # threshold but should still land in the same cluster transitively.
    corr = pd.DataFrame(
        [[1.0, 0.95, 0.2], [0.95, 1.0, 0.92], [0.2, 0.92, 1.0]],
        index=["a", "b", "c"],
        columns=["a", "b", "c"],
    )

    clusters = cluster_correlated_books(corr, threshold=0.9)

    assert clusters == [sorted(["a", "b", "c"])] or sorted(clusters[0]) == ["a", "b", "c"]


def test_cluster_correlated_books_no_correlation_gives_singleton_clusters():
    corr = pd.DataFrame(
        [[1.0, 0.1], [0.1, 1.0]],
        index=["a", "b"],
        columns=["a", "b"],
    )

    clusters = cluster_correlated_books(corr, threshold=0.9)

    assert sorted(clusters) == [["a"], ["b"]]
