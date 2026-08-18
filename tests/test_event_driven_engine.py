from strategy.backtest_live_engine import run_backtest, run_live_check
from strategy.event_driven_engine import st2_threshold_decide_fn, make_st2_threshold_event_cfg


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
    action, position, trade = st2_threshold_decide_fn(_cfg(), None, _data_point(rsi=55.0))

    assert "OPENED CE" in action
    assert position["Option Type"] == "CE"
    assert position["Entry Premium"] == 100.0
    assert trade is None


def test_opens_pe_when_rsi_below_50():
    action, position, trade = st2_threshold_decide_fn(_cfg(), None, _data_point(rsi=45.0))

    assert "OPENED PE" in action
    assert position["Option Type"] == "PE"
    assert position["Entry Premium"] == 90.0


def test_skips_open_when_rsi_not_ready():
    action, position, trade = st2_threshold_decide_fn(_cfg(), None, _data_point(rsi=None))

    assert "SKIPPED" in action
    assert position is None
    assert trade is None


def test_skips_open_when_past_squareoff():
    action, position, trade = st2_threshold_decide_fn(_cfg(), None, _data_point(past_squareoff=True))

    assert "SKIPPED" in action
    assert position is None


def test_skips_open_when_capital_insufficient_for_one_lot():
    # 75 lot_size x 100 premium = Rs 7,500/lot - Rs 5,000 capital can't buy even 1
    action, position, trade = st2_threshold_decide_fn(_cfg(initial_capital=5000), None, _data_point(rsi=55.0))

    assert "SKIPPED" in action
    assert position is None


def test_holds_when_neither_target_nor_sl_hit():
    cfg = _cfg()
    _, position, _ = st2_threshold_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = st2_threshold_decide_fn(cfg, position, _data_point(ce_ltp=101.0))

    assert "HELD" in action
    assert new_position is not None
    assert trade is None


def test_closes_at_target():
    cfg = _cfg()
    _, position, _ = st2_threshold_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Target is 5% of initial_capital (Rs 5,000); need ce_ltp high enough to
    # clear both the 5% target AND real transaction costs.
    action, new_position, trade = st2_threshold_decide_fn(cfg, position, _data_point(ce_ltp=115.0))

    assert "CLOSED (Target)" in action
    assert new_position is None
    assert trade["Exit Reason"] == "Target"
    assert trade["Net PnL"] > 0


def test_closes_at_hybrid_stop_loss_when_set():
    cfg = _cfg(hybrid_sl_cap_pct=2.0)
    _, position, _ = st2_threshold_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Hybrid cap here is min(2% of 1,00,000, 2% of capital deployed) = Rs 2,000.
    # A big premium drop should breach it.
    action, new_position, trade = st2_threshold_decide_fn(cfg, position, _data_point(ce_ltp=70.0))

    assert "CLOSED (Stop Loss)" in action
    assert trade["Net PnL"] < 0


def test_closes_at_plain_stop_loss_when_hybrid_not_set():
    cfg = _cfg(hybrid_sl_cap_pct=None)
    _, position, _ = st2_threshold_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    # Plain stop_loss_pct = 2% of initial_capital, same Rs 2,000 threshold here.
    action, new_position, trade = st2_threshold_decide_fn(cfg, position, _data_point(ce_ltp=70.0))

    assert "CLOSED (Stop Loss)" in action


def test_closes_at_squareoff_when_neither_target_nor_sl_hit():
    cfg = _cfg()
    _, position, _ = st2_threshold_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = st2_threshold_decide_fn(
        cfg, position, _data_point(ce_ltp=100.5, past_squareoff=True)
    )

    assert "CLOSED (Square-Off)" in action
    assert trade["Exit Reason"] == "Square-Off"


def test_spread_pct_makes_the_same_trade_slightly_worse():
    cfg_no_spread = _cfg(spread_pct=None)
    cfg_with_spread = _cfg(spread_pct=0.26)

    _, pos_a, _ = st2_threshold_decide_fn(cfg_no_spread, None, _data_point(rsi=55.0, ce_ltp=100.0))
    _, pos_b, _ = st2_threshold_decide_fn(cfg_with_spread, None, _data_point(rsi=55.0, ce_ltp=100.0))

    _, _, trade_no_spread = st2_threshold_decide_fn(cfg_no_spread, pos_a, _data_point(ce_ltp=115.0))
    _, _, trade_with_spread = st2_threshold_decide_fn(cfg_with_spread, pos_b, _data_point(ce_ltp=115.0))

    assert trade_with_spread["Net PnL"] < trade_no_spread["Net PnL"]


def test_run_backtest_replays_a_full_open_then_close_sequence():
    cfg = _cfg()
    data_points = [
        _data_point(timestamp="t1", rsi=55.0, ce_ltp=100.0),   # opens CE
        _data_point(timestamp="t2", ce_ltp=105.0),             # holds
        _data_point(timestamp="t3", ce_ltp=115.0),             # closes at Target
    ]

    portfolio, actions = run_backtest(st2_threshold_decide_fn, cfg, data_points, initial_capital=100000)

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

    batch_portfolio, _ = run_backtest(st2_threshold_decide_fn, cfg, data_points, initial_capital=100000)

    live_portfolio = {"Cash": 100000, "Position": None, "Closed Trades": []}
    for point in data_points:
        _, live_portfolio = run_live_check(st2_threshold_decide_fn, cfg, live_portfolio, point)

    assert live_portfolio == batch_portfolio
