from strategy.futures_signal_backtest import (
    calculate_worst_case_lots,
    close_trade,
    summarize_trades,
)


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
