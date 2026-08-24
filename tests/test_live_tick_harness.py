import datetime

import pandas as pd

from indicators.rsi import calculate_rsi
from strategy.event_driven_engine import (
    rsi_momentum_decide_fn, make_st2_threshold_event_cfg,
    oi_footprint_decide_fn, make_oi_footprint_event_cfg,
)
from strategy.live_tick_harness import (
    CandleAggregator, LiveTickRunner, MIN_CANDLES_FOR_RSI,
    OIBuildupTracker, OIFootprintTickRunner, handle_symbol_update_message,
    _maybe_top_up_capital, _today_consecutive_losses,
)


def _ts(minute, second=0, hour=9):
    return datetime.datetime(2026, 8, 18, hour, minute, second)


def test_first_tick_opens_a_bucket_but_writes_nothing_yet():
    agg = CandleAggregator()

    agg.on_tick(_ts(17), 100.0)

    assert agg.candles.empty  # bucket not closed yet - nothing appended


def test_ticks_within_the_same_bucket_update_high_low_close():
    agg = CandleAggregator()

    agg.on_tick(_ts(15, 0), 100.0)
    agg.on_tick(_ts(16, 30), 105.0)
    agg.on_tick(_ts(17, 45), 98.0)
    agg.on_tick(_ts(19, 0), 102.0)   # same 15-19 bucket (5-min, floored to 15)
    agg.on_tick(_ts(20, 0), 110.0)   # next bucket (20-24) - closes the first

    assert len(agg.candles) == 1
    closed = agg.candles.iloc[0]
    assert closed["Open"] == 100.0
    assert closed["High"] == 105.0
    assert closed["Low"] == 98.0
    assert closed["Close"] == 102.0


def test_current_rsi_none_before_minimum_candles():
    agg = CandleAggregator()

    # Only a couple of closed candles - nowhere near MIN_CANDLES_FOR_RSI.
    for m in (0, 5, 10):
        agg.on_tick(_ts(m), 100.0 + m)
    agg.on_tick(_ts(15), 999.0)  # closes the last of those few buckets

    assert agg.current_rsi() is None


def test_current_rsi_matches_calculate_rsi_on_an_equivalent_dataframe():
    agg = CandleAggregator()

    prices = [100 + i for i in range(MIN_CANDLES_FOR_RSI + 2)]  # steady uptrend
    minute = 0
    for p in prices:
        agg.on_tick(_ts(minute % 60, hour=9 + minute // 60), p)
        minute += 5

    # One more tick to close the final bucket in that loop.
    agg.on_tick(_ts(minute % 60, hour=9 + minute // 60), prices[-1] + 1)

    live_rsi = agg.current_rsi()
    direct_rsi = calculate_rsi(agg.candles).iloc[-1]

    assert live_rsi is not None
    assert round(live_rsi, 6) == round(float(direct_rsi), 6)


def _seeded_candles(n, start_price=100.0):
    """n closed candles, mildly uptrending, ending well before `now`."""
    rows = []
    idx = []
    price = start_price
    base = datetime.datetime(2026, 8, 18, 9, 0)
    for i in range(n):
        price += 1
        rows.append({"Open": price, "High": price + 0.5, "Low": price - 0.5, "Close": price})
        idx.append(base + datetime.timedelta(minutes=5 * i))
    return pd.DataFrame(rows, index=idx)


class _SpyBackend:
    """Records on_open/on_close calls - isolates the execution_backend
    wiring in live_tick_harness.py from any real broker/paper logic."""

    def __init__(self):
        self.opens = []
        self.closes = []

    def on_open(self, cfg, position):
        self.opens.append((cfg, position))

    def on_close(self, cfg, trade_record):
        self.closes.append((cfg, trade_record))


def _runner(hybrid_sl_cap_pct=2.0, spread_pct=None, execution_backend=None, previous_close=None,
            daily_profit_lock=False, daily_loss_lock=False, max_consecutive_losses=2, closed_trades=None):
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000,
                                        hybrid_sl_cap_pct=hybrid_sl_cap_pct, spread_pct=spread_pct,
                                        daily_profit_lock=daily_profit_lock,
                                        daily_loss_lock=daily_loss_lock,
                                        max_consecutive_losses=max_consecutive_losses)
    portfolio = {"Cash": 100000, "Position": None, "Closed Trades": closed_trades or []}
    seeded = _seeded_candles(MIN_CANDLES_FOR_RSI + 5)  # RSI ready from tick 1

    return LiveTickRunner(
        decide_fn=rsi_momentum_decide_fn,
        cfg=cfg,
        portfolio=portfolio,
        underlying_symbol="NSE:NIFTY50-INDEX",
        ce_symbol="NSE:NIFTY2681824500CE",
        pe_symbol="NSE:NIFTY2681824500PE",
        squareoff_time=(15, 15),
        initial_candles=seeded,
        execution_backend=execution_backend,
        previous_close=previous_close,
    )


def test_tick_for_untracked_symbol_is_ignored():
    runner = _runner()

    result = runner.on_tick("NSE:SOMEOTHER-EQ", _ts(20), 500.0)

    assert result is None
    assert runner.portfolio["Position"] is None


def test_ce_tick_before_any_underlying_tick_is_held_back():
    runner = _runner()

    result = runner.on_tick(runner.ce_symbol, _ts(20), 100.0)

    assert result is None  # no spot/RSI context yet, nothing to decide on


def test_underlying_tick_with_seeded_rsi_can_open_a_position():
    runner = _runner()

    # Seeded candles are a steady uptrend -> RSI comfortably >= 50 -> CE.
    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert action is not None
    assert "OPENED CE" in action
    assert runner.portfolio["Position"] is not None
    assert runner.portfolio["Position"]["Option Type"] == "CE"


def test_full_open_then_target_close_sequence_via_ticks():
    runner = _runner()

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE

    action = runner.on_tick(runner.ce_symbol, _ts(21), 115.0)  # jumps to Target

    assert "CLOSED (Target)" in action
    assert runner.portfolio["Position"] is None
    assert len(runner.portfolio["Closed Trades"]) == 1
    assert runner.portfolio["Cash"] > 100000


def test_open_notifies_execution_backend_on_open():
    backend = _SpyBackend()
    runner = _runner(execution_backend=backend)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE

    assert len(backend.opens) == 1
    cfg, position = backend.opens[0]
    assert position["Option Type"] == "CE"
    assert len(backend.closes) == 0


def test_target_close_notifies_execution_backend_on_close():
    backend = _SpyBackend()
    runner = _runner(execution_backend=backend)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE
    runner.on_tick(runner.ce_symbol, _ts(21), 115.0)  # jumps to Target

    assert len(backend.closes) == 1
    cfg, trade_record = backend.closes[0]
    assert trade_record["Exit Reason"] == "Target"


def test_today_consecutive_losses_pure_function_counts_backward_from_latest():
    # Direct unit test of the module-level function itself (moved out
    # of LiveTickRunner 24-Aug-2026 so OIFootprintTickRunner could
    # share it too) - the behavior-level tests above/below only cover
    # it indirectly through a runner.
    trades = [
        {"Entry Time": "2026-08-18 09:00:00", "Exit Time": "2026-08-18 09:05:00", "Net PnL": 100},
        {"Entry Time": "2026-08-18 09:06:00", "Exit Time": "2026-08-18 09:10:00", "Net PnL": -50},
        {"Entry Time": "2026-08-18 09:11:00", "Exit Time": "2026-08-18 09:15:00", "Net PnL": -75},
    ]
    portfolio = {"Closed Trades": trades}

    assert _today_consecutive_losses(portfolio, _ts(20)) == 2


def test_top_up_triggers_at_40pct_drawdown():
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    portfolio = {"Cash": 60000, "Position": None, "Closed Trades": []}  # exactly 40% down

    _maybe_top_up_capital(cfg, portfolio, _ts(20))

    assert portfolio["Cash"] == 100000
    assert len(portfolio["Capital Top-ups"]) == 1
    assert portfolio["Capital Top-ups"][0]["Cash Before"] == 60000
    assert portfolio["Capital Top-ups"][0]["Topped Up To"] == 100000
    assert portfolio["Capital Top-ups"][0]["Time"] == "2026-08-18 09:20:00"


def test_top_up_does_not_trigger_above_40pct_drawdown():
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    portfolio = {"Cash": 60001, "Position": None, "Closed Trades": []}  # just under 40% down

    _maybe_top_up_capital(cfg, portfolio, _ts(20))

    assert portfolio["Cash"] == 60001
    assert "Capital Top-ups" not in portfolio


def test_top_up_never_triggers_mid_position():
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    portfolio = {"Cash": 0, "Position": {"Option Type": "CE"}, "Closed Trades": []}

    _maybe_top_up_capital(cfg, portfolio, _ts(20))

    assert portfolio["Cash"] == 0
    assert "Capital Top-ups" not in portfolio


def test_top_up_records_multiple_events_across_repeated_drawdowns():
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    portfolio = {"Cash": 50000, "Position": None, "Closed Trades": []}

    _maybe_top_up_capital(cfg, portfolio, _ts(20))
    portfolio["Cash"] = 45000  # a later, separate drawdown
    _maybe_top_up_capital(cfg, portfolio, _ts(45))

    assert len(portfolio["Capital Top-ups"]) == 2
    assert portfolio["Cash"] == 100000


def test_top_up_flows_through_a_real_liveTickRunner_on_tick():
    runner = _runner()
    runner.portfolio["Cash"] = 55000  # 45% down, no open position

    # An underlying tick alone reaches decide_fn/top-up (sets spot, then
    # proceeds past the "no context yet" guard in the same call).
    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)

    assert runner.portfolio["Cash"] == 100000
    assert len(runner.portfolio.get("Capital Top-ups", [])) == 1


def test_held_tick_does_not_notify_execution_backend():
    backend = _SpyBackend()
    runner = _runner(execution_backend=backend)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE
    runner.on_tick(runner.ce_symbol, _ts(20, 30), 101.0)  # neither Target nor SL - HELD

    assert len(backend.opens) == 1  # only the original open
    assert len(backend.closes) == 0


def test_previous_close_flows_through_to_a_circuit_risk_close():
    # previous_close 24500 -> spot 24500 (the entry tick) sits centered
    # between both 10% bands (22050/26950), ~10% from either - nowhere
    # near, so entry proceeds normally. A LATER underlying tick moving
    # spot to 26900 lands ~0.2% from the upper band - inside the
    # default 2% gate - forcing the close. Confirms LiveTickRunner's
    # own constructor param actually reaches decide_fn's data_point on
    # a real tick sequence, not just that event_driven_engine.py's gate
    # works in isolation (already covered by tests/test_event_driven_
    # engine.py).
    runner = _runner(previous_close=24500.0)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE, spot far from any band
    action = runner.on_tick(runner.underlying_symbol, _ts(20, 30), 26900.0)  # spot now near upper band

    assert "CLOSED (Circuit Risk)" in action


def test_runner_without_a_backend_defaults_to_a_working_no_op():
    # No execution_backend passed - must not raise (PaperExecutionBackend default).
    runner = _runner()

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "OPENED CE" in action


def test_past_squareoff_is_computed_from_tick_timestamp():
    runner = _runner()

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE

    action = runner.on_tick(runner.ce_symbol, _ts(20, hour=15, second=30), 100.5)

    assert "CLOSED (Square-Off)" in action


def test_before_market_open_is_computed_from_tick_timestamp():
    # Real bug caught live (21-Aug-2026): a WebSocket connection can
    # deliver a real tick before 09:15 IST (Fyers replaying its last
    # pre-market snapshot on connect) - must not open a position on it.
    runner = _runner()

    runner.on_tick(runner.underlying_symbol, _ts(0, hour=9), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(0, second=1, hour=9), 100.0)

    assert "SKIPPED (before market open)" in action


def test_today_realized_pnl_is_computed_from_closed_trades_and_gates_new_entries():
    # Real feature added 21-Aug-2026 at the user's own request, after
    # today's whipsaw-loss session - a Rs 2,000 daily-profit-lock
    # variant. today's Closed Trades already sum to Rs 2,500 (past the
    # Rs 2,000 lock) - a new entry attempt must be skipped.
    todays_trade = {"Entry Time": "2026-08-18 09:00:00", "Exit Time": "2026-08-18 09:05:00", "Net PnL": 2500}
    runner = _runner(daily_profit_lock=True, closed_trades=[todays_trade])

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "SKIPPED (today's profit lock reached)" in action


def test_today_realized_pnl_ignores_a_previous_days_trade():
    yesterdays_trade = {"Entry Time": "2026-08-17 09:00:00", "Exit Time": "2026-08-17 09:05:00", "Net PnL": 9999}
    runner = _runner(daily_profit_lock=True, closed_trades=[yesterdays_trade])

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "OPENED CE" in action


def test_today_consecutive_losses_gates_new_entries_via_daily_loss_lock():
    # Added 21-Aug-2026, ported from fyers_options_engine.py's own
    # proven daily_loss_lock, after st2_threshold/simple_st1_threshold
    # whipsawed for real today (81/106 trades, 71-79% Stop-Loss).
    todays_losses = [
        {"Entry Time": "2026-08-18 09:00:00", "Exit Time": "2026-08-18 09:05:00", "Net PnL": -500},
        {"Entry Time": "2026-08-18 09:06:00", "Exit Time": "2026-08-18 09:10:00", "Net PnL": -300},
    ]
    runner = _runner(daily_loss_lock=True, max_consecutive_losses=2, closed_trades=todays_losses)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "SKIPPED (today already has 2+ consecutive losses" in action


def test_today_consecutive_losses_resets_after_a_win():
    trades = [
        {"Entry Time": "2026-08-18 09:00:00", "Exit Time": "2026-08-18 09:05:00", "Net PnL": -500},
        {"Entry Time": "2026-08-18 09:06:00", "Exit Time": "2026-08-18 09:10:00", "Net PnL": -300},
        {"Entry Time": "2026-08-18 09:11:00", "Exit Time": "2026-08-18 09:15:00", "Net PnL": 400},
    ]
    runner = _runner(daily_loss_lock=True, max_consecutive_losses=2, closed_trades=trades)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "OPENED CE" in action


def test_today_consecutive_losses_ignores_a_previous_days_streak():
    yesterdays_losses = [
        {"Entry Time": "2026-08-17 09:00:00", "Exit Time": "2026-08-17 09:05:00", "Net PnL": -500},
        {"Entry Time": "2026-08-17 09:06:00", "Exit Time": "2026-08-17 09:10:00", "Net PnL": -300},
    ]
    runner = _runner(daily_loss_lock=True, max_consecutive_losses=2, closed_trades=yesterdays_losses)

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "OPENED CE" in action


# --- OIBuildupTracker / OIFootprintTickRunner ---

def test_oi_tracker_no_signal_on_first_snapshot():
    tracker = OIBuildupTracker()

    signal = tracker.on_oi_snapshot(spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)

    assert signal is None  # nothing to compare against yet


def test_oi_tracker_classifies_long_buildup_as_ce():
    tracker = OIBuildupTracker()
    tracker.on_oi_snapshot(spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)

    # Price up + OI up (>= MIN_OI_CHANGE_PCT) -> Long Buildup -> CE.
    signal = tracker.on_oi_snapshot(spot=24520, strike=24500, ce_oi=115000, pe_oi=100000)

    assert signal == "CE"
    assert tracker.latest_signal == "CE"


def test_oi_tracker_no_signal_on_strike_change():
    tracker = OIBuildupTracker()
    tracker.on_oi_snapshot(spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)

    signal = tracker.on_oi_snapshot(spot=24560, strike=24550, ce_oi=115000, pe_oi=100000)

    assert signal is None


def _oi_runner(execution_backend=None, previous_close=None, daily_loss_lock=False,
                max_consecutive_losses=2, closed_trades=None):
    cfg = make_oi_footprint_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000,
                                       daily_loss_lock=daily_loss_lock,
                                       max_consecutive_losses=max_consecutive_losses)
    portfolio = {"Cash": 100000, "Position": None, "Closed Trades": closed_trades or []}

    return OIFootprintTickRunner(
        decide_fn=oi_footprint_decide_fn,
        cfg=cfg,
        portfolio=portfolio,
        ce_symbol="NSE:NIFTY2681824500CE",
        pe_symbol="NSE:NIFTY2681824500PE",
        squareoff_time=(15, 15),
        execution_backend=execution_backend,
        previous_close=previous_close,
    )


def test_oi_runner_on_oi_snapshot_before_any_price_tick_holds_back():
    runner = _oi_runner()

    action = runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)

    assert action is not None  # spot is now known, decide_fn runs...
    assert "SKIPPED" in action  # ...but no signal yet (first snapshot)


def test_oi_runner_today_consecutive_losses_gates_new_entries_via_daily_loss_lock():
    # Added 24-Aug-2026, after a real incident: oi_footprint_banknifty
    # whipsawed 141 real trades (69 losses, -Rs 23,952) with no breaker
    # at all - OIFootprintTickRunner had no _today_consecutive_losses
    # equivalent (LiveTickRunner-only until this fix moved it to
    # module level and wired it into both runners).
    todays_losses = [
        {"Entry Time": "2026-08-18 09:00:00", "Exit Time": "2026-08-18 09:05:00", "Net PnL": -500},
        {"Entry Time": "2026-08-18 09:06:00", "Exit Time": "2026-08-18 09:10:00", "Net PnL": -300},
    ]
    runner = _oi_runner(daily_loss_lock=True, max_consecutive_losses=2, closed_trades=todays_losses)

    runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)
    action = runner.on_oi_snapshot(_ts(25), spot=24520, strike=24500, ce_oi=115000, pe_oi=100000)

    assert "SKIPPED (today already has 2+ consecutive losses" in action


def test_oi_runner_full_signal_to_open_to_target_sequence():
    runner = _oi_runner()

    runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)
    action = runner.on_oi_snapshot(_ts(25), spot=24520, strike=24500, ce_oi=115000, pe_oi=100000)

    # No CE price known yet - decide_fn should skip the open (not crash
    # on a None premium), not fabricate a trade at whatever's cached.
    assert "SKIPPED" in action

    action = runner.on_tick(runner.ce_symbol, _ts(25, 30), 60.0)
    assert "OPENED CE" in action

    action = runner.on_tick(runner.ce_symbol, _ts(26), 62.0)
    assert "CLOSED (Target)" in action
    assert runner.portfolio["Cash"] > 100000


def test_oi_runner_previous_close_flows_through_to_a_circuit_risk_close():
    # See test_previous_close_flows_through_to_a_circuit_risk_close's
    # comment above for the same previous_close=24500 (spot centered,
    # far from either band) / spot=26900 (near the upper band) reasoning.
    runner = _oi_runner(previous_close=24500.0)

    runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)
    runner.on_oi_snapshot(_ts(25), spot=24520, strike=24500, ce_oi=115000, pe_oi=100000)
    runner.on_tick(runner.ce_symbol, _ts(25, 30), 60.0)  # opens CE

    action = runner.on_oi_snapshot(_ts(26), spot=26900, strike=24500, ce_oi=115000, pe_oi=100000)

    assert "CLOSED (Circuit Risk)" in action


def test_oi_runner_notifies_execution_backend_on_open_and_close():
    backend = _SpyBackend()
    runner = _oi_runner(execution_backend=backend)

    runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)
    runner.on_oi_snapshot(_ts(25), spot=24520, strike=24500, ce_oi=115000, pe_oi=100000)
    runner.on_tick(runner.ce_symbol, _ts(25, 30), 60.0)  # opens CE

    assert len(backend.opens) == 1
    assert backend.opens[0][1]["Option Type"] == "CE"

    runner.on_tick(runner.ce_symbol, _ts(26), 62.0)  # Target close

    assert len(backend.closes) == 1
    assert backend.closes[0][1]["Exit Reason"] == "Target"


# --- handle_symbol_update_message() - the one piece of connect_and_run()
# that IS testable without a live connection (see its own docstring).
# Real message shape confirmed via 17-Aug's WebSocket research, not
# guessed - matches an actual Fyers SymbolUpdate example payload.

def _real_shaped_message(**overrides):
    message = {
        "ltp": 60.0, "bid_price": 59.9, "ask_price": 60.1,
        "vol_traded_today": 1632306, "bid_size": 59, "ask_size": 16,
        "last_traded_time": 1755500000, "exch_feed_time": 1755500001,
        "last_traded_qty": 9, "tot_buy_qty": 69427, "tot_sell_qty": 234706,
        "avg_trade_price": 60.0, "low_price": 58.0, "high_price": 62.0,
        "lower_ckt": 0, "upper_ckt": 0, "open_price": 59.0, "prev_close_price": 58.5,
        "type": "sf", "symbol": "NSE:NIFTY2681824500CE", "ch": 1.5, "chp": 2.5,
    }
    message.update(overrides)
    return message


class _SpyRunner:
    """Minimal fake, not a real LiveTickRunner - isolates handle_symbol_
    update_message()'s own extraction/wiring logic from decide_fn."""

    def __init__(self):
        self.calls = []

    def on_tick(self, symbol, timestamp, ltp, bid, ask):
        self.calls.append({"symbol": symbol, "timestamp": timestamp, "ltp": ltp, "bid": bid, "ask": ask})
        return f"recorded {symbol}"


def test_handle_symbol_update_extracts_real_field_names_correctly():
    spy = _SpyRunner()

    handle_symbol_update_message(_real_shaped_message(), spy)

    assert len(spy.calls) == 1
    call = spy.calls[0]
    assert call["symbol"] == "NSE:NIFTY2681824500CE"
    assert call["ltp"] == 60.0
    assert call["bid"] == 59.9   # from bid_price, not "bid"
    assert call["ask"] == 60.1   # from ask_price, not "ask"


def test_handle_symbol_update_prefers_exch_feed_time_over_last_traded_time():
    spy = _SpyRunner()

    handle_symbol_update_message(
        _real_shaped_message(exch_feed_time=1755500999, last_traded_time=1755500000), spy
    )

    expected = datetime.datetime.fromtimestamp(
        1755500999, tz=datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    )
    assert spy.calls[0]["timestamp"] == expected


def test_handle_symbol_update_falls_back_to_last_traded_time_when_exch_feed_time_missing():
    spy = _SpyRunner()
    message = _real_shaped_message()
    del message["exch_feed_time"]

    handle_symbol_update_message(message, spy)

    expected = datetime.datetime.fromtimestamp(
        message["last_traded_time"], tz=datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    )
    assert spy.calls[0]["timestamp"] == expected


def test_handle_symbol_update_end_to_end_through_a_real_liveTickRunner():
    # Proves the full real-shaped-message -> handle_symbol_update_
    # message -> LiveTickRunner.on_tick -> decide_fn pipeline works
    # together, not just each piece in isolation.
    runner = _runner()

    handle_symbol_update_message(
        _real_shaped_message(symbol=runner.underlying_symbol, ltp=24500.0), runner
    )
    action = handle_symbol_update_message(
        _real_shaped_message(symbol=runner.ce_symbol, ltp=100.0), runner
    )

    # _runner()'s seeded candles are a steady uptrend (same fixture the
    # earlier RSI tests rely on) -> RSI comfortably >= 50 -> CE, same
    # deterministic outcome as test_underlying_tick_with_seeded_rsi_
    # can_open_a_position above, just reached via the real message
    # shape this time instead of calling on_tick() directly.
    assert "OPENED CE" in action
    assert runner.portfolio["Position"]["Option Type"] == "CE"
