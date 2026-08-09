# Added 09-Aug-2026 - real, percentage-based Indian F&O FUTURES
# transaction cost model - a SEPARATE model from strategy/transaction_
# costs.py (equity intraday) and strategy/options_transaction_costs.py
# (options premium), since futures rates genuinely differ:
#   - STT on futures: 0.02% SELL side only (on the FULL contract
#     notional value - price x lot size x lots - not just premium like
#     options)
#   - Different stamp duty rate (0.002% buy side, futures-specific)
# Zero brokerage assumed - Zerodha (this project's representative
# discount-broker baseline throughout, matching transaction_costs.py's
# own convention) charges flat/negligible brokerage on F&O, already
# effectively captured by the BROKERAGE_PER_ORDER_CAP pattern elsewhere
# - kept simple here since it's a small fraction of the real cost on a
# large-notional futures trade anyway.

STT_SELL_PCT = 0.02 / 100        # futures SELL side only, on full notional
EXCHANGE_TXN_PCT = 0.0019 / 100  # NSE futures
STAMP_DUTY_BUY_PCT = 0.002 / 100 # futures-specific rate, buy side only
SEBI_CHARGES_PCT = 10 / 1e7      # Rs 10 per crore of turnover, same as elsewhere
GST_PCT = 18 / 100                # on exchange + SEBI charges


def calculate_futures_round_trip_cost(entry_price, exit_price, quantity):
    """
    Real round-trip (buy + sell) transaction cost for one futures
    trade, in rupees - percentage-of-NOTIONAL-turnover based.

    Parameters
    ----------
    entry_price : float
    exit_price : float
    quantity : int - lots * lot_size, the full contract quantity

    Returns
    -------
    float
    """

    buy_value = entry_price * quantity
    sell_value = exit_price * quantity

    stt = sell_value * STT_SELL_PCT
    exchange_charges = (buy_value + sell_value) * EXCHANGE_TXN_PCT
    stamp_duty = buy_value * STAMP_DUTY_BUY_PCT
    sebi_charges = (buy_value + sell_value) * SEBI_CHARGES_PCT
    gst = (exchange_charges + sebi_charges) * GST_PCT

    return stt + exchange_charges + stamp_duty + sebi_charges + gst
