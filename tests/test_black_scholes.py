import math

from indicators.black_scholes import black_scholes_price, implied_volatility, black_scholes_greeks


def test_call_put_parity():
    spot, strike, t, vol, r = 24000, 24000, 3 / 365, 0.13, 0.065

    call = black_scholes_price(spot, strike, t, vol, "CE", r)
    put = black_scholes_price(spot, strike, t, vol, "PE", r)

    parity_rhs = spot - strike * math.exp(-r * t)

    assert abs((call - put) - parity_rhs) < 1e-6


def test_zero_time_to_expiry_is_intrinsic_value():
    itm_call = black_scholes_price(24100, 24000, 0, 0.13, "CE")
    otm_call = black_scholes_price(23900, 24000, 0, 0.13, "CE")
    itm_put = black_scholes_price(23900, 24000, 0, 0.13, "PE")

    assert itm_call == 100
    assert otm_call == 0
    assert itm_put == 100


def test_atm_premium_positive_and_reasonable():
    price = black_scholes_price(24000, 24000, 3 / 365, 0.13, "CE")

    assert 0 < price < 500  # sanity range for a ~3-day-to-expiry ATM NIFTY option


def test_higher_volatility_increases_premium():
    low_vol = black_scholes_price(24000, 24000, 3 / 365, 0.10, "CE")
    high_vol = black_scholes_price(24000, 24000, 3 / 365, 0.25, "CE")

    assert high_vol > low_vol


def test_invalid_option_type_raises():
    try:
        black_scholes_price(24000, 24000, 3 / 365, 0.13, "XX")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_implied_volatility_recovers_the_volatility_used_to_price():
    # Round-trip: price at a known vol, then solve backwards - should
    # land back on (near) that same vol.
    spot, strike, t, true_vol = 24000, 24100, 5 / 365, 0.145

    price = black_scholes_price(spot, strike, t, true_vol, "CE")
    recovered_vol = implied_volatility(price, spot, strike, t, "CE")

    assert abs(recovered_vol - true_vol) < 0.001


def test_implied_volatility_round_trip_for_a_put_too():
    spot, strike, t, true_vol = 57800, 57700, 2 / 365, 0.18

    price = black_scholes_price(spot, strike, t, true_vol, "PE")
    recovered_vol = implied_volatility(price, spot, strike, t, "PE")

    assert abs(recovered_vol - true_vol) < 0.001


def test_implied_volatility_none_when_price_below_intrinsic():
    # A quoted price cheaper than intrinsic value is impossible for any
    # positive volatility - e.g. a stale/bad quote - solver should say
    # so rather than return a nonsense number.
    iv = implied_volatility(market_price=50, spot=24200, strike=24000, time_to_expiry_years=5 / 365, option_type="CE")

    assert iv is None


def test_implied_volatility_none_at_or_past_expiry():
    iv = implied_volatility(market_price=100, spot=24000, strike=24000, time_to_expiry_years=0, option_type="CE")

    assert iv is None


def test_greeks_delta_between_0_and_1_for_call():
    greeks = black_scholes_greeks(24000, 24000, 3 / 365, 0.13, "CE")

    assert 0 < greeks["delta"] < 1


def test_greeks_delta_between_minus1_and_0_for_put():
    greeks = black_scholes_greeks(24000, 24000, 3 / 365, 0.13, "PE")

    assert -1 < greeks["delta"] < 0


def test_greeks_theta_is_negative_for_a_long_option():
    # Time decay works against a long option holder - premium should
    # lose value per day passing, all else equal.
    greeks = black_scholes_greeks(24000, 24000, 3 / 365, 0.13, "CE")

    assert greeks["theta"] < 0


def test_greeks_vega_is_positive():
    # Higher volatility always makes an option MORE valuable, never less.
    greeks = black_scholes_greeks(24000, 24000, 3 / 365, 0.13, "CE")

    assert greeks["vega"] > 0


def test_greeks_none_at_zero_time_to_expiry():
    greeks = black_scholes_greeks(24000, 24000, 0, 0.13, "CE")

    assert greeks["delta"] is None
    assert greeks["theta"] is None
    assert greeks["vega"] is None
