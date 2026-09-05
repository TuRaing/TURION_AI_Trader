from strategy.backtest_live_engine import run_backtest, run_live_check
from strategy.event_driven_engine import (
    rsi_momentum_decide_fn, rsi_momentum_quote_decide_fn,
    make_st2_threshold_event_cfg, make_simple_st1_threshold_event_cfg,
    oi_footprint_decide_fn, oi_footprint_quote_decide_fn, make_oi_footprint_event_cfg,
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


def test_lots_uncapped_by_default():
    # entry_premium=1.0 -> uncapped lots would be 100000/(1*75)=1333.
    cfg = _cfg()
    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=1.0))

    assert position["Lots"] == 1333


def test_max_lots_caps_a_near_expiry_style_cheap_premium():
    # Regression test for a real bug caught live, 04-Sep-2026: a
    # near-expiry Deribit contract's collapsing premium made lots
    # balloon to 1238 (normal range 5-20), producing a single trade
    # worth +$1,968,854.76 against a $10,000 book. Same cheap
    # entry_premium=1.0 as the uncapped test above, but with max_lots
    # set - lots must clamp to the cap, not the raw capital/premium
    # division.
    cfg = _cfg(max_lots=50)
    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=1.0))

    assert position["Lots"] == 50


def test_max_lots_does_not_raise_lots_that_are_already_below_the_cap():
    cfg = _cfg(max_lots=50)
    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    assert position["Lots"] == 13  # unaffected - already under the 50 cap


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


def test_skips_open_when_capital_depleted():
    cfg = _cfg(stop_at_zero_capital=True)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(current_cash=-500.0))

    assert "SKIPPED (capital depleted - book stopped)" in action
    assert position is None


def test_stop_at_zero_capital_does_not_skip_while_cash_positive():
    cfg = _cfg(stop_at_zero_capital=True)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(current_cash=1.0))

    assert "OPENED" in action


def test_stop_at_zero_capital_ignored_when_flag_is_off():
    # Defaults to False (make_st2_threshold_event_cfg) - a negative
    # current_cash must not matter unless explicitly turned on.
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(current_cash=-999999.0))

    assert "OPENED" in action


def test_stop_at_zero_capital_does_not_block_managing_an_existing_position():
    cfg = _cfg(stop_at_zero_capital=True)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0, current_cash=1000.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=101.0, current_cash=-500.0)
    )

    assert "HELD" in action
    assert new_position is not None


def test_ce_blocked_when_spot_below_trend_ema():
    cfg = _cfg(require_trend_confirmation=True)

    action, position, trade = rsi_momentum_decide_fn(
        cfg, None, _data_point(rsi=55.0, spot=24500.0, spot_ema=24600.0)
    )

    assert "SKIPPED (CE blocked - spot below trend EMA)" in action
    assert position is None


def test_pe_blocked_when_spot_above_trend_ema():
    cfg = _cfg(require_trend_confirmation=True)

    action, position, trade = rsi_momentum_decide_fn(
        cfg, None, _data_point(rsi=45.0, spot=24500.0, spot_ema=24400.0)
    )

    assert "SKIPPED (PE blocked - spot above trend EMA)" in action
    assert position is None


def test_ce_allowed_when_spot_above_trend_ema():
    cfg = _cfg(require_trend_confirmation=True)

    action, position, trade = rsi_momentum_decide_fn(
        cfg, None, _data_point(rsi=55.0, spot=24600.0, spot_ema=24500.0)
    )

    assert "OPENED CE" in action


def test_trend_confirmation_skips_when_ema_not_ready():
    cfg = _cfg(require_trend_confirmation=True)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, spot_ema=None))

    assert "SKIPPED (trend EMA not ready yet)" in action


def test_trend_confirmation_ignored_when_flag_is_off():
    # Defaults to False - a spot below its own EMA must not block CE
    # unless explicitly turned on.
    action, position, trade = rsi_momentum_decide_fn(
        _cfg(), None, _data_point(rsi=55.0, spot=24500.0, spot_ema=24600.0)
    )

    assert "OPENED CE" in action


def test_skips_open_when_daily_profit_lock_reached():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_pct=2.0)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=2500))

    assert "SKIPPED (today's profit lock reached)" in action
    assert position is None


def test_daily_profit_lock_does_not_skip_below_threshold():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_pct=2.0)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=1500))

    assert "OPENED" in action


def test_daily_profit_lock_threshold_scales_with_initial_capital():
    # Rs 2,000 was only ever 2% of Rs 100,000 by coincidence - confirm
    # the lock is a real percentage, not a number that happens to match.
    cfg = _cfg(initial_capital=200000, daily_profit_lock=True, daily_profit_lock_pct=2.0)

    below = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=3000))[0]
    at_threshold = rsi_momentum_decide_fn(cfg, None, _data_point(today_realized_pnl=4000))[0]

    assert "OPENED" in below
    assert "SKIPPED (today's profit lock reached)" in at_threshold


def test_daily_profit_lock_ignored_when_flag_is_off():
    # daily_profit_lock defaults to False (make_st2_threshold_event_cfg)
    # - today_realized_pnl past the threshold must not matter.
    action, position, trade = rsi_momentum_decide_fn(_cfg(), None, _data_point(today_realized_pnl=999999))

    assert "OPENED" in action


def test_daily_profit_lock_does_not_block_managing_an_existing_position():
    cfg = _cfg(daily_profit_lock=True, daily_profit_lock_pct=2.0)
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


def test_records_quote_premiums_and_quote_pnl_on_full_round_trip():
    # Added 21-Aug-2026, alongside "Entry/Exit Premium (Quote)" - see
    # event_driven_engine.py's own 21-Aug-2026 notes. Confirms the new
    # fields are populated correctly AND that decision logic (which
    # reason fires, "Net PnL") is completely untouched - it must still
    # read exactly like test_closes_at_target above.
    cfg = _cfg()
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0, ce_ask=100.5))

    assert position["Entry Premium (Quote)"] == 100.5

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=115.0, ce_bid=114.0)
    )

    assert "CLOSED (Target)" in action
    assert trade["Entry Premium (Quote)"] == 100.5
    assert trade["Exit Premium (Quote)"] == 114.0
    # Buying at the ask and selling at the bid is always worse than the
    # LTP-based figure - the whole point of this field (see today's real
    # depth-slippage finding: LTP overstates realized PnL).
    assert trade["Net PnL (Quote)"] is not None
    assert trade["Net PnL (Quote)"] < trade["Net PnL"]


def test_quote_pnl_is_none_when_data_point_has_no_bid_ask():
    # Backtest replay data_points carry no bid/ask columns at all (no
    # historical depth data exists) - must not crash, and a genuinely-
    # unknown quote PnL must never be silently reported as a real 0.
    cfg = _cfg()
    entry_point = _data_point(rsi=55.0, ce_ltp=100.0)
    del entry_point["ce_bid"], entry_point["ce_ask"]

    _, position, _ = rsi_momentum_decide_fn(cfg, None, entry_point)
    assert position["Entry Premium (Quote)"] is None

    exit_point = _data_point(ce_ltp=115.0)
    del exit_point["ce_bid"], exit_point["ce_ask"]

    action, new_position, trade = rsi_momentum_decide_fn(cfg, position, exit_point)

    assert "CLOSED" in action
    assert trade["Exit Premium (Quote)"] is None
    assert trade["Net PnL (Quote)"] is None


def test_quote_decide_fn_opens_using_ask_not_ltp():
    # Added 21-Aug-2026, alongside rsi_momentum_quote_decide_fn - the 6
    # new "_lock_quote*pct" books trigger Target/Stop-Loss off real
    # bid/ask, not LTP. Confirms entry reads ce_ask, ignores ce_ltp.
    cfg = _cfg()
    action, position, trade = rsi_momentum_quote_decide_fn(
        cfg, None, _data_point(rsi=55.0, ce_ltp=100.0, ce_ask=100.5)
    )

    assert "OPENED CE" in action
    assert position["Entry Premium"] == 100.5
    # No redundant "(Quote)" field here - Entry Premium above already IS
    # the quote for this decide_fn.
    assert "Entry Premium (Quote)" not in position


def test_quote_decide_fn_closes_using_bid_not_ltp():
    cfg = _cfg()
    _, position, _ = rsi_momentum_quote_decide_fn(
        cfg, None, _data_point(rsi=55.0, ce_ltp=100.0, ce_ask=100.5)
    )

    action, new_position, trade = rsi_momentum_quote_decide_fn(
        cfg, position, _data_point(ce_ltp=100.0, ce_bid=115.0)
    )

    assert "CLOSED (Target)" in action
    assert trade["Entry Premium"] == 100.5
    assert trade["Exit Premium"] == 115.0
    assert "Net PnL (Quote)" not in trade


def test_quote_decide_fn_skips_open_when_ask_missing():
    # Never silently falls back to LTP - a missing quote just means no
    # trade, same guard style as a missing/zero LTP does today.
    cfg = _cfg()
    point = _data_point(rsi=55.0)
    point["ce_ask"] = None

    action, position, trade = rsi_momentum_quote_decide_fn(cfg, None, point)

    assert "SKIPPED (no valid premium quote)" in action
    assert position is None


def test_quote_decide_fn_holds_when_bid_missing_while_open():
    cfg = _cfg()
    _, position, _ = rsi_momentum_quote_decide_fn(
        cfg, None, _data_point(rsi=55.0, ce_ask=100.5)
    )

    point = _data_point()
    point["ce_bid"] = None

    action, new_position, trade = rsi_momentum_quote_decide_fn(cfg, position, point)

    assert "HELD (no valid premium quote)" in action
    assert new_position is position
    assert trade is None


def test_skips_open_when_daily_loss_lock_reached():
    # Added 21-Aug-2026, ported from fyers_options_engine.py's
    # MAX_CONSECUTIVE_LOSSES/daily_loss_lock (already proven there)
    # after st2_threshold/simple_st1_threshold whipsawed for real today
    # (81/106 trades, 71-79% Stop-Loss).
    cfg = _cfg(daily_loss_lock=True, max_consecutive_losses=2)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_consecutive_losses=2))

    assert "SKIPPED (today already has 2+ consecutive losses" in action
    assert position is None


def test_daily_loss_lock_does_not_skip_below_streak():
    cfg = _cfg(daily_loss_lock=True, max_consecutive_losses=2)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_consecutive_losses=1))

    assert "OPENED" in action


def test_daily_loss_lock_ignored_when_flag_is_off():
    cfg = _cfg(daily_loss_lock=False)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_consecutive_losses=5))

    assert "OPENED" in action


def test_daily_loss_lock_respects_custom_max_consecutive_losses():
    cfg = _cfg(daily_loss_lock=True, max_consecutive_losses=3)

    action, position, trade = rsi_momentum_decide_fn(cfg, None, _data_point(today_consecutive_losses=2))

    assert "OPENED" in action


def test_daily_loss_lock_does_not_block_managing_an_existing_position():
    cfg = _cfg(daily_loss_lock=True, max_consecutive_losses=2)
    _, position, _ = rsi_momentum_decide_fn(cfg, None, _data_point(rsi=55.0, ce_ltp=100.0))

    action, new_position, trade = rsi_momentum_decide_fn(
        cfg, position, _data_point(ce_ltp=101.0, today_consecutive_losses=5)
    )

    assert "HELD" in action


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


def test_oi_footprint_skips_open_when_daily_loss_lock_reached():
    # Added 24-Aug-2026, after a real incident: oi_footprint_banknifty
    # whipsawed 141 real trades (69 losses, -Rs 23,952) with no breaker
    # at all - same gate already proven on the RSI-momentum family.
    cfg = _oi_cfg(daily_loss_lock=True, max_consecutive_losses=2)

    action, position, trade = oi_footprint_decide_fn(cfg, None, _oi_data_point(today_consecutive_losses=2))

    assert "SKIPPED (today already has 2+ consecutive losses" in action
    assert position is None


def test_oi_footprint_daily_loss_lock_ignored_when_flag_is_off():
    cfg = _oi_cfg(daily_loss_lock=False)

    action, position, trade = oi_footprint_decide_fn(cfg, None, _oi_data_point(today_consecutive_losses=5))

    assert "OPENED" in action


def test_oi_footprint_daily_loss_lock_does_not_block_below_threshold():
    cfg = _oi_cfg(daily_loss_lock=True, max_consecutive_losses=2)

    action, position, trade = oi_footprint_decide_fn(cfg, None, _oi_data_point(today_consecutive_losses=1))

    assert "OPENED" in action


def test_oi_footprint_closes_at_fixed_rupee_target():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0))

    # lots = 100000 // (60*75) = 22; Target Rs 1,500 needs a real jump.
    action, new_position, trade = oi_footprint_decide_fn(cfg, position, _oi_data_point(ce_ltp=62.0))

    assert "CLOSED (Target)" in action
    assert trade["Net PnL"] >= 1500


def test_oi_footprint_records_quote_premiums_and_quote_pnl():
    # Same 21-Aug-2026 addition as rsi_momentum_decide_fn's matching
    # test above - oi_footprint_decide_fn shares the identical pattern.
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_decide_fn(cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0, ce_ask=60.3))

    assert position["Entry Premium (Quote)"] == 60.3

    action, new_position, trade = oi_footprint_decide_fn(cfg, position, _oi_data_point(ce_ltp=62.0, ce_bid=61.7))

    assert "CLOSED (Target)" in action
    assert trade["Exit Premium (Quote)"] == 61.7
    assert trade["Net PnL (Quote)"] is not None
    assert trade["Net PnL (Quote)"] < trade["Net PnL"]


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


# --- oi_footprint_quote_decide_fn ---

def test_oi_footprint_quote_decide_fn_opens_using_ask_not_ltp():
    # Added 24-Aug-2026, same shape as rsi_momentum_quote_decide_fn's
    # own 21-Aug-2026 tests - confirms entry reads ce_ask, ignores
    # ce_ltp.
    cfg = _oi_cfg()
    action, position, trade = oi_footprint_quote_decide_fn(
        cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0, ce_ask=60.3)
    )

    assert "OPENED CE" in action
    assert position["Entry Premium"] == 60.3
    assert "Entry Premium (Quote)" not in position


def test_oi_footprint_quote_decide_fn_closes_using_bid_not_ltp():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_quote_decide_fn(
        cfg, None, _oi_data_point(oi_signal="CE", ce_ltp=60.0, ce_ask=60.3)
    )

    action, new_position, trade = oi_footprint_quote_decide_fn(
        cfg, position, _oi_data_point(ce_ltp=60.0, ce_bid=82.0)
    )

    assert "CLOSED (Target)" in action
    assert trade["Entry Premium"] == 60.3
    assert trade["Exit Premium"] == 82.0
    assert "Net PnL (Quote)" not in trade


def test_oi_footprint_quote_decide_fn_skips_open_when_ask_missing():
    cfg = _oi_cfg()
    point = _oi_data_point(oi_signal="CE")
    point["ce_ask"] = None

    action, position, trade = oi_footprint_quote_decide_fn(cfg, None, point)

    assert "SKIPPED (no valid premium quote)" in action
    assert position is None


def test_oi_footprint_quote_decide_fn_holds_when_bid_missing_while_open():
    cfg = _oi_cfg()
    _, position, _ = oi_footprint_quote_decide_fn(
        cfg, None, _oi_data_point(oi_signal="CE", ce_ask=60.3)
    )

    point = _oi_data_point()
    point["ce_bid"] = None

    action, new_position, trade = oi_footprint_quote_decide_fn(cfg, position, point)

    assert "HELD (no valid premium quote)" in action
    assert new_position is position
    assert trade is None


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
