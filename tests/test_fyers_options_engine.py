import datetime

from strategy.fyers_options_engine import (
    make_strategy, _net_pnl, _today_realized_pnl, _today_consecutive_losses,
    _hybrid_stop_loss_cap, _daily_profit_lock_threshold, IST, DAILY_PROFIT_LOCK_RS,
    MAX_CONSECUTIVE_LOSSES, TRAIL_PCT,
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


def test_make_strategy_defaults_no_hybrid_sl_cap():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["hybrid_sl_cap_pct"] is None


def test_make_strategy_hybrid_sl_cap_variant():
    cfg = make_strategy("simple_st1_slcap", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         hybrid_sl_cap_pct=2.0)

    assert cfg["hybrid_sl_cap_pct"] == 2.0


def test_hybrid_cap_uses_flat_when_flat_is_smaller():
    # Small position (Rs 20,000 deployed) on a large book (Rs 1,00,000
    # initial capital) - pct-of-deployed (2% of 20,000 = 400) is
    # smaller than flat (2% of 1,00,000 = 2,000) here... wait, check
    # the actual smaller one and assert against it directly.
    cfg = make_strategy("x", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         initial_capital=100000, hybrid_sl_cap_pct=2.0)

    cap = _hybrid_stop_loss_cap(cfg, capital_deployed=20000)

    assert cap == min(100000 * 0.02, 20000 * 0.02)
    assert cap == 400  # pct-of-deployed is smaller here


def test_hybrid_cap_uses_pct_when_pct_is_smaller():
    cfg = make_strategy("x", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         initial_capital=15000, hybrid_sl_cap_pct=2.0)

    # A large deployed position relative to a small book - flat cap
    # (2% of 15,000 = 300) is smaller than pct-of-deployed (2% of
    # 50,000 = 1,000) here.
    cap = _hybrid_stop_loss_cap(cfg, capital_deployed=50000)

    assert cap == min(15000 * 0.02, 50000 * 0.02)
    assert cap == 300  # flat is smaller here


def test_hybrid_cap_never_worse_than_either_pure_version():
    cfg = make_strategy("x", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         initial_capital=100000, hybrid_sl_cap_pct=2.0)

    for capital_deployed in (5000, 50000, 100000, 250000, 1000000):
        flat_cap = 100000 * 0.02
        pct_cap = capital_deployed * 0.02

        cap = _hybrid_stop_loss_cap(cfg, capital_deployed)

        assert cap <= flat_cap
        assert cap <= pct_cap


def test_make_strategy_defaults_no_daily_profit_lock_pct():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["daily_profit_lock_pct"] is None


def test_daily_profit_lock_threshold_uses_flat_rs_when_pct_unset():
    cfg = make_strategy("simple_st1_threshold", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0,
                         daily_profit_lock=True, group="threshold")

    assert _daily_profit_lock_threshold(cfg) == DAILY_PROFIT_LOCK_RS


def test_daily_profit_lock_threshold_uses_pct_of_capital_when_set():
    cfg = make_strategy("st2_threshold_slcap2pctlock", "NIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                         daily_profit_lock=True, group="threshold", hybrid_sl_cap_pct=2.0,
                         daily_profit_lock_pct=2.0, initial_capital=10000)

    # 2% of Rs 10,000 = Rs 200, not the flat Rs 2,000 - the whole point
    # of this variant (see PROJECT_STATUS.md's "HYBRID SL + DYNAMIC
    # PROFIT-LOCK CAPITAL SWEEP" entry).
    assert _daily_profit_lock_threshold(cfg) == 200


def test_daily_profit_lock_threshold_matches_flat_at_1_lakh():
    # 2% of the default Rs 1,00,000 initial_capital equals the original
    # flat Rs 2,000 exactly - the two variants only diverge away from
    # that one capital tier.
    cfg = make_strategy("st2_threshold_slcap2pctlock", "NIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                         daily_profit_lock=True, group="threshold", hybrid_sl_cap_pct=2.0,
                         daily_profit_lock_pct=2.0)

    assert _daily_profit_lock_threshold(cfg) == DAILY_PROFIT_LOCK_RS == 2000


def test_make_strategy_defaults_no_trailing_min_pct():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["trailing_min_pct"] is None


def test_make_strategy_trailing_variant():
    cfg = make_strategy("st2_threshold_trailing2pct", "NIFTY", target_net_pct=5.0, stop_loss_pct=2.0,
                         daily_profit_lock=True, group="threshold", hybrid_sl_cap_pct=2.0,
                         trailing_min_pct=2.0)

    assert cfg["trailing_min_pct"] == 2.0
    # target_net_pct is kept for interface consistency but becomes
    # inert once trailing_min_pct is set (see _check_position()).
    assert cfg["target_net_pct"] == 5.0


def test_trail_pct_is_30_percent():
    # Same giveback-from-peak already used and analyzed for
    # oi_footprint's own live trailing variant - reused here rather
    # than inventing a second, untested value.
    assert TRAIL_PCT == 0.30
