import pandas as pd

from strategy.futures_signal_backtest import (
    calculate_worst_case_lots,
    close_trade,
    summarize_trades,
    _run_on_data,
)


def _make_ohlcv(n=200, start_price=24500.0, seed=7):

    import random

    random.seed(seed)

    dates = pd.date_range("2026-01-01 09:15", periods=n, freq="5min")

    closes = [start_price]

    for _ in range(n - 1):
        closes.append(closes[-1] + random.uniform(-20, 20))

    close = pd.Series(closes, index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + 5
    low = pd.concat([open_, close], axis=1).min(axis=1) - 5
    volume = pd.Series([1000] * n, index=dates)

    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume})


def test_worst_case_lots_basic_math():
    # spot=24500, 10% worst case = 2450/point-equivalent move, lot_size=75
    # worst_case_loss_per_lot = 24500 * 0.10 * 75 = 183,750
    lots = calculate_worst_case_lots(capital=500000, spot=24500, lot_size=75, worst_case_move_pct=10.0)

    assert lots == 500000 // 183750  # == 2


def test_worst_case_lots_zero_when_capital_too_small():
    lots = calculate_worst_case_lots(capital=50000, spot=24500, lot_size=75, worst_case_move_pct=10.0)

    assert lots == 0


def test_worst_case_lots_more_conservative_than_margin_based():
    # A margin-based approach (~12%) would allow MORE lots than the
    # worst-case (10% INSTANT move) approach for the same capital,
    # since margin assumes normal SL execution, not an instant gap -
    # confirms this sizing is deliberately more conservative, per the
    # user's explicit safety request.
    capital = 250000
    spot = 24500
    lot_size = 75

    worst_case_lots = calculate_worst_case_lots(capital, spot, lot_size, worst_case_move_pct=10.0)
    margin_based_lots = int(capital // (spot * 0.12 * lot_size))

    assert worst_case_lots <= margin_based_lots


def test_worst_case_lots_zero_on_zero_spot():
    assert calculate_worst_case_lots(capital=100000, spot=0, lot_size=75) == 0


def test_close_trade_buy_profit():
    position = {"Direction": "BUY", "Entry Time": "t1", "Entry Price": 24500, "Quantity": 75}

    trade = close_trade(position, "t2", 24600, "Target")

    assert trade["PnL"] == (24600 - 24500) * 75
    assert trade["Net PnL"] < trade["PnL"]  # cost subtracted
    assert trade["Direction"] == "BUY"


def test_close_trade_sell_profit_on_price_drop():
    position = {"Direction": "SELL", "Entry Time": "t1", "Entry Price": 24500, "Quantity": 75}

    trade = close_trade(position, "t2", 24400, "Target")

    assert trade["PnL"] == (24500 - 24400) * 75


def test_summarize_trades_flags_capital_never_negative_in_safe_scenario():
    trades = [
        {"Net PnL": -1000, "PnL": -1000, "Cost": 0, "Exit Reason": "Stop Loss"},
        {"Net PnL": 2000, "PnL": 2000, "Cost": 0, "Exit Reason": "Target"},
    ]

    result = summarize_trades(trades, starting_capital=100000)

    assert result["Capital Ever Negative"] is False
    assert result["Minimum Capital Seen"] == 99000


def test_summarize_trades_detects_capital_going_negative():
    # A deliberately unsafe sequence (as if worst-case sizing were
    # bypassed) - confirms the safety check itself actually catches it.
    trades = [
        {"Net PnL": -150000, "PnL": -150000, "Cost": 0, "Exit Reason": "Stop Loss"},
    ]

    result = summarize_trades(trades, starting_capital=100000)

    assert result["Capital Ever Negative"] is True
    assert result["Minimum Capital Seen"] == -50000


def test_run_on_data_with_adx_filter_runs_without_error():
    # NOTE: the ADX filter makes each INDIVIDUAL entry check more
    # restrictive, but total trade COUNT isn't guaranteed to go down -
    # a held position blocks new entries, so a filter that changes
    # WHICH candles trigger entries can also change how long positions
    # stay open, and therefore how many distinct trades fit in the
    # same window (confirmed on real data: BANKNIFTY showed MORE
    # trades with the filter on, not fewer - a real, non-buggy result
    # of this path dependency, not an invariant to assert against).
    data = _make_ohlcv()

    with_filter = _run_on_data(
        data, lot_size=75, atr_sl_mult=1.0, atr_target_mult=2.0, starting_capital=250000,
        worst_case_move_pct=10.0, allow_short=True, require_adx_filter=True, adx_threshold=25,
    )

    assert "Total Trades" in with_filter
    assert with_filter["Total Trades"] == len(with_filter["Trades"])


def test_summarize_trades_win_rate_and_totals():
    trades = [
        {"Net PnL": 100, "PnL": 120, "Cost": 20, "Exit Reason": "Target"},
        {"Net PnL": -50, "PnL": -40, "Cost": 10, "Exit Reason": "Stop Loss"},
    ]

    result = summarize_trades(trades, starting_capital=100000)

    assert result["Total Trades"] == 2
    assert result["Win Rate"] == 50.0
    assert result["Net PnL"] == 50
    assert result["Total Cost"] == 30
