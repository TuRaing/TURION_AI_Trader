# Added 03-Aug-2026 - real, percentage-based F&O options transaction
# cost model, kept separate from strategy/transaction_costs.py (that
# module is equity-only - different STT/brokerage rules apply to
# options). Modeled on commonly published discount-broker NSE F&O
# rates (representative, e.g. Zerodha-style) - VERIFY against the
# user's actual broker before trusting this for real capital, same
# caveat as the equity model.

BROKERAGE_PER_ORDER = 20.0          # flat per executed order (buy, sell)
STT_SELL_PCT = 0.1 / 100            # options SELL side, on premium turnover
EXCHANGE_TXN_PCT = 0.03503 / 100    # NSE F&O, on premium turnover
STAMP_DUTY_BUY_PCT = 0.003 / 100    # options BUY side, on premium turnover
SEBI_CHARGES_PCT = 10 / 1e7         # Rs 10 per crore of premium turnover
GST_PCT = 18 / 100                  # on brokerage + exchange + SEBI charges


def calculate_options_round_trip_cost(entry_premium, exit_premium, lot_size, lots):
    """
    Real round-trip (buy + sell) transaction cost for one intraday NIFTY
    options trade, in rupees.

    Parameters
    ----------
    entry_premium, exit_premium : float
        Per-unit option premium.
    lot_size : int
    lots : int

    Returns
    -------
    float
    """

    quantity = lot_size * lots

    buy_value = entry_premium * quantity
    sell_value = exit_premium * quantity

    brokerage = BROKERAGE_PER_ORDER * 2
    stt = sell_value * STT_SELL_PCT
    exchange_charges = (buy_value + sell_value) * EXCHANGE_TXN_PCT
    stamp_duty = buy_value * STAMP_DUTY_BUY_PCT
    sebi_charges = (buy_value + sell_value) * SEBI_CHARGES_PCT
    gst = (brokerage + exchange_charges + sebi_charges) * GST_PCT

    return brokerage + stt + exchange_charges + stamp_duty + sebi_charges + gst
