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
