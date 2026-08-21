from strategy.backtest_live_engine import run_backtest, run_live_check
from strategy.event_driven_engine import (
    rsi_momentum_decide_fn, make_st2_threshold_event_cfg, make_simple_st1_threshold_event_cfg,
    oi_footprint_decide_fn, make_oi_footprint_event_cfg,
)


def _cfg(**overrides):
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    cfg.update(overrides)
    return cfg


def _data_point(**overrides):
    point = {
        "timestamp": "2026-08-18 09:20:00",
        "spot": 24500.0,
        "rsi": 55.0,
        "ce_symbol": "NSE:NIFTY2681824500CE", "ce_ltp": 100.0, "ce_bid": 99.9, "ce_ask": 100.1,
        "pe_symbol": "NSE:NIFTY2681824500PE", "pe_ltp": 90.0, "pe_bid": 89.9, "pe_ask": 90.1,
        "past_squareoff": False,
    }
    point.update(overrides)
    return point


def test_opens_ce_when_rsi_at_or_above_50():
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(rsi=55.0))

    assert "OPENED CE" in action
    assert position["Option Type"] == "CE"
    assert position["Entry Premium"] == 100.0
    assert trade is None


def test_opens_pe_when_rsi_below_50():
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(rsi=45.0))

    assert "OPENED PE" in action
    assert position["Option Type"] == "PE"
    assert position["Entry Premium"] == 90.0


def test_skips_open_when_rsi_not_ready():
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(rsi=None))

    assert "SKIPPED" in action
    assert position is None
    assert trade is None


def test_skips_open_when_past_squareoff():
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(past_squareoff=True))

    assert "SKIPPED" in action
    assert position is None


def test_skips_open_when_before_market_open():
    # Real bug caught live (21-Aug-2026): a WebSocket connection
    # replays Fyers' last pre-market snapshot (often yesterday's
    # closing quote) before 09:15 IST - must not open a real-tracked
    # position on that stale data.
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(before_market_open=True))

    assert "SKIPPED (before market open)" in action
    assert position is None


def test_skips_open_when_daily_profit_lock_reached():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_rs=2000)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=2500))

    assert "SKIPPED (today's profit lock reached)" in action
    assert position is None


def test_daily_profit_lock_does_not_skip_below_threshold():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_rs=2000)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=1500))

    assert "OPENED" in action


def test_daily_profit_lock_ignored_when_flag_is_off():
    # daily_profit_lock defaults to False (make_st2_threshold_event_cfg)
    # - today_realized_pnl past the threshold must not matter.
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(today_realized_pnl=999999))

    assert "OPENED" in action


def test_daily_profit_lock_does_not_block_managing_an_existing_position():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_rs=2000)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=101.0, today_realized_pnl=2500)
    )

    assert "HELD" in action
    assert new_position is not None


def test_before_market_open_does_not_block_managing_an_existing_position():
    # Only NEW entries are gated - an already-open position (e.g. one
    # legitimately opened yesterday and carried overnight) must still
    # be checked for Target/Stop-Loss/Square-Off regardless of time,
    # matching fyers_options_engine.py's check_or_open() convention.
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=101.0, before_market_open=True)
    )

    assert "HELD" in action
    assert new_position is not None


def test_skips_open_when_capital_insufficient_for_one_lot():
    # 75 lot_size x 100 premium = Rs 7,500/lot - Rs 5,000 capital can't buy even 1
    action, position, trade = rsi_momentum_decide_fn(_cfg(initial_capital=5000), None, _data_point(rsi=55.0))

    assert "SKIPPED" in action
    assert position is None


def test_holds_when_neither_target_nor_sl_hit():
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=101.0))

    assert "HELD" in action
    assert new_position is not None
    assert trade is None


def test_closes_at_target():
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Target is 5% of initial_capital (Rs 5,000); need ce_ltp high enough to
    # clear both the 5% target AND real transaction costs.
    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=115.0))

    assert "CLOSED (Target)" in action
    assert new_position is None
    assert trade["Exit Reason"] == "Target"
    assert trade["Net PnL"] > 0


def test_closes_at_hybrid_stop_loss_when_set():
    cfg = _cfg(hybrid_sl_cap_pct=2.0)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Hybrid cap here is min(2% of 1,00,000, 2% of capital deployed) = Rs 2,000.
    # A big premium drop should breach it.
    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=70.0))

    assert "CLOSED (Stop Loss)" in action
    assert trade["Net PnL"] < 0


def test_closes_at_plain_stop_loss_when_hybrid_not_set():
    cfg = _cfg(hybrid_sl_cap_pct=None)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Plain stop_loss_pct = 2% of initial_capital, same Rs 2,000 threshold here.
    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=70.0))

    assert "CLOSED (Stop Loss)" in action


def test_closes_at_squareoff_when_neither_target_nor_sl_hit():
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=100.5, past_squareoff=True)
    )

    assert "CLOSED (Square-Off)" in action
    assert trade["Exit Reason"] == "Square-Off"


def test_skips_open_when_near_circuit_band():
    # previous_close 22270 -> 10% upper band = 24497 - spot 24500 is
    # only ~0.013% away, well inside the default 2% proximity gate.
    action, position, trade = rsi_momentum_decide_fn(
        _cfg(), None, _data_point(rsi=55.0, previous_close=22270.0)
    )

    assert "SKIPPED" in action
    assert "circuit" in action.lower()
    assert position is None


def test_opens_normally_when_far_from_circuit_band():
    # previous_close == spot -> 10% away from either band, nowhere near.
    action, position, trade = rsi_momentum_decide_fn(
        _cfg(), None, _data_point(rsi=55.0, previous_close=24500.0)
    )

    assert "OPENED" in action
    assert position is not None


def test_missing_previous_close_never_blocks_entry():
    # No "previous_close" key at all (older caller/test data) - the
    # gate must be skipped, not treated as "always near".
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(rsi=55.0))

    assert "OPENED" in action


def test_closes_at_circuit_risk_when_near_band_and_no_target_or_sl_hit():
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=100.5, previous_close=22270.0)
    )

    assert "CLOSED (Circuit Risk)" in action
    assert trade["Exit Reason"] == "Circuit Risk"


def test_circuit_risk_does_not_override_an_already_hit_target():
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Target is 5% net - a big enough premium jump hits Target first,
    # even though this same data_point is also near the circuit band.
    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=115.0, previous_close=22270.0)
    )

    assert "CLOSED (Target)" in action


def test_spread_pct_makes_the_same_trade_slightly_worse():
    cfg_no_spread = _cfg(spread_pct=None)
    cfg_with_spread = _cfg(spread_pct=0.26)

    _, pos_a, _ = rsi_momentum_decide_fn(cfg_no_spread, None, _data_point(rsi=55.0, ce_ltp=100.0))
    _, pos_b, _ = rsi_momentum_decide_fn(cfg_with_spread, None, _data_point(rsi=55.0, ce_ltp=100.0))

    _, _, trade_no_spread = rsi_momentum_decide_fn(cfg_no_spread, pos_a, _data_point(ce_ltp=115.0))
    _, _, trade_with_spread = rsi_momentum_decide_fn(cfg_with_spread, pos_b, _data_point(ce_ltp=115.0))

    assert trade_with_spread["Net PnL"] < trade_no_spread["Net PnL"]


def test_run_backtest_replays_a_full_open_then_close_sequence():
    cfg = _cfg()
    data_points = [
        _data_point(timestamp="t1", rsi=55.0, ce_ltp=100.0),   # opens CE
        _data_point(timestamp="t2", ce_ltp=105.0),             # holds
        _data_point(timestamp="t3", ce_ltp=115.0),             # closes at Target
    ]

    portfolio, actions = run_backtest(rsi_momentum_decide_fn, cfg, data_points, initial_capital=100000)

    assert "OPENED" in actions[0]
    assert "HELD" in actions[1]
    assert "CLOSED" in actions[2]
    assert len(portfolio["Closed Trades"]) == 1
    assert portfolio["Cash"] > 100000  # the Target trade was profitable


def test_run_live_check_matches_run_backtest_for_the_same_points_fed_one_at_a_time():
    # The actual guarantee this whole framework exists for (see test_
    # backtest_live_engine.py's own version of this test) - byte-
    # identical results whether fed as a batch or one live check at a
    # time, because both paths call the exact same decide_fn/_step().
    cfg = _cfg()
    data_points = [
        _data_point(timestamp="t1", rsi=55.0, ce_ltp=100.0),
        _data_point(timestamp="t2", ce_ltp=105.0),
        _data_point(timestamp="t3", ce_ltp=115.0),
    ]

    batch_portfolio, _ = run_backtest(rsi_momentum_decide_fn, cfg, data_points, initial_capital=100000)

    live_portfolio = {"Cash": 100000, "Position": None, "Closed Trades": []}
    for point in data_points:
        _, live_portfolio = run_live_check(rsi_momentum_decide_fn, cfg, live_portfolio, point)

    assert live_portfolio == batch_portfolio


# --- rsi_momentum_decide_fn with simple_st1_threshold's cfg (3%/3%,
# not st2_threshold's 5%/2%) - same decide_fn, proves the shared
# function actually respects cfg rather than having 5%/2% baked in.

def _st1_cfg(**overrides):
    cfg = make_simple_st1_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    cfg.update(overrides)
    return cfg


def test_simple_st1_threshold_cfg_uses_symmetric_3pct_ratios():
    cfg = _st1_cfg()

    assert cfg["target_net_pct"] == 3.0
    assert cfg["stop_loss_pct"] == 3.0


def test_simple_st1_threshold_closes_at_its_own_3pct_target():
    cfg = _st1_cfg(hybrid_sl_cap_pct=None)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # 3% of Rs 1,00,000 = Rs 3,000 - a smaller move than st2_threshold's
    # 5% target needs, so this ce_ltp would only just clear st1's target.
    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=105.0))

    assert "CLOSED (Target)" in action
    assert trade["Net PnL"] >= 3000


def test_simple_st1_threshold_closes_at_its_own_3pct_plain_stop_loss():
    cfg = _st1_cfg(hybrid_sl_cap_pct=None)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, _data_point(ce_ltp=95.0))

    assert "CLOSED (Stop Loss)" in action
    assert trade["Net PnL"] <= -3000


# --- oi_footprint_decide_fn ---

def _oi_cfg(**overrides):
    cfg = make_oi_footprint_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    cfg.update(overrides)
    return cfg


def _oi_data_point(**overrides):
    point = {
        "timestamp": "2026-08-18 09:20:00",
        "spot": 24500.0,
        "oi_signal": "CE",
        "ce_symbol": "NSE:NIFTY2681824500CE", "ce_ltp": 60.0, "ce_bid": 59.9, "ce_ask": 60.1,
        "pe_symbol": "NSE:NIFTY2681824500PE", "pe_ltp": 55.0, "pe_bid": 54.9, "pe_ask": 55.1,
        "past_squareoff": False,
    }
    point.update(overrides)
    return point


def test_oi_footprint_opens_ce_on_ce_signal():
    action, position, trade = oi_footprint_decide_fn(_oi_cfg(), None, _oi_data_point(oi_signal="CE"))

    assert "OPENED CE" in action
    assert position["Option Type"] == "CE"
    assert position["Entry Premium"] == 60.0


def test_oi_footprint_opens_pe_on_pe_signal():
    action, position, trade = oi_footprint_decide_fn(_oi_cfg(), None, _oi_data_point(oi_signal="PE"))

    assert "OPENED PE" in action
    assert position["Option Type"] == "PE"
    assert position["Entry Premium"] == 55.0


def test_oi_footprint_skips_open_when_no_signal():
    action, position, trade = oi_footprint_decide_fn(_oi_cfg(), None, _oi_data_point(oi_signal=None))

    assert "SKIPPED" in action
    assert position is None


def test_oi_footprint_closes_at_fixed_rupee_target():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0))

    # lots = 100000 // (60*75) = 22; Target Rs 1,500 needs a real jump.
    action, new_position, trade = oi_footprint_decide_fn(cfg, position, _oi_data_point(ce_ltp=62.0))

    assert "CLOSED (Target)" in action
    assert trade["Net PnL"] >= 1500


def test_oi_footprint_closes_at_fixed_rupee_stop_loss():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0))

    action, new_position, trade = oi_footprint_decide_fn(cfg, position, _oi_data_point(ce_ltp=58.0))

    assert "CLOSED (Stop Loss)" in action
    assert trade["Net PnL"] <= -1500


def test_oi_footprint_skips_open_when_before_market_open():
    action, position, trade = oi_footprint_decide_fn(
        _oi_cfg(), None, _oi_data_point(oi_signal="CE", before_market_open=True)
    )

    assert "SKIPPED (before market open)" in action
    assert position is None


def test_oi_footprint_skips_open_when_near_circuit_band():
    action, position, trade = oi_footprint_decide_fn(
        _oi_cfg(), None, _oi_data_point(oi_signal="CE", previous_close=22270.0)
    )

    assert "SKIPPED" in action
    assert position is None


def test_oi_footprint_closes_at_circuit_risk():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0))

    # ce_ltp=60.5 is nowhere near the fixed Rs 1,500 Target/Stop-Loss.
    action, new_position, trade = oi_footprint_decide_fn(
        cfg, position, _oi_data_point(ce_ltp=60.5, previous_close=22270.0)
    )

    assert "CLOSED (Circuit Risk)" in action
    assert trade["Exit Reason"] == "Circuit Risk"


def test_oi_footprint_hybrid_sl_cap_overrides_fixed_rupee_sl():
    cfg = _oi_cfg(hybrid_sl_cap_pct=2.0)
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0))

    # Hybrid cap here = min(2% of 1,00,000, 2% of deployed) = Rs 2,000,
    # LOOSER than the fixed Rs 1,500 - a loss between the two should
    # still be held under the hybrid rule but would have closed under
    # the original fixed rule.
    action, new_position, trade = oi_footprint_decide_fn(cfg, position, _oi_data_point(ce_ltp=59.1))

    assert "HELD" in action


def test_oi_footprint_run_backtest_full_sequence():
    cfg = _oi_cfg()
    data_points = [
        _oi_data_point(timestamp="t1", oi_signal="CE", ce_ltp=60.0),
        _oi_data_point(timestamp="t2", ce_ltp=61.0),
        _oi_data_point(timestamp="t3", ce_ltp=62.0),
    ]

    portfolio, actions = run_backtest(oi_footprint_decide_fn, cfg, data_points, initial_capital=100000)

    assert "OPENED" in actions[0]
    assert len(portfolio["Closed Trades"]) == 1
    assert portfolio["Cash"] > 100000
