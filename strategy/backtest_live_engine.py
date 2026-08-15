# Added 15-Aug-2026 - Shared Backtest-Live Engine, per the 08-Aug
# decision (see doc/PROJECT_STATUS.md's "GAPS VS A PROFESSIONAL ALGO
# TRADING SYSTEM" #6): a real divergence already happened once -
# nifty_options_backtest.py's hand-written, Black-Scholes-estimated
# logic showed +69%/57 days, while the SEPARATE hand-written live
# module showed a large real loss on the same idea. Two independently
# hand-written copies of "the same" entry/exit logic can silently
# drift apart.
#
# This module does NOT touch any of the 59 already-running books -
# per the 08-Aug decision, existing strategies keep their own
# hand-written check functions untouched. This is FRAMEWORK ONLY,
# for the next NEW strategy idea: write its entry/exit rule as one
# `decide_fn`, and run THE SAME FUNCTION through both run_backtest()
# (fed a list of historical data points) and run_live_check() (fed
# one live data point per cron trigger) - there is no second copy to
# drift out of sync with the first, because there is only one.
#
# `decide_fn` contract (caller-supplied, pure):
#   decide_fn(cfg, position, data_point) -> (action, new_position, trade_record)
#     cfg          : dict of strategy parameters (caller-defined)
#     position     : dict describing the open position, or None
#     data_point   : one bar/tick/snapshot (caller-defined shape -
#                    the SAME shape must come from both the historical
#                    data list and the live data source)
#     action       : short string for logging ("OPENED", "CLOSED", "HELD", ...)
#     new_position : dict (open) or None (flat) - stored back onto the portfolio
#     trade_record : dict to append to Closed Trades, or None if nothing closed
#                    (must include "Net PnL" if not None - added straight to Cash)


def _step(decide_fn, cfg, portfolio, data_point):

    action, new_position, trade_record = decide_fn(cfg, portfolio.get("Position"), data_point)

    portfolio["Position"] = new_position

    if trade_record is not None:
        portfolio["Cash"] += trade_record["Net PnL"]
        portfolio.setdefault("Closed Trades", []).append(trade_record)

    return action, portfolio


def run_backtest(decide_fn, cfg, historical_data_points, initial_capital=100000.0):
    """
    Replays historical_data_points through decide_fn one at a time,
    building up a simulated portfolio exactly the way run_live_check()
    would build up a real one - same function, same step logic.

    Returns the final portfolio dict (Cash, Position, Closed Trades)
    plus the action taken at every step, for inspection.
    """

    portfolio = {"Cash": initial_capital, "Position": None, "Closed Trades": []}
    actions = []

    for data_point in historical_data_points:
        action, portfolio = _step(decide_fn, cfg, portfolio, data_point)
        actions.append(action)

    return portfolio, actions


def run_live_check(decide_fn, cfg, portfolio, live_data_point):
    """
    Feeds exactly ONE live data point through the identical _step()
    a backtest run uses. Call once per cron-triggered check, same
    calling convention every live strategy in this project already
    follows (load portfolio, check, save portfolio).
    """

    return _step(decide_fn, cfg, portfolio, live_data_point)
