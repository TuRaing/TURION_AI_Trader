# Added 14-Aug-2026 - NSE index-level market-wide circuit breaker bands
# (see doc/PROJECT_STATUS.md's "CIRCUIT-BREAKER PROTECTION IDEAS" entry,
# candidate #3: a proactive square-off filter that exits BEFORE the
# underlying reaches a circuit level, instead of waiting for the normal
# Target/Stop-Loss check - a halted position can't be closed at all
# until trading resumes, so getting out early is the only protection
# once price is genuinely close). NSE's index-level circuit breakers
# trip at 10%/15%/20% movement in NIFTY 50 from the previous trading
# day's closing value (same tiers for BANKNIFTY-linked instruments,
# since the market-wide halt is driven by NIFTY 50's own move). This
# module only computes the pure distance-to-band math - it does not
# decide what a strategy does with that number.

CIRCUIT_TIERS_PCT = (10.0, 15.0, 20.0)


def compute_circuit_levels(previous_close, tier_pct=10.0):
    """
    Pure function - the lower and upper index levels that would trip
    the given circuit tier, relative to the previous trading day's
    closing value.

    Returns
    -------
    (lower_level, upper_level) : tuple of float
    """

    band = previous_close * (tier_pct / 100)

    return previous_close - band, previous_close + band


def distance_to_circuit_pct(spot, previous_close, tier_pct=10.0):
    """
    Pure function - how far the current spot is from the NEARER circuit
    boundary, expressed as a percentage of the previous close (so it's
    directly comparable to tier_pct itself). A smaller number means
    spot is closer to tripping that circuit tier.

    Returns
    -------
    float, always >= 0.
    """

    lower, upper = compute_circuit_levels(previous_close, tier_pct)

    distance_to_upper = abs(upper - spot)
    distance_to_lower = abs(spot - lower)

    nearer_distance = min(distance_to_upper, distance_to_lower)

    return (nearer_distance / previous_close) * 100


def is_near_circuit_band(spot, previous_close, proximity_threshold_pct=2.0, tier_pct=10.0):
    """
    Pure function - True once spot is within proximity_threshold_pct
    (as a percentage of previous_close) of tripping the given circuit
    tier. Intended as a proactive square-off gate, checked alongside
    the normal Target/Stop-Loss check - see the module docstring above.
    """

    return distance_to_circuit_pct(spot, previous_close, tier_pct) <= proximity_threshold_pct
