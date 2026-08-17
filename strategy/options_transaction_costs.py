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

# Added 17-Aug-2026 - REAL measured bid-ask spread (not an assumption -
# see PROJECT_STATUS.md's "REAL SPREAD MEASURED FROM COLLECTED DATA"
# entry), computed from reports/options_premium_history.jsonl's 28,820
# real Bid/Ask snapshots collected since 04-Aug via strategy/fyers_
# options_collector.py. Median spread as %% of mid-price, ATM strikes:
# NIFTY 0.26%%, BANKNIFTY 0.31%% - well under the ~1-1.3%% breakeven
# threshold found in the 15-Aug theoretical slippage stress-test, so
# adding this does not flip any currently-profitable book to a loss
# under typical conditions (the rare p99 tail, ~3.3-3.8%%, is not
# modeled here - a single flat median, not a distribution).
SPREAD_COST_PCT_NIFTY = 0.26
SPREAD_COST_PCT_BANKNIFTY = 0.31


def calculate_options_round_trip_cost(entry_premium, exit_premium, lot_size, lots, spread_pct=None):
    """
    Real round-trip (buy + sell) transaction cost for one intraday NIFTY
    options trade, in rupees.

    Parameters
    ----------
    entry_premium, exit_premium : float
        Per-unit option premium.
    lot_size : int
    lots : int
    spread_pct : float or None
        Added 17-Aug-2026 - when set, adds the real measured bid-ask
        spread cost (SPREAD_COST_PCT_NIFTY/BANKNIFTY above) on top of
        the existing brokerage/STT/exchange/stamp-duty/SEBI/GST costs -
        approximates the round-trip cost of crossing the spread once
        (buy near the ask, sell near the bid), applied to the average
        of entry/exit premium. Default None keeps every existing
        caller's behavior EXACTLY unchanged - this is an opt-in
        addition, not a retroactive change to any already-running
        book's cost basis (matches this project's "never modify a
        working module" rule - see fyers_options_engine.py's identical
        opt-in pattern for hybrid_sl_cap_pct/daily_profit_lock_pct/
        trailing_min_pct).

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

    total = brokerage + stt + exchange_charges + stamp_duty + sebi_charges + gst

    if spread_pct is not None:
        avg_premium = (entry_premium + exit_premium) / 2
        total += avg_premium * quantity * (spread_pct / 100)

    return total
