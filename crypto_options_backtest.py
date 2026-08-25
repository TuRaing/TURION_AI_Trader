import datetime

import requests

from strategy.backtest_live_engine import run_backtest
from strategy.deribit_data import get_instruments, pick_atm_instruments, to_usd_premium
from strategy.event_driven_engine import rsi_momentum_decide_fn, make_st2_threshold_event_cfg
from strategy.live_tick_harness import CandleAggregator

# Added 24-Aug-2026 - Phase 2 of the approved crypto paper-trading
# plan: "try the EXISTING, already-proven RSI-momentum signal unchanged
# against crypto data; only design a new signal if that genuinely
# fails" - this is that actual validation step, run against REAL
# historical Deribit data (Deribit's free public get_tradingview_chart_
# data endpoint), needing no VM/deploy at all. Mirrors strategy/nifty_
# options_backtest.py's role for the NIFTY side, but standalone at root
# like backtest.py/momentum_vix_backtest.py - a one-off analysis
# script, not imported by any live engine.
#
# rsi_momentum_decide_fn/make_st2_threshold_event_cfg are used byte-
# for-byte unchanged (event_driven_engine.py) - no new signal logic
# here, only real historical data assembled into the same data_point
# shape a live tick stream would produce (see strategy/crypto_tick_
# runner.py's own on_tick()).
#
# DATA SOURCE NOTES (confirmed via real queries, 24-Aug-2026):
#  - "spot" comes from BTC-PERPETUAL/ETH-PERPETUAL's own real trade-
#    price history, not the index directly - Deribit's tradingview
#    chart-data endpoint rejects instrument_name="btc_usd" outright
#    ("instrument not found") - the perpetual's price tracks the index
#    closely (funding-rate arbitrage keeps them within basis points),
#    a documented, acceptable proxy for a first validation pass.
#  - ce_ltp/pe_ltp come from the ATM option's own real coin-denominated
#    TRADE price history (get_tradingview_chart_data), converted to USD
#    via to_usd_premium() using the concurrent spot bar - not mark
#    price (Deribit doesn't expose historical mark-price bars via this
#    endpoint) and not bid/ask (no historical depth at all) - ce_bid/
#    ce_ask/pe_bid/pe_ask are left None throughout, same as a backtest
#    replay for the NIFTY side already does (rsi_momentum_decide_fn
#    only reads *_ltp when entry_field/exit_field are both "ltp", which
#    is what this cfg uses).
#  - A real, thin option book trades far from every 5-min bar - missing
#    bars are FORWARD-FILLED from the last real trade (not treated as
#    "no signal"), same "stale but real, not fabricated" choice
#    _maybe_top_up_capital()'s own philosophy elsewhere in this project
#    already reflects for paper bookkeeping.
#
# KNOWN LIMITATION (same one strategy/event_driven_runner.py's build_
# runners() already accepts for the live NIFTY/BankNifty engine - see
# that function's own docstring): the ATM strike is picked ONCE, from
# TODAY's real option chain, not re-derived at each historical
# timestamp - Deribit doesn't expose a historical option-chain listing,
# so there is no way to know what was actually ATM at each past moment
# without a paid data source. Acceptable for a first strategy-
# validation pass over a short (days) lookback window.

CHART_BASE_URL = "https://www.deribit.com/api/v2/public/get_tradingview_chart_data"
RESOLUTION_MINUTES = 5
LOOKBACK_DAYS = 7
INITIAL_CAPITAL = 10000.0


def _fetch_chart_bars(instrument_name, start_ms, end_ms, resolution_minutes=RESOLUTION_MINUTES):
    """
    Real close-price bars (ticks[i] -> close[i]), ms-epoch UTC ticks.
    Returns [] on "no_data" (confirmed real status value, 24-Aug-2026)
    rather than raising - a genuinely untraded instrument/window is a
    valid (if useless) real answer, not an error.
    """

    response = requests.get(CHART_BASE_URL, params={
        "instrument_name": instrument_name,
        "start_timestamp": start_ms,
        "end_timestamp": end_ms,
        "resolution": str(resolution_minutes),
    }, timeout=30)
    response.raise_for_status()
    result = response.json()["result"]

    if result.get("status") != "ok":
        return []

    return list(zip(result["ticks"], result["close"]))


def build_historical_data_points(currency="BTC", lookback_days=LOOKBACK_DAYS):
    """
    Assembles real historical Deribit data into the same data_point
    shape strategy/crypto_tick_runner.py's CryptoTickRunner.on_tick()
    builds live - see this module's own docstring for the real data
    sources and their limitations.
    """

    now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    start_ms = now_ms - lookback_days * 24 * 3600 * 1000

    perpetual = "BTC-PERPETUAL" if currency.upper() == "BTC" else "ETH-PERPETUAL"
    spot_bars = _fetch_chart_bars(perpetual, start_ms, now_ms)

    if not spot_bars:
        raise RuntimeError(f"No historical spot data returned by Deribit for {perpetual}")

    spot_price_now = spot_bars[-1][1]
    instruments = get_instruments(currency)
    expiry, atm_strike, ce_symbol, pe_symbol = pick_atm_instruments(instruments, spot_price_now)

    print(f"ATM instruments picked from today's chain: {ce_symbol} / {pe_symbol} "
          f"(strike {atm_strike}, expiry {datetime.datetime.fromtimestamp(expiry / 1000, tz=datetime.timezone.utc)})")

    ce_bars = dict(_fetch_chart_bars(ce_symbol, start_ms, now_ms))
    pe_bars = dict(_fetch_chart_bars(pe_symbol, start_ms, now_ms))

    print(f"Bars fetched: spot={len(spot_bars)}, ce={len(ce_bars)}, pe={len(pe_bars)}")

    aggregator = CandleAggregator()
    data_points = []
    last_ce_coin, last_pe_coin = None, None

    for ts_ms, spot in spot_bars:
        timestamp = datetime.datetime.fromtimestamp(ts_ms / 1000, tz=datetime.timezone.utc)
        aggregator.on_tick(timestamp, spot)

        if ts_ms in ce_bars:
            last_ce_coin = ce_bars[ts_ms]
        if ts_ms in pe_bars:
            last_pe_coin = pe_bars[ts_ms]

        data_points.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "spot": spot,
            "rsi": aggregator.current_rsi(),
            "ce_symbol": ce_symbol, "ce_ltp": to_usd_premium(last_ce_coin, spot),
            "ce_bid": None, "ce_ask": None,
            "pe_symbol": pe_symbol, "pe_ltp": to_usd_premium(last_pe_coin, spot),
            "pe_bid": None, "pe_ask": None,
            "past_squareoff": False,
            "before_market_open": False,
        })

    return data_points


def main():
    cfg = make_st2_threshold_event_cfg(index="BTC", lot_size=1, initial_capital=INITIAL_CAPITAL)
    data_points = build_historical_data_points("BTC")

    portfolio, actions = run_backtest(rsi_momentum_decide_fn, cfg, data_points, initial_capital=INITIAL_CAPITAL)

    closed = portfolio["Closed Trades"]
    wins = [t for t in closed if t["Net PnL"] > 0]

    print(f"\nData points: {len(data_points)}")
    print(f"Trades: {len(closed)}")
    if closed:
        print(f"Win rate: {len(wins) / len(closed) * 100:.1f}%")
        for t in closed:
            print(f"  {t['Entry Time']} -> {t['Exit Time']} | {t['Option Type']} | "
                  f"{t['Exit Reason']:<10} | Net PnL {t['Net PnL']:.2f}")
    print(f"\nFinal Cash: {portfolio['Cash']:.2f} (started at {INITIAL_CAPITAL:.2f})")
    print(f"Net PnL: {portfolio['Cash'] - INITIAL_CAPITAL:.2f}")


if __name__ == "__main__":
    main()
