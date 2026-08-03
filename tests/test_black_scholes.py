import math

from indicators.black_scholes import black_scholes_price


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
