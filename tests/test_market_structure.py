from indicators.market_structure import (
    find_swing_points,
    MarketStructureTracker,
    detect_order_block,
    detect_fair_value_gap,
)


def test_find_swing_points_detects_high_and_low():
    #             0   1   2   3   4   5   6
    high = [10, 11, 15, 12, 11, 16, 13]
    low = [9, 10, 12, 8, 7, 12, 11]

    swings = find_swing_points(high, low, lookback=2)
    indices_and_types = {(s["index"], s["type"]) for s in swings}

    assert (2, "high") in indices_and_types  # 15 is the local max in [0..4]
    assert (4, "low") in indices_and_types   # 7 is the local min in [2..6]


def test_find_swing_points_confirms_only_with_enough_candles_on_both_sides():
    high = [10, 20, 10]
    low = [5, 15, 5]

    # lookback=2 needs 2 candles on each side - only 3 candles total here,
    # so nothing can be confirmed.
    assert find_swing_points(high, low, lookback=2) == []


def test_tracker_establishes_uptrend_from_higher_high_and_higher_low():
    tracker = MarketStructureTracker()

    tracker.add_swing("low", 100)
    tracker.add_swing("high", 110)
    tracker.add_swing("low", 105)  # higher low than 100

    assert tracker.trend == "up"


def test_tracker_bos_confirms_continuation_in_trend_direction():
    tracker = MarketStructureTracker()
    tracker.add_swing("low", 100)
    tracker.add_swing("high", 110)
    tracker.trend = "up"

    assert tracker.check_break(111) == "BOS"
    assert tracker.trend == "up"


def test_tracker_choch_on_break_above_last_swing_high_while_downtrend():
    tracker = MarketStructureTracker()
    tracker.add_swing("high", 110)
    tracker.add_swing("low", 100)
    tracker.trend = "down"

    result = tracker.check_break(111)

    assert result == "CHOCH"
    assert tracker.trend == "up"


def test_tracker_no_break_when_close_stays_inside_range():
    tracker = MarketStructureTracker()
    tracker.add_swing("high", 110)
    tracker.add_swing("low", 100)
    tracker.trend = "up"

    assert tracker.check_break(105) is None


def test_detect_order_block_bullish_needs_down_close_before_breakout():
    open_ = [10, 12, 9]
    close = [9, 9, 15]  # index 1: down-close candle (12 -> 9), index 2: breakout

    ob = detect_order_block(open_, close, direction="up", breakout_index=2)

    assert ob == {"index": 1, "high_ref": 12, "low_ref": 9}


def test_detect_order_block_bearish_needs_up_close_before_breakout():
    open_ = [10, 9, 15]
    close = [9, 12, 5]  # index 1: up-close candle (9 -> 12), index 2: breakout down

    ob = detect_order_block(open_, close, direction="down", breakout_index=2)

    assert ob == {"index": 1, "high_ref": 12, "low_ref": 9}


def test_detect_order_block_none_when_preceding_candle_agrees_with_breakout():
    open_ = [10, 9, 9]
    close = [9, 11, 15]  # index 1 is an UP-close candle, but breakout is "up" too

    assert detect_order_block(open_, close, direction="up", breakout_index=2) is None


def test_detect_fair_value_gap_bullish():
    high = [10, 12, 20]
    low = [8, 11, 15]  # candle 0 high (10) < candle 2 low (15) -> bullish gap

    fvg = detect_fair_value_gap(high, low, index=1)

    assert fvg == {"direction": "up", "top": 15, "bottom": 10}


def test_detect_fair_value_gap_bearish():
    high = [20, 12, 10]
    low = [15, 11, 8]  # candle 0 low (15) > candle 2 high (10) -> bearish gap

    fvg = detect_fair_value_gap(high, low, index=1)

    assert fvg == {"direction": "down", "top": 15, "bottom": 10}


def test_detect_fair_value_gap_none_when_no_imbalance():
    high = [10, 12, 11]
    low = [8, 9, 9]

    assert detect_fair_value_gap(high, low, index=1) is None


def test_detect_fair_value_gap_none_at_series_edges():
    high = [10, 12]
    low = [8, 9]

    assert detect_fair_value_gap(high, low, index=0) is None
    assert detect_fair_value_gap(high, low, index=1) is None
