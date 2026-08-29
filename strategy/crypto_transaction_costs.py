# Added 29-Aug-2026 - Deribit-specific options round-trip cost model,
# kept separate from strategy/options_transaction_costs.py (that
# module's BROKERAGE_PER_ORDER/STT/stamp-duty/SEBI constants are all
# INR figures for Indian NSE F&O). CLAUDE.md's own rule keeps crypto
# options logic fully separate from the NIFTY/BankNifty logic - the
# real bug this file fixes is exactly that separation having been
# violated: event_driven_engine.py's _net_pnl() was calling the NIFTY
# cost function directly on USD Deribit premiums, so a real Rs 20/
# order flat brokerage was being subtracted as $20 - about 95x too
# large at the real USD/INR rate (~95.43, see the crypto sub-project's
# own capital-conversion note). That single misapplied flat fee alone
# was enough to turn almost every ETH paper trade into a loss
# regardless of real price movement (confirmed live: a clean ETH
# backtest at Rs 1,00,000-equivalent capital produced 967 trades over
# 7 days, 0.5% win rate, nearly every one a uniform ~$48-50 "Stop
# Loss" - overwhelmingly this misapplied brokerage, not the market).
#
# Deribit's real options fee schedule: ~0.03% of the underlying index
# price per contract, capped at 12.5% of the option premium, no flat
# per-order brokerage at all. Modeled here as a simple percentage of
# premium turnover (conservative, taker-side) rather than plumbing the
# index price through every _net_pnl call site for a closer replica -
# same "good enough for paper bookkeeping" bar this project already
# applies elsewhere (see e.g. deribit_data.py's perpetual-as-index-
# proxy note).

TAKER_FEE_PCT = 0.03 / 100  # of premium turnover, each side (buy + sell)


def calculate_crypto_options_round_trip_cost(entry_premium, exit_premium, lot_size, lots, spread_pct=None):
    """
    Real round-trip (buy + sell) transaction cost for one Deribit
    crypto options trade, in USD - see this module's own docstring for
    why this exists as a separate function from the NIFTY/BankNifty
    cost model rather than reusing it.

    Same signature as options_transaction_costs.calculate_options_
    round_trip_cost() so either can be passed as a cfg["cost_fn"]
    override into event_driven_engine.py's _net_pnl() unchanged.
    """

    quantity = lot_size * lots

    buy_value = entry_premium * quantity
    sell_value = exit_premium * quantity

    fee = (buy_value + sell_value) * TAKER_FEE_PCT

    spread_cost = 0.0
    if spread_pct is not None:
        avg_premium = (entry_premium + exit_premium) / 2
        spread_cost = avg_premium * quantity * (spread_pct / 100)

    return fee + spread_cost
