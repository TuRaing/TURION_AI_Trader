from strategy.backtest_live_engine import run_backtest, run_live_check

# A toy flat Target/Stop-Loss decide_fn, used only to exercise the
# engine - real strategies supply their own. Kept deliberately simple:
# BUY at 100 if flat, close on Target (+10) or Stop-Loss (-10).


def _toy_decide_fn(cfg, position, data_point):

    price = data_point["price"]

    if position is None:
        return "OPENED", {"Entry Price": price}, None

    entry = position["Entry Price"]

    if price >= entry + cfg["target"]:
        trade = {"Entry Price": entry, "Exit Price": price, "Net PnL": price - entry}
        return "CLOSED (Target)", None, trade

    if price <= entry - cfg["stop_loss"]:
        trade = {"Entry Price": entry, "Exit Price": price, "Net PnL": price - entry}
        return "CLOSED (Stop Loss)", None, trade

    return "HELD", position, None


CFG = {"target": 10, "stop_loss": 10}
DATA_POINTS = [
    {"price": 100},  # opens
    {"price": 105},  # held
    {"price": 112},  # closes on target, +12
    {"price": 100},  # opens again
    {"price": 90},   # closes on stop loss, -10
]


def test_run_backtest_replays_every_data_point():
    portfolio, actions = run_backtest(_toy_decide_fn, CFG, DATA_POINTS, initial_capital=1000.0)

    assert actions == ["OPENED", "HELD", "CLOSED (Target)", "OPENED", "CLOSED (Stop Loss)"]
    assert len(portfolio["Closed Trades"]) == 2
    assert portfolio["Cash"] == 1000.0 + 12 + (-10)
    assert portfolio["Position"] is None


def test_run_live_check_matches_backtest_step_for_step():
    # Feeding the SAME data points one at a time through run_live_check
    # (as a real cron-triggered strategy would, one call per check)
    # must produce the exact same end state as run_backtest fed the
    # whole list at once - this is the whole point of a shared engine:
    # there is only one decide_fn, so there is nothing to diverge.
    backtest_portfolio, _ = run_backtest(_toy_decide_fn, CFG, DATA_POINTS, initial_capital=1000.0)

    live_portfolio = {"Cash": 1000.0, "Position": None, "Closed Trades": []}
    for data_point in DATA_POINTS:
        _, live_portfolio = run_live_check(_toy_decide_fn, CFG, live_portfolio, data_point)

    assert live_portfolio == backtest_portfolio


def test_run_live_check_returns_the_action_for_this_one_step():
    portfolio = {"Cash": 1000.0, "Position": None, "Closed Trades": []}

    action, portfolio = run_live_check(_toy_decide_fn, CFG, portfolio, {"price": 100})

    assert action == "OPENED"
    assert portfolio["Position"] == {"Entry Price": 100}


def test_run_backtest_with_no_trades_leaves_cash_untouched():
    def _never_trades(cfg, position, data_point):
        return "HELD", position, None

    portfolio, actions = run_backtest(_never_trades, {}, [{"price": 100}] * 3, initial_capital=500.0)

    assert portfolio["Cash"] == 500.0
    assert portfolio["Closed Trades"] == []
    assert actions == ["HELD", "HELD", "HELD"]
