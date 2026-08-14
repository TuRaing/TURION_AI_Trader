from indicators.circuit_band import (
    compute_circuit_levels,
    distance_to_circuit_pct,
    is_near_circuit_band,
)


def test_circuit_levels_symmetric_around_previous_close():
    lower, upper = compute_circuit_levels(previous_close=24000, tier_pct=10.0)

    assert lower == 21600
    assert upper == 26400


def test_distance_is_zero_exactly_at_the_upper_band():
    distance = distance_to_circuit_pct(spot=26400, previous_close=24000, tier_pct=10.0)

    assert distance == 0


def test_distance_is_zero_exactly_at_the_lower_band():
    distance = distance_to_circuit_pct(spot=21600, previous_close=24000, tier_pct=10.0)

    assert distance == 0


def test_distance_at_previous_close_equals_the_full_tier():
    # Spot exactly at previous close is tier_pct away from either band.
    distance = distance_to_circuit_pct(spot=24000, previous_close=24000, tier_pct=10.0)

    assert distance == 10.0


def test_distance_uses_the_nearer_band_not_the_farther_one():
    # Spot much closer to the upper band than the lower one.
    distance = distance_to_circuit_pct(spot=26000, previous_close=24000, tier_pct=10.0)

    expected = (400 / 24000) * 100
    assert abs(distance - expected) < 1e-9


def test_is_near_circuit_band_true_within_threshold():
    # Upper band is 26400; spot at 26300 is ~0.42% away - within a 2% threshold.
    assert is_near_circuit_band(spot=26300, previous_close=24000, proximity_threshold_pct=2.0, tier_pct=10.0)


def test_is_near_circuit_band_false_far_from_threshold():
    # A normal, calm day's move (well under 1%) should never trip a 2% proximity gate.
    assert not is_near_circuit_band(spot=24100, previous_close=24000, proximity_threshold_pct=2.0, tier_pct=10.0)


def test_real_14aug_nifty_move_is_nowhere_near_the_circuit_band():
    # Real 14-Aug data: previous close ~24,395.85, day's actual range
    # stayed within ~0.5% - a genuinely calm day, used here as a sanity
    # check that normal trading days don't fire this gate.
    assert not is_near_circuit_band(spot=24366, previous_close=24395.85, proximity_threshold_pct=2.0, tier_pct=10.0)
