from strategy.risk_engine import calculate_atr_levels


def test_buy_levels():
    sl, target = calculate_atr_levels(100, 2, "BUY", sl_mult=1.5, target_mult=3.0)
    assert sl == 100 - 2 * 1.5   # 97
    assert target == 100 + 2 * 3.0  # 106


def test_sell_levels():
    sl, target = calculate_atr_levels(100, 2, "SELL", sl_mult=1.5, target_mult=3.0)
    assert sl == 100 + 2 * 1.5   # 103
    assert target == 100 - 2 * 3.0  # 94


def test_buy_stop_below_and_target_above_entry():
    sl, target = calculate_atr_levels(24200, 26.58, "BUY")
    assert sl < 24200 < target


def test_sell_stop_above_and_target_below_entry():
    sl, target = calculate_atr_levels(24200, 26.58, "SELL")
    assert target < 24200 < sl
