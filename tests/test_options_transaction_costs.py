from strategy.options_transaction_costs import (
    calculate_options_round_trip_cost, SPREAD_COST_PCT_NIFTY, SPREAD_COST_PCT_BANKNIFTY,
)


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


def test_spread_pct_defaults_to_none_and_does_not_change_existing_cost():
    without_spread = calculate_options_round_trip_cost(entry_premium=100, exit_premium=110, lot_size=75, lots=13)
    explicit_none = calculate_options_round_trip_cost(entry_premium=100, exit_premium=110, lot_size=75, lots=13,
                                                        spread_pct=None)

    assert without_spread == explicit_none


def test_spread_pct_adds_real_cost_on_top():
    without_spread = calculate_options_round_trip_cost(entry_premium=100, exit_premium=110, lot_size=75, lots=13)
    with_spread = calculate_options_round_trip_cost(entry_premium=100, exit_premium=110, lot_size=75, lots=13,
                                                      spread_pct=SPREAD_COST_PCT_NIFTY)

    quantity = 75 * 13
    avg_premium = (100 + 110) / 2
    expected_spread_cost = avg_premium * quantity * (SPREAD_COST_PCT_NIFTY / 100)

    assert with_spread > without_spread
    assert round(with_spread - without_spread, 6) == round(expected_spread_cost, 6)


def test_banknifty_spread_pct_differs_from_nifty():
    # Real measured medians differ (BANKNIFTY's is wider) - not the
    # same constant reused for both indices.
    assert SPREAD_COST_PCT_BANKNIFTY != SPREAD_COST_PCT_NIFTY
    assert SPREAD_COST_PCT_BANKNIFTY > SPREAD_COST_PCT_NIFTY
