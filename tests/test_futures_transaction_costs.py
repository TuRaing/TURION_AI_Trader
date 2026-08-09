from strategy.futures_transaction_costs import calculate_futures_round_trip_cost


def test_futures_cost_is_positive_for_a_normal_trade():
    cost = calculate_futures_round_trip_cost(entry_price=24500, exit_price=24600, quantity=75)

    assert cost > 0


def test_futures_cost_scales_with_notional_value():
    small = calculate_futures_round_trip_cost(entry_price=24500, exit_price=24600, quantity=75)
    large = calculate_futures_round_trip_cost(entry_price=24500, exit_price=24600, quantity=750)

    assert large > small
