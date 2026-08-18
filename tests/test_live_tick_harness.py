import datetime

import pandas as pd

from indicators.rsi import calculate_rsi
from strategy.event_driven_engine import st2_threshold_decide_fn, make_st2_threshold_event_cfg
from strategy.live_tick_harness import CandleAggregator, LiveTickRunner, MIN_CANDLES_FOR_RSI


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
        decide_fn=st2_threshold_decide_fn,
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
