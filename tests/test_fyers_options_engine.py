import datetime

from strategy.fyers_options_engine import (
    make_strategy, _net_pnl, _today_realized_pnl, _today_consecutive_losses,
    IST, DAILY_PROFIT_LOCK_RS, MAX_CONSECUTIVE_LOSSES,
)


def test_make_strategy_nifty_uses_nifty_lot_and_strike():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["underlying_symbol"] == "NSE:NIFTY50-INDEX"
    assert cfg["portfolio_file"] == "reports/fyers_options_simple_st1_nifty_portfolio.json"


def test_make_strategy_banknifty_uses_banknifty_lot_and_strike():
    cfg = make_strategy("simple_st1", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["underlying_symbol"] == "NSE:NIFTYBANK-INDEX"
    assert cfg["portfolio_file"] == "reports/fyers_options_simple_st1_banknifty_portfolio.json"


def test_net_pnl_positive_when_premium_rises():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    pnl = _net_pnl(cfg, entry_premium=100, current_premium=110, lots=5)

    assert pnl > 0


def test_net_pnl_negative_when_premium_falls():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    pnl = _net_pnl(cfg, entry_premium=100, current_premium=90, lots=5)

    assert pnl < 0


def test_net_pnl_uses_banknifty_lot_size():
    nifty_cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)
    banknifty_cfg = make_strategy("simple_st1", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    nifty_pnl = _net_pnl(nifty_cfg, entry_premium=100, current_premium=110, lots=1)
    banknifty_pnl = _net_pnl(banknifty_cfg, entry_premium=100, current_premium=110, lots=1)

    # Same premium move, but NIFTY's lot size (75) is larger than
    # BANKNIFTY's (30), so 1 NIFTY lot's gross P&L is bigger.
    assert nifty_pnl > banknifty_pnl


def _exit_time_str(days_ago=0):
    """Exit Time is stored naive/UTC (see fyers_options_engine.py's
    convention) - build a value that round-trips to the right IST
    calendar day regardless of when this test actually runs."""

    ist_dt = datetime.datetime.now(IST) - datetime.timedelta(days=days_ago)
    return ist_dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def test_today_realized_pnl_sums_only_todays_closed_trades():
    portfolio = {
        "Closed Trades": [
            {"Exit Time": _exit_time_str(0), "Net PnL": 1500},
            {"Exit Time": _exit_time_str(0), "Net PnL": 800},
            {"Exit Time": _exit_time_str(2), "Net PnL": 9999},
        ]
    }

    assert _today_realized_pnl(portfolio) == 2300


def test_today_realized_pnl_zero_when_no_closed_trades():
    assert _today_realized_pnl({"Closed Trades": []}) == 0


def test_daily_profit_lock_threshold_is_2000_rupees():
    assert DAILY_PROFIT_LOCK_RS == 2000


def test_make_strategy_defaults_no_daily_profit_lock():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["daily_profit_lock"] is False
    assert cfg["group"] is None


def test_make_strategy_threshold_variant_keeps_same_ratios():
    cfg = make_strategy("simple_st1_threshold", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         daily_profit_lock=True, group="threshold")

    assert cfg["daily_profit_lock"] is True
    assert cfg["group"] == "threshold"
    assert cfg["target_net_pct"] == 3.0
    assert cfg["stop_loss_pct"] == 3.0
    assert cfg["portfolio_file"] == "reports/fyers_options_simple_st1_threshold_nifty_portfolio.json"


def test_max_consecutive_losses_threshold_is_2():
    assert MAX_CONSECUTIVE_LOSSES == 2


def test_make_strategy_defaults_no_daily_loss_lock():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["daily_loss_lock"] is False


def test_make_strategy_loss_lock_variant():
    cfg = make_strategy("st2_threshold", "BANKNIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                         daily_profit_lock=True, daily_loss_lock=True, group="threshold")

    assert cfg["daily_loss_lock"] is True


def test_today_consecutive_losses_counts_streak_from_most_recent():
    portfolio = {
        "Closed Trades": [
            {"Exit Time": _exit_time_str(0), "Net PnL": 1500},   # win - breaks any earlier streak
            {"Exit Time": _exit_time_str(0), "Net PnL": -800},
            {"Exit Time": _exit_time_str(0), "Net PnL": -600},
        ]
    }

    assert _today_consecutive_losses(portfolio) == 2


def test_today_consecutive_losses_zero_after_a_win():
    portfolio = {
        "Closed Trades": [
            {"Exit Time": _exit_time_str(0), "Net PnL": -800},
            {"Exit Time": _exit_time_str(0), "Net PnL": 1200},
        ]
    }

    assert _today_consecutive_losses(portfolio) == 0


def test_today_consecutive_losses_ignores_earlier_days():
    portfolio = {
        "Closed Trades": [
            {"Exit Time": _exit_time_str(2), "Net PnL": -500},
            {"Exit Time": _exit_time_str(2), "Net PnL": -500},
            {"Exit Time": _exit_time_str(0), "Net PnL": -300},
        ]
    }

    # only today's single loss counts, not yesterday's streak
    assert _today_consecutive_losses(portfolio) == 1


def test_today_consecutive_losses_zero_when_no_closed_trades():
    assert _today_consecutive_losses({"Closed Trades": []}) == 0
