from strategy.options_transaction_costs import calculate_options_round_trip_cost


def test_cost_is_positive_for_a_typical_trade():
    cost = calculate_options_round_trip_cost(entry_premium=100, exit_premium=110, lot_size=75, lots=13)

    assert cost > 0


def test_cost_increases_with_turnover():
    small = calculate_options_round_trip_cost(entry_premium=50, exit_premium=55, lot_size=75, lots=1)
    large = calculate_options_round_trip_cost(entry_premium=50, exit_premium=55, lot_size=75, lots=20)

    assert large > small


def test_flat_brokerage_floor_even_at_tiny_premium():
    cost = calculate_options_round_trip_cost(entry_premium=1, exit_premium=1, lot_size=75, lots=1)

    assert cost >= 40  # 2 x Rs 20 flat per-order brokerage, at minimum
