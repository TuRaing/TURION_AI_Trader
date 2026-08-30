import requests

# Added 29-Aug-2026, at the user's own request - "आपण slippage कसा
# मोजणार" (how will we measure slippage). Deliberately the CHEAP first
# step, not strategy/depth_collector.py's "walk the real order book"
# method - that needs a Deribit depth archive which doesn't exist yet
# (see doc/CRYPTO_PROJECT_STATUS.md's own note on this). This script
# instead reads two fields ALREADY recorded on every crypto closed
# trade, no new data collection needed:
#
#   "Net PnL"       - recorded PnL, based on LTP (last traded price)
#   "Net PnL (Quote)" - recorded PnL, based on the real bid/ask at
#                       entry/exit (see strategy/event_driven_engine.
#                       py's _rsi_momentum_decide(), entry_field="ltp"
#                       branch - this is reporting-only, it does NOT
#                       drive the live engine's own entry/exit
#                       decisions, which stay LTP-based)
#
# Same method the NIFTY side's 21-Aug-2026 retrospective analysis used
# to first catch this same class of gap (LTP overstated realized PnL
# by ~87-91% on a thin ATM book) - before that book, run_depth_
# collector.py's real order-book archive existed. This script is the
# crypto equivalent of that FIRST, no-new-infra pass.
#
# Reads live from the SAME public Firebase Realtime Database REST
# endpoint crypto_app polls (see crypto_app/lib/api.dart's own module
# comment for why this is safe/public) - not the local reports/*.json
# on the VM, so this runs correctly from any machine, not just the VM
# itself.

RTDB_BASE = "https://turion-ai-trader-default-rtdb.asia-southeast1.firebasedatabase.app"
BOOKS = [("BTC", "rsi_momentum_crypto_btc"), ("ETH", "rsi_momentum_crypto_eth")]


def fetch_closed_trades(strategy_name):
    response = requests.get(f"{RTDB_BASE}/event_driven_portfolios/{strategy_name}.json", timeout=15)
    response.raise_for_status()
    portfolio = response.json() or {}
    return portfolio.get("Closed Trades", [])


def analyze_book(label, strategy_name):
    trades = fetch_closed_trades(strategy_name)

    usable = [t for t in trades if t.get("Net PnL (Quote)") is not None]
    skipped = len(trades) - len(usable)

    print(f"\n=== {label} ({strategy_name}) ===")
    print(f"Closed trades: {len(trades)} (usable for slippage: {len(usable)}, "
          f"skipped - missing quote data: {skipped})")

    if not usable:
        return

    total_ltp = sum(t["Net PnL"] for t in usable)
    total_quote = sum(t["Net PnL (Quote)"] for t in usable)
    gap = total_ltp - total_quote

    print(f"Total Net PnL (LTP, what the live engine reports):  {total_ltp:+.2f}")
    print(f"Total Net PnL (Quote, real bid/ask fill):           {total_quote:+.2f}")
    print(f"Gap (LTP minus Quote):                               {gap:+.2f}")

    if total_quote != 0:
        overstatement_pct = gap / abs(total_quote) * 100
        print(f"LTP overstates real PnL by: {overstatement_pct:+.1f}%")

    worst = max(usable, key=lambda t: t["Net PnL"] - t["Net PnL (Quote)"])
    worst_gap = worst["Net PnL"] - worst["Net PnL (Quote)"]
    print(f"Worst single-trade gap: {worst_gap:+.2f} "
          f"({worst['Symbol']} {worst['Option Type']}, LTP {worst['Net PnL']:+.2f} "
          f"vs Quote {worst['Net PnL (Quote)']:+.2f}, {worst['Exit Time']})")


def main():
    for label, strategy_name in BOOKS:
        analyze_book(label, strategy_name)


if __name__ == "__main__":
    main()
