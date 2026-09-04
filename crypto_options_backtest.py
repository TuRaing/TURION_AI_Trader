import datetime

from strategy.backtest_live_engine import run_backtest
from strategy.crypto_tick_runner import _realized_pnl_within_hours
from strategy.crypto_transaction_costs import calculate_crypto_options_round_trip_cost
from strategy.deribit_data import get_instruments, get_tradingview_chart_data, pick_atm_instruments, to_usd_premium
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

RESOLUTION_MINUTES = 5
LOOKBACK_DAYS = 7


def build_historical_data_points(currency="BTC", lookback_days=LOOKBACK_DAYS, offset_days=0):
    """
    Assembles real historical Deribit data into the same data_point
    shape strategy/crypto_tick_runner.py's CryptoTickRunner.on_tick()
    builds live - see this module's own docstring for the real data
    sources and their limitations.

    offset_days - added 30-Aug-2026, at the user's own request for a
    consistency check on a DIFFERENT window than "the last 7 days from
    right now" - shifts the whole window back by this many days (e.g.
    offset_days=3 tests 10-3=7 days ago through 3 days ago). Real
    constraint (see this module's own docstring on ATM being picked
    from TODAY's chain): the currently-listed weekly option only has
    real trade history back to when it was FIRST listed - roughly 10-11
    days before its own expiry - so offset_days much beyond ~3-4 will
    start running into thin/missing real CE-PE data for a weekly
    contract, not a limitation of this parameter itself.
    """

    now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    now_ms -= offset_days * 24 * 3600 * 1000
    start_ms = now_ms - lookback_days * 24 * 3600 * 1000

    perpetual = "BTC-PERPETUAL" if currency.upper() == "BTC" else "ETH-PERPETUAL"
    spot_bars = get_tradingview_chart_data(perpetual, start_ms, now_ms, RESOLUTION_MINUTES)

    if not spot_bars:
        raise RuntimeError(f"No historical spot data returned by Deribit for {perpetual}")

    spot_price_now = spot_bars[-1][1]
    instruments = get_instruments(currency)
    expiry, atm_strike, ce_symbol, pe_symbol = pick_atm_instruments(instruments, spot_price_now)

    print(f"ATM instruments picked from today's chain: {ce_symbol} / {pe_symbol} "
          f"(strike {atm_strike}, expiry {datetime.datetime.fromtimestamp(expiry / 1000, tz=datetime.timezone.utc)})")

    ce_bars = dict(get_tradingview_chart_data(ce_symbol, start_ms, now_ms, RESOLUTION_MINUTES))
    pe_bars = dict(get_tradingview_chart_data(pe_symbol, start_ms, now_ms, RESOLUTION_MINUTES))

    print(f"Bars fetched: spot={len(spot_bars)}, ce={len(ce_bars)}, pe={len(pe_bars)}")

    aggregator = CandleAggregator()
    data_points = []
    last_ce_coin, last_pe_coin = None, None

    # spot_ema - added 01-Sep-2026, at the user's own request, feeding
    # event_driven_engine.py's opt-in require_trend_confirmation gate
    # (see that module's own note for the real 4-Sep whipsaw this is
    # meant to fix). EMA_PERIOD=12 at this module's own 5-min
    # resolution = a 1-hour trend read, deliberately much slower than
    # CandleAggregator's own RSI (which reacts within a few candles) -
    # "slow" is the whole point, so a brief RSI-oversold/overbought
    # blip inside a longer trend doesn't count as trend-reversal
    # confirmation. None until EMA_PERIOD real spot bars have been
    # seen (matches every other "not ready yet" field in this
    # project - never a silently-immature reading).
    EMA_PERIOD = 12
    ema_alpha = 2 / (EMA_PERIOD + 1)
    spot_ema = None
    bars_seen = 0

    for ts_ms, spot in spot_bars:
        timestamp = datetime.datetime.fromtimestamp(ts_ms / 1000, tz=datetime.timezone.utc)
        aggregator.on_tick(timestamp, spot)

        if ts_ms in ce_bars:
            last_ce_coin = ce_bars[ts_ms]
        if ts_ms in pe_bars:
            last_pe_coin = pe_bars[ts_ms]

        bars_seen += 1
        spot_ema = spot if spot_ema is None else ema_alpha * spot + (1 - ema_alpha) * spot_ema

        data_points.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "spot": spot,
            "spot_ema": spot_ema if bars_seen >= EMA_PERIOD else None,
            "rsi": aggregator.current_rsi(),
            "ce_symbol": ce_symbol, "ce_ltp": to_usd_premium(last_ce_coin, spot),
            "ce_bid": None, "ce_ask": None,
            "pe_symbol": pe_symbol, "pe_ltp": to_usd_premium(last_pe_coin, spot),
            "pe_bid": None, "pe_ask": None,
            "past_squareoff": False,
            "before_market_open": False,
        })

    return data_points


def _print_summary(currency, initial_capital, portfolio, data_points):
    closed = portfolio["Closed Trades"]
    wins = [t for t in closed if t["Net PnL"] > 0]

    print(f"\n=== {currency} (capital {initial_capital:.2f}) ===")
    print(f"Data points: {len(data_points)}")
    print(f"Trades: {len(closed)}")
    if closed:
        print(f"Win rate: {len(wins) / len(closed) * 100:.1f}%")
        for t in closed:
            print(f"  {t['Entry Time']} -> {t['Exit Time']} | {t['Option Type']} | "
                  f"{t['Exit Reason']:<10} | Net PnL {t['Net PnL']:.2f}")
    print(f"Final Cash: {portfolio['Cash']:.2f} (started at {initial_capital:.2f})")
    print(f"Net PnL: {portfolio['Cash'] - initial_capital:.2f}")


def run_for(currency, initial_capital, data_points):
    """
    Runs one currency's backtest at its own capital - split out
    29-Aug-2026 so BTC and ETH (very different real contract sizes -
    1 lot = 1 full coin notional, so BTC's own ATM premium runs
    $1,500-2,500+ vs ETH's $50-150) can each be checked at the capital
    that actually suits their own economics, in one script run, rather
    than only ever testing one currency/capital pair per run.

    data_points - CHANGED 30-Aug-2026 from "fetched internally" to "a
    parameter" - real bug caught the same day: this used to call
    build_historical_data_points() itself, so calling this multiple
    times per currency (to compare variants) each refetched "the last
    7 days from right now" independently. Since real time moves forward
    between calls, each variant silently ran against a DIFFERENT
    historical window (occasionally even a different ATM strike, if
    spot crossed one between calls) - the daily_loss_lock/12h-window
    comparison this function exists for was NOT apples-to-apples until
    this fix (confirmed live: the exact same "24h lock" config produced
    opposite-sign results, +$1,702 then -$6,586, purely from this).
    Callers now fetch data_points ONCE per currency and pass the SAME
    object to every variant being compared.
    """

    cfg = make_st2_threshold_event_cfg(index=currency, lot_size=1, initial_capital=initial_capital,
                                        cost_fn=calculate_crypto_options_round_trip_cost)

    portfolio, actions = run_backtest(rsi_momentum_decide_fn, cfg, data_points, initial_capital=initial_capital)
    _print_summary(currency, initial_capital, portfolio, data_points)


def run_for_with_profit_lock(currency, initial_capital, data_points, profit_lock_pct=1.0, lock_window_hours=2,
                              trailing_min_pct=None):
    """
    Added 30-Aug-2026, at the user's own request - "2h साठी 1% profit
    lock करून trade stop": once realized PnL within the last
    `lock_window_hours` hours reaches `profit_lock_pct`% of
    initial_capital, block new entries until that rolling window's
    realized PnL drops back under the threshold again (naturally, as
    old winning trades age out of the window) - cfg's existing
    daily_profit_lock/daily_profit_lock_pct (make_st2_threshold_event_
    cfg) fed by a rolling-window today_realized_pnl instead of a
    UTC-calendar-day one, same rolling-window treatment already given
    to daily_loss_lock above (see run_for_with_daily_loss_lock()'s own
    note for why a calendar-day reset doesn't fit a 24/7 market).

    Same "reimplement the trivial step loop locally, don't touch the
    shared backtest_live_engine.py" reasoning as run_for_with_daily_
    loss_lock() - only one more injected field (today_realized_pnl)
    alongside the same today_consecutive_losses this needs too, since
    daily_loss_lock's own gate stays available (both gates are
    independent opt-ins in cfg).

    trailing_min_pct - added 30-Aug-2026, user's own follow-up ask
    ("profit lock (1%, 12h) ला trailing stop loss लाऊन") - optional,
    stacks strategy/event_driven_engine.py's trailing-stop variant
    (see that module's own 30-Aug-2026 note) on top of the profit lock
    being tested here, rather than being a separate function - the two
    are independent cfg opt-ins that compose cleanly (profit lock gates
    NEW entries; trailing changes how an OPEN position exits).
    """

    cfg = make_st2_threshold_event_cfg(index=currency, lot_size=1, initial_capital=initial_capital,
                                        cost_fn=calculate_crypto_options_round_trip_cost,
                                        daily_profit_lock=True, daily_profit_lock_pct=profit_lock_pct,
                                        trailing_min_pct=trailing_min_pct)

    portfolio = {"Cash": initial_capital, "Position": None, "Closed Trades": []}

    for data_point in data_points:
        timestamp = datetime.datetime.strptime(data_point["timestamp"], "%Y-%m-%d %H:%M:%S")
        realized_pnl = _realized_pnl_within_hours(portfolio, timestamp, lock_window_hours)
        data_point = {**data_point, "today_realized_pnl": realized_pnl}

        action, position, trade = rsi_momentum_decide_fn(cfg, portfolio["Position"], data_point)
        portfolio["Position"] = position
        if trade is not None:
            portfolio["Cash"] += trade["Net PnL"]
            portfolio["Closed Trades"].append(trade)

    label = f"{currency} (profit lock, {profit_lock_pct}%, {lock_window_hours}h window"
    label += f", trailing {trailing_min_pct}%)" if trailing_min_pct is not None else ")"
    _print_summary(label, initial_capital, portfolio, data_points)


def main():
    # CHANGED 29-Aug-2026, user's own explicit ask - BTC at an amount
    # that can actually afford a lot ($10,000), ETH at the Rs
    # 1,00,000-equivalent ($1,047.89) - see run_crypto_options_engine.
    # py's own matching 29-Aug-2026 note for the real "capital
    # insufficient for 1 lot" finding behind this split.
    #
    # data_points fetched ONCE per currency here, then reused for every
    # variant below - see run_for()'s own 30-Aug-2026 note for the real
    # apples-to-apples bug this fixes.
    #
    # SIMPLIFIED 30-Aug-2026 - this function briefly carried several
    # more experiments (daily_loss_lock at 24h/12h windows, a trailing-
    # stop variant) tried and rejected the same session (all made
    # things worse or showed no consistent benefit vs the plain
    # baseline - see doc/CRYPTO_PROJECT_STATUS.md's own record of each
    # result) - removed here to keep this script's actual current
    # experiment readable, not a growing pile of dead-end variants.
    # Only the one variant that showed a real, consistent improvement -
    # profit lock (1%, 2h rolling window), no trailing - is kept, now
    # tested on TWO different real windows for a consistency check.
    btc_data_recent = build_historical_data_points("BTC")
    eth_data_recent = build_historical_data_points("ETH")

    run_for("BTC", 10000.0, btc_data_recent)
    run_for("ETH", 1047.89, eth_data_recent)

    run_for_with_profit_lock("BTC", 10000.0, btc_data_recent, profit_lock_pct=1.0, lock_window_hours=2)
    run_for_with_profit_lock("ETH", 1047.89, eth_data_recent, profit_lock_pct=1.0, lock_window_hours=2)

    # Added 30-Aug-2026, user's own explicit consistency check - same
    # profit-lock setting, an OLDER, non-overlapping-as-far-as-real-
    # data-allows window (offset_days=3 - see build_historical_data_
    # points()'s own note on why this can't go much further back for a
    # weekly option contract).
    btc_data_older = build_historical_data_points("BTC", offset_days=3)
    eth_data_older = build_historical_data_points("ETH", offset_days=3)

    run_for("BTC", 10000.0, btc_data_older)
    run_for("ETH", 1047.89, eth_data_older)

    run_for_with_profit_lock("BTC", 10000.0, btc_data_older, profit_lock_pct=1.0, lock_window_hours=2)
    run_for_with_profit_lock("ETH", 1047.89, eth_data_older, profit_lock_pct=1.0, lock_window_hours=2)


if __name__ == "__main__":
    main()
