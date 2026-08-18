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


def _runner(hybrid_sl_cap_pct=2.0, spread_pct=None):
    cfg = make_st2_threshold_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000,
                                        hybrid_sl_cap_pct=hybrid_sl_cap_pct, spread_pct=spread_pct)
    portfolio = {"Cash": 100000, "Position": None, "Closed Trades": []}
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


def test_past_squareoff_is_computed_from_tick_timestamp():
    runner = _runner()

    runner.on_tick(runner.underlying_symbol, _ts(20), 24500.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE

    action = runner.on_tick(runner.ce_symbol, _ts(20, hour=15, second=30), 100.5)

    assert "CLOSED (Square-Off)" in action


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


def _oi_runner():
    cfg = make_oi_footprint_event_cfg(index="NIFTY", lot_size=75, initial_capital=100000)
    portfolio = {"Cash": 100000, "Position": None, "Closed Trades": []}

    return OIFootprintTickRunner(
        decide_fn=oi_footprint_decide_fn,
        cfg=cfg,
        portfolio=portfolio,
        ce_symbol="NSE:NIFTY2681824500CE",
        pe_symbol="NSE:NIFTY2681824500PE",
        squareoff_time=(15, 15),
    )


def test_oi_runner_on_oi_snapshot_before_any_price_tick_holds_back():
    runner = _oi_runner()

    action = runner.on_oi_snapshot(_ts(20), spot=24500, strike=24500, ce_oi=100000, pe_oi=90000)

    assert action is not None  # spot is now known, decide_fn runs...
    assert "SKIPPED" in action  # ...but no signal yet (first snapshot)


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
