import math

# Added 03-Aug-2026 for the NIFTY options money-management backtest
# (strategy/nifty_options_backtest.py) - real historical NIFTY option
# premium data does not exist (NSE's option chain API only ever serves
# today's live snapshot, confirmed 30-Jul), so this estimates a
# theoretical premium from spot + India VIX (used as an implied-
# volatility proxy) instead. This is an ESTIMATE, not a real traded
# price - real premiums also reflect bid/ask spread, open interest,
# and moment-to-moment supply/demand that this model cannot see.


def _norm_cdf(x):

    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_price(spot, strike, time_to_expiry_years, volatility, option_type, risk_free_rate=0.065):
    """
    Theoretical European option premium (Black-Scholes) - close enough for
    a same-day, near-the-money NIFTY weekly option that this backtest
    exits well before expiry (index options are cash-settled and trade
    close to their European-style theoretical value in practice).

    Parameters
    ----------
    spot : float
        Underlying (NIFTY) price.
    strike : float
    time_to_expiry_years : float
        Time to expiry, in years. <= 0 collapses to intrinsic value (the
        position has expired/matured).
    volatility : float
        Annualized volatility as a decimal (e.g. India VIX of 13.5 -> 0.135).
    option_type : str
        "CE" or "PE".
    risk_free_rate : float
        Annualized, decimal. Default 6.5% (representative of an Indian
        risk-free short rate) - a small, mostly cosmetic input for a
        same-day hold where T is tiny.

    Returns
    -------
    float, never negative.
    """

    if option_type not in ("CE", "PE"):
        raise ValueError(f"option_type must be 'CE' or 'PE', got {option_type!r}")

    if time_to_expiry_years <= 0 or volatility <= 0:

        if option_type == "CE":
            return max(spot - strike, 0.0)

        return max(strike - spot, 0.0)

    sqrt_t = math.sqrt(time_to_expiry_years)

    d1 = (
        math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry_years
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t

    if option_type == "CE":
        price = spot * _norm_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(d2)
    else:
        price = strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)

    return max(price, 0.0)


# Added 13-Aug-2026 - the reverse direction: given a REAL traded premium
# (from Entry Premium/Exit Premium, now that Exit Spot is also saved -
# see fyers_options_engine.py's 13-Aug note), back out the volatility
# the market was actually pricing in at that moment. Needed because
# Fyers' option-chain API does not return IV directly (confirmed via
# Fyers' own community forum - a known, open request) - this is the
# standard workaround every tool without a broker-supplied IV field
# uses. Bisection instead of Newton-Raphson - no derivative needed,
# simpler to get right, and volatility search space is small (0-500%)
# so it converges in well under max_iterations regardless.

def implied_volatility(market_price, spot, strike, time_to_expiry_years, option_type,
                        risk_free_rate=0.065, low=0.001, high=5.0, tolerance=0.01, max_iterations=100):
    """
    The volatility that makes black_scholes_price(...) equal market_price,
    found by bisection. Returns None if market_price is below intrinsic
    value or otherwise outside what any positive volatility can produce
    (a real possibility with real bid/ask-driven prices, not a bug).

    Parameters mirror black_scholes_price(), plus:
    market_price : float
        The real traded premium to match.
    low, high : float
        Search bounds on annualized volatility (decimal) - 0.1% to 500%
        comfortably brackets anything a liquid NIFTY/BANKNIFTY option
        should show.
    tolerance : float
        Stop once the implied price is within this many rupees of
        market_price.

    Returns
    -------
    float (annualized volatility, decimal) or None.
    """

    if time_to_expiry_years <= 0 or market_price <= 0:
        return None

    intrinsic = max(spot - strike, 0.0) if option_type == "CE" else max(strike - spot, 0.0)

    if market_price < intrinsic:
        return None

    price_at_high = black_scholes_price(spot, strike, time_to_expiry_years, high, option_type, risk_free_rate)

    if market_price > price_at_high:
        return None

    for _ in range(max_iterations):

        mid = (low + high) / 2
        price = black_scholes_price(spot, strike, time_to_expiry_years, mid, option_type, risk_free_rate)

        if abs(price - market_price) < tolerance:
            return mid

        if price < market_price:
            low = mid
        else:
            high = mid

    return (low + high) / 2


def black_scholes_greeks(spot, strike, time_to_expiry_years, volatility, option_type, risk_free_rate=0.065):
    """
    Delta, Theta, Vega at the given inputs (typically volatility comes
    from implied_volatility() on a real traded premium, not a guess).

    Returns
    -------
    dict with:
      delta : premium change per Re 1 spot move
      theta : premium change per calendar day passing (already negative
              for a long option - decay), NOT per year
      vega  : premium change per 1 percentage-point volatility move
              (e.g. VIX 13.5 -> 14.5)
    None values if time_to_expiry_years or volatility isn't positive
    (Greeks aren't defined at/past expiry or at zero volatility).
    """

    if option_type not in ("CE", "PE"):
        raise ValueError(f"option_type must be 'CE' or 'PE', got {option_type!r}")

    if time_to_expiry_years <= 0 or volatility <= 0:
        return {"delta": None, "theta": None, "vega": None}

    sqrt_t = math.sqrt(time_to_expiry_years)

    d1 = (
        math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry_years
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t

    pdf_d1 = math.exp(-d1 ** 2 / 2) / math.sqrt(2 * math.pi)

    if option_type == "CE":
        delta = _norm_cdf(d1)
        theta_per_year = (
            -(spot * pdf_d1 * volatility) / (2 * sqrt_t)
            - risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(d2)
        )
    else:
        delta = _norm_cdf(d1) - 1
        theta_per_year = (
            -(spot * pdf_d1 * volatility) / (2 * sqrt_t)
            + risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry_years) * _norm_cdf(-d2)
        )

    vega = spot * pdf_d1 * sqrt_t / 100  # per 1 percentage-point vol move

    return {
        "delta": delta,
        "theta": theta_per_year / 365,  # per calendar day
        "vega": vega,
    }
