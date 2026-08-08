# Added 08-Aug-2026 - real, percentage-based Indian equity DELIVERY
# transaction cost model (multi-day holds, e.g. strategy/paper_trading.py's
# Swing/Watchlist engine) - a SEPARATE model from strategy/transaction_
# costs.py, which is calibrated for INTRADAY equity specifically and would
# be wrong here on several points that genuinely differ for delivery:
#   - STT applies on BOTH buy and sell sides for delivery (0.1% each),
#     not sell-side-only like intraday (0.025%)
#   - Stamp duty rate differs (0.015% delivery vs 0.003% intraday)
#   - Zerodha (this project's representative discount-broker baseline,
#     matching transaction_costs.py's own convention) charges ZERO
#     brokerage on equity delivery trades - intraday's brokerage-with-cap
#     model doesn't apply here at all
#   - Delivery adds DP (Depository Participant) charges on the sell side
#     (a flat per-scrip charge for moving shares out of demat) that
#     intraday trades never incur (shares never actually enter demat)
# Also includes calculate_stcg_tax() - Short-Term Capital Gains tax
# (~20%, the post-Budget-2024 rate) applies specifically to delivery
# equity gains (held >1 day, <1 year) - NOT to intraday (that's taxed as
# speculative business income at the trader's income-slab rate, a
# different regime entirely) and NOT to options (non-speculative business
# income, same slab-rate regime) - so this tax calculation belongs only
# to this delivery-specific module, not a general-purpose one.

STT_PCT = 0.1 / 100                 # delivery: BOTH buy and sell sides
EXCHANGE_TXN_PCT = 0.00297 / 100     # NSE, same rate as intraday
STAMP_DUTY_BUY_PCT = 0.015 / 100     # delivery rate (vs intraday's 0.003%)
SEBI_CHARGES_PCT = 10 / 1e7          # Rs 10 per crore of turnover, same as intraday
DP_CHARGES_PER_SELL = 15.0           # flat, per scrip, sell side only (Zerodha-representative)
GST_PCT = 18 / 100                   # on exchange + SEBI charges (brokerage is Rs 0 here)

STCG_TAX_PCT = 20.0 / 100            # post-Budget-2024 short-term capital gains rate


def calculate_delivery_round_trip_cost(entry_price, exit_price, quantity=1):
    """
    Real round-trip (buy + sell) transaction cost for one equity DELIVERY
    trade, in rupees. Zero brokerage assumed (Zerodha-representative, same
    baseline strategy/transaction_costs.py already uses for intraday).

    Parameters
    ----------
    entry_price : float
    exit_price : float
    quantity : int

    Returns
    -------
    float
    """

    buy_value = entry_price * quantity
    sell_value = exit_price * quantity

    stt = (buy_value + sell_value) * STT_PCT
    exchange_charges = (buy_value + sell_value) * EXCHANGE_TXN_PCT
    stamp_duty = buy_value * STAMP_DUTY_BUY_PCT
    sebi_charges = (buy_value + sell_value) * SEBI_CHARGES_PCT
    dp_charges = DP_CHARGES_PER_SELL
    gst = (exchange_charges + sebi_charges) * GST_PCT

    return stt + exchange_charges + stamp_duty + sebi_charges + dp_charges + gst


def calculate_stcg_tax(net_pnl):
    """
    Short-Term Capital Gains tax on one delivery trade's Net PnL (after
    the round-trip cost above). Only applies to GAINS - a loss isn't
    taxed here (real tax law lets losses offset other gains, but that's
    a portfolio-level/annual calculation, not a per-trade one - this
    keeps the per-trade figure simple and conservative: never claims a
    tax REFUND on an individual losing trade).

    Returns
    -------
    tax : float
    after_tax_pnl : float
    """

    if net_pnl <= 0:
        return 0.0, round(net_pnl, 2)

    tax = round(net_pnl * STCG_TAX_PCT, 2)

    return tax, round(net_pnl - tax, 2)
