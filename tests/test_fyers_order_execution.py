from strategy.fyers_order_execution import compute_stop_loss_trigger_price
from strategy.options_transaction_costs import calculate_options_round_trip_cost


def test_trigger_price_is_below_entry_for_a_long_position():
    trigger = compute_stop_loss_trigger_price(entry_premium=100, lots=20, lot_size=75, max_loss_rupees=2000)

    assert trigger is not None
    assert trigger < 100


def test_trigger_price_realizes_approximately_the_requested_loss():
    entry_premium = 100
    lots = 20
    lot_size = 75

    trigger = compute_stop_loss_trigger_price(entry_premium, lots, lot_size, max_loss_rupees=2000)

    gross = (trigger - entry_premium) * lots * lot_size
    cost = calculate_options_round_trip_cost(entry_premium, trigger, lot_size, lots)
    net_pnl = gross - cost

    assert abs(net_pnl - (-2000)) < 5


def test_larger_position_needs_a_smaller_price_move_to_hit_the_same_rupee_cap():
    small_position_trigger = compute_stop_loss_trigger_price(entry_premium=100, lots=5, lot_size=75, max_loss_rupees=2000)
    large_position_trigger = compute_stop_loss_trigger_price(entry_premium=100, lots=30, lot_size=75, max_loss_rupees=2000)

    # A bigger position hits the same rupee loss cap with a smaller drop in premium.
    assert (100 - large_position_trigger) < (100 - small_position_trigger)


def test_returns_none_when_position_too_small_to_ever_lose_the_cap():
    # A tiny 1-lot position on a cheap option can't lose Rs 2,000 even
    # if the premium falls all the way to zero.
    trigger = compute_stop_loss_trigger_price(entry_premium=2, lots=1, lot_size=75, max_loss_rupees=2000)

    assert trigger is None


def test_matches_the_real_oi_footprint_overshoot_example():
    # 14-Aug-2026 real trade: entry 109.05, 19 lots, NIFTY lot_size 75,
    # actual overshot exit was 98.85 (net -Rs 14,850.53). A broker-side
    # trigger at -Rs 2,000 should sit well above that real exit price.
    trigger = compute_stop_loss_trigger_price(entry_premium=109.05, lots=19, lot_size=75, max_loss_rupees=2000)

    assert trigger > 98.85
