from strategy.backtest_engine import summarize_trades, close_trade


def _trade(pnl, reason="Target"):
    return {
        "Entry Time": "t1",
        "Entry Price": 100,
        "Exit Time": "t2",
        "Exit Price": 100 + pnl,
        "Exit Reason": reason,
        "PnL": pnl,
    }


def test_empty_trades():
    s = summarize_trades([])
    assert s["Total Trades"] == 0
    assert s["Win Rate"] == 0
    assert s["Total PnL"] == 0
    assert s["Max Drawdown"] == 0


def test_win_loss_counts():
    s = summarize_trades([_trade(10), _trade(-5), _trade(20), _trade(-5)])
    assert s["Total Trades"] == 4
    assert s["Wins"] == 2
    assert s["Losses"] == 2
    assert s["Win Rate"] == 50.0
    assert s["Total PnL"] == 20


def test_zero_pnl_counts_as_loss():
    # PnL <= 0 is a loss by definition
    s = summarize_trades([_trade(0)])
    assert s["Losses"] == 1
    assert s["Wins"] == 0


def test_max_drawdown():
    # equity path: +50, then -30 -> peak 50, trough 20, drawdown 30
    s = summarize_trades([_trade(50), _trade(-30)])
    assert s["Max Drawdown"] == 30


def test_exit_reason_breakdown():
    s = summarize_trades([_trade(10, "Target"), _trade(-5, "Stop Loss"), _trade(8, "Target")])
    assert s["Exit Reasons"]["Target"] == 2
    assert s["Exit Reasons"]["Stop Loss"] == 1


def test_close_trade_computes_pnl():
    position = {"Entry Time": "t1", "Entry Price": 100, "Quantity": 1}
    trade = close_trade(position, "t2", 108, "Target")
    assert trade["PnL"] == 8
    assert trade["Exit Reason"] == "Target"
