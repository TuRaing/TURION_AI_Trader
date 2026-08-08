from strategy.delivery_transaction_costs import calculate_delivery_round_trip_cost, calculate_stcg_tax


def test_delivery_cost_is_positive_for_a_normal_trade():
    cost = calculate_delivery_round_trip_cost(entry_price=1000, exit_price=1050, quantity=10)

    assert cost > 0


def test_delivery_cost_includes_stt_on_both_sides():
    # STT alone (buy + sell) should already exceed a same-side-only STT
    # calc, confirming both sides are counted (unlike intraday's sell-only).
    buy_value = 1000 * 10
    sell_value = 1050 * 10
    expected_min_stt = (buy_value + sell_value) * (0.1 / 100)

    cost = calculate_delivery_round_trip_cost(entry_price=1000, exit_price=1050, quantity=10)

    assert cost >= expected_min_stt


def test_delivery_cost_includes_flat_dp_charge():
    # Even a trivially small trade should carry at least the flat DP charge.
    cost = calculate_delivery_round_trip_cost(entry_price=10, exit_price=10.01, quantity=1)

    assert cost >= 15.0


def test_stcg_tax_is_20_percent_of_a_gain():
    tax, after_tax = calculate_stcg_tax(net_pnl=1000)

    assert tax == 200.0
    assert after_tax == 800.0


def test_stcg_tax_is_zero_on_a_loss():
    tax, after_tax = calculate_stcg_tax(net_pnl=-500)

    assert tax == 0.0
    assert after_tax == -500.0


def test_stcg_tax_is_zero_on_exactly_zero_pnl():
    tax, after_tax = calculate_stcg_tax(net_pnl=0)

    assert tax == 0.0
    assert after_tax == 0.0
