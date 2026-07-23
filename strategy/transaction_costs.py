# Updated: 2026-07-23 - real, percentage-based Indian equity intraday
# transaction cost model, replacing the flat Rs 30/trade guess used in
# earlier backtests (strategy/orb_vwap_backtest.py etc.) - a flat guess
# badly overstates cost on cheap/small-quantity trades and understates it
# on large ones, since almost every real charge is a percentage of
# turnover, not a fixed rupee amount. Modeled on Zerodha's published
# published intraday equity charges (representative of discount brokers
# generally) - verify against the user's actual broker before trusting
# this for real capital.

BROKERAGE_PER_ORDER_CAP = 20.0
BROKERAGE_PCT = 0.03 / 100          # or the cap, whichever is LOWER
STT_SELL_PCT = 0.025 / 100          # sell side only, intraday equity
EXCHANGE_TXN_PCT = 0.00297 / 100    # NSE
STAMP_DUTY_BUY_PCT = 0.003 / 100    # buy side only
SEBI_CHARGES_PCT = 10 / 1e7            # Rs 10 per crore of turnover
GST_PCT = 18 / 100                  # on brokerage + exchange + SEBI charges


def _brokerage(turnover):

    return min(BROKERAGE_PER_ORDER_CAP, turnover * BROKERAGE_PCT)


def calculate_round_trip_cost(entry_price, exit_price, quantity=1):
    """
    Real round-trip (buy + sell) transaction cost for one intraday equity
    trade, in rupees - percentage-of-turnover based, not a flat guess.

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

    brokerage = _brokerage(buy_value) + _brokerage(sell_value)
    stt = sell_value * STT_SELL_PCT
    exchange_charges = (buy_value + sell_value) * EXCHANGE_TXN_PCT
    stamp_duty = buy_value * STAMP_DUTY_BUY_PCT
    sebi_charges = (buy_value + sell_value) * SEBI_CHARGES_PCT
    gst = (brokerage + exchange_charges + sebi_charges) * GST_PCT

    return brokerage + stt + exchange_charges + stamp_duty + sebi_charges + gst
