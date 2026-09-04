import concurrent.futures
import datetime
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
# See run_event_driven_engine.py's own matching note - under systemd,
# stdout isn't a TTY, so Python defaults to full block buffering
# instead of line buffering, which would sit every print() unflushed
# for a long time rather than reaching `journalctl` promptly.

# Added 29-Aug-2026, real bug caught live on the deployed VM: systemd's
# EnvironmentFile= parser does not safely round-trip a raw JSON blob
# (the service account key's embedded quotes/backslashes get mangled -
# confirmed live: "Unable to load PEM file... Invalid symbol 61") even
# though the exact same FIREBASE_SERVICE_ACCOUNT-env-var-holds-raw-JSON
# contract already works fine via GitHub Actions secrets (see report/
# push_notifier.py's own docstring). Rather than touch that shared,
# already-proven module, this entrypoint reads the JSON from a FILE
# (FIREBASE_SERVICE_ACCOUNT_FILE, a plain path - safe for systemd's
# EnvironmentFile, no special characters) and sets the env var itself,
# in Python, where there's no shell/systemd-style escaping to get
# wrong. FIREBASE_SERVICE_ACCOUNT itself (if already set directly) is
# left untouched - this is purely a fallback for the file-based path.
_service_account_file = os.environ.get("FIREBASE_SERVICE_ACCOUNT_FILE")
if _service_account_file and not os.environ.get("FIREBASE_SERVICE_ACCOUNT"):
    with open(_service_account_file, "r") as _f:
        os.environ["FIREBASE_SERVICE_ACCOUNT"] = _f.read()

from report.firebase_realtime_sync import sync_portfolio, sync_strategy_tick, sync_strategy_candles
from strategy.crypto_transaction_costs import calculate_crypto_options_round_trip_cost
from strategy.crypto_tick_runner import CryptoTickRunner, load_portfolio, save_portfolio
from strategy.deribit_data import (
    get_index_price, get_instruments, get_tradingview_chart_data, pick_atm_instruments, connect_and_run,
)
from strategy.event_driven_engine import rsi_momentum_decide_fn, rsi_momentum_quote_decide_fn, make_st2_threshold_event_cfg
from strategy.execution_backend import PaperExecutionBackend
from strategy.live_tick_harness import MIN_CANDLES_FOR_RSI
from strategy.tick_collector import LiveCandleAggregator

# Added 24-Aug-2026 - Phase 3 of the approved crypto paper-trading plan
# (see this branch's own plan / doc/PROJECT_STATUS.md): the VM entry
# point for the Deribit BTC options book, mirroring run_event_driven_
# engine.py's "top-level script resolves real config/network calls,
# strategy/ modules underneath stay pure/testable" split. Simpler than
# the Fyers version - no fetch_access_token()/weekend gate needed:
# every Deribit endpoint here is unauthenticated public market data,
# and Deribit is a 24/7 market with no NSE-style trading hours.
#
# rsi_momentum_decide_fn/make_st2_threshold_event_cfg used byte-for-
# byte unchanged (strategy/event_driven_engine.py), per the plan's own
# "try the current strategy first" rule - checked against real
# historical Deribit data first (crypto_options_backtest.py) before
# this live-wiring step was written. Two separate 7-day backtest runs
# gave opposite results (+$7,716 then -$4,382, on $10,000, different
# real weeks) - small-sample real-market variance, not yet enough to
# call the signal proven OR broken. Live paper results on the deployed
# VM are what actually decides that, not either single backtest run.
#
# ONE currency per PROCESS (not per script) - each currency runs as
# its own systemd service/connect_and_run() connection, configured via
# CRYPTO_CURRENCY/CRYPTO_INITIAL_CAPITAL env vars rather than a shared
# MultiStrategyRouter (strategy/event_driven_runner.py's approach for
# NIFTY's 4 concurrent books) - simpler, and each currency's own ATM
# instrument/capital needs are genuinely independent, not worth a
# shared-connection abstraction for just two books.
#
# CHANGED 29-Aug-2026, real constraint found live on the deployed VM:
# 1 Deribit option contract = 1 full coin notional (lot_size=1) - at
# BTC's real spot (~$77-79k), a single ATM weekly premium runs
# $1,500-2,500+, so a Rs 1,00,000-equivalent ($1,048) BTC book can
# NEVER afford even 1 lot ("SKIPPED (capital insufficient for 1 lot..."
# on every single tick, confirmed live). ETH's spot (~$2,400-2,500) is
# ~30x smaller, so ETH's own ATM weekly premiums ($50-150) fit
# comfortably inside Rs 1,00,000 - user's own explicit fix: run BTC at
# an amount that can actually afford lots ($10,000, the original,
# already-proven-live value) and ETH at the Rs 1,00,000-equivalent
# ($1,047.89) separately, rather than forcing one capital figure onto
# both currencies' very different real contract economics.
#
# NOT LIVE-TESTED beyond this session's own manual WebSocket
# verification (see strategy/deribit_data.py's connect_and_run()
# docstring) - actually running this needs the standalone VM from
# Phase 4 of the plan, which doesn't exist yet.

_DEFAULT_CAPITAL = {"BTC": 10000.0, "ETH": 1047.89}

CURRENCY = os.environ.get("CRYPTO_CURRENCY", "BTC").upper()
INITIAL_CAPITAL = float(os.environ.get("CRYPTO_INITIAL_CAPITAL", _DEFAULT_CAPITAL.get(CURRENCY, 10000.0)))
CANDLE_SEED_HOURS = 12  # comfortably more than MIN_CANDLES_FOR_RSI * 5min needs

# CRYPTO_QUOTE_BASED - added 29-Aug-2026, real live finding: comparing
# every closed trade's LTP-based "Net PnL" against its already-recorded
# "Net PnL (Quote)" (analyze_crypto_slippage.py) showed LTP overstates
# real PnL by ~90-95% on this thin ATM book - same class of gap the
# NIFTY side found on 21-Aug-2026, fixed there the same way: a second,
# SEPARATE book (rsi_momentum_quote_decide_fn - real ask at entry, real
# bid at exit, not LTP) alongside the original rather than replacing
# it, per this project's "never silently change a running book" rule.
# Own STRATEGY_NAME (suffix "_quote") so it gets its own portfolio
# file/systemd unit and never mixes history with the original LTP book
# - see deploy/turion-crypto-options-*-quote.service.
QUOTE_BASED = os.environ.get("CRYPTO_QUOTE_BASED", "0") == "1"
DECIDE_FN = rsi_momentum_quote_decide_fn if QUOTE_BASED else rsi_momentum_decide_fn

# CRYPTO_PROFIT_LOCK_PCT/CRYPTO_PROFIT_LOCK_WINDOW_HOURS - added
# 30-Aug-2026, at the user's own request, after a real backtest sweep
# (doc/CRYPTO_PROJECT_STATUS.md's own record) found daily_profit_lock
# helps BOTH BTC and ETH, but only with a short ROLLING window (BTC:
# 1%/2h, ETH: 0.5%/3h - NOT the same for both, and NOT the UTC-
# calendar-day boundary daily_profit_lock normally uses elsewhere - see
# strategy/crypto_tick_runner.py's _realized_pnl_within_hours() for
# why a 24/7 market needs a rolling window instead). Same "separate
# book, not a change to the running one" rule as CRYPTO_QUOTE_BASED
# above - own STRATEGY_NAME suffix ("_profitlock") so it never mixes
# portfolio history with the original book. PROFIT_LOCK_PCT unset
# (None) means the gate stays off entirely - every existing book's
# behavior is unchanged unless a systemd unit explicitly sets this.
_profit_lock_pct_raw = os.environ.get("CRYPTO_PROFIT_LOCK_PCT")
PROFIT_LOCK_ENABLED = _profit_lock_pct_raw is not None
PROFIT_LOCK_PCT = float(_profit_lock_pct_raw) if PROFIT_LOCK_ENABLED else None
PROFIT_LOCK_WINDOW_HOURS = float(os.environ.get("CRYPTO_PROFIT_LOCK_WINDOW_HOURS", 24))

# CRYPTO_RSI_CE_THRESHOLD/CRYPTO_RSI_PE_THRESHOLD - added 31-Aug-2026,
# after a real finding: a plain RSI>=50 midpoint split fires on every
# marginal RSI wobble on a choppy day, disproportionately hurting PE
# entries (see strategy/event_driven_engine.py's own 31-Aug-2026 note
# for the exact BTC/ETH numbers). A backtest sweep found CE>=70/PE<=30
# (real conviction required, not just crossing 50) flips BOTH BTC and
# ETH from a loss to a real profit - and critically, PE trades
# THEMSELVES turn profitable too, not just filtered out. Same
# "separate book" rule as every other opt-in above - own STRATEGY_NAME
# suffix ("_rsi70") so it never mixes history with the plain book.
# Both default to 50 (unset) so every existing book's behavior is
# unchanged.
RSI_CE_THRESHOLD = float(os.environ.get("CRYPTO_RSI_CE_THRESHOLD", 50))
RSI_PE_THRESHOLD = float(os.environ.get("CRYPTO_RSI_PE_THRESHOLD", 50))
RSI_THRESHOLD_CHANGED = RSI_CE_THRESHOLD != 50 or RSI_PE_THRESHOLD != 50

# CRYPTO_DAILY_LOSS_LOCK/CRYPTO_MAX_CONSECUTIVE_LOSSES - added
# 01-Sep-2026, after a real live whipsaw: BTC RSI-70/30 took 9
# consecutive PE Stop-Losses in 12 minutes on 4-Sep (spot trending up
# against every "conviction" PE entry). A combo backtest sweep found
# RSI-70/30 + daily_loss_lock (max 2 consecutive losses, the existing
# UTC-calendar-day version - see event_driven_engine.py's own note)
# was the ONLY variant positive in BOTH tested real windows for BTC
# (recent: -$1,172 -> +$5,189; older: still +$10,525) - see doc/
# CRYPTO_PROJECT_STATUS.md's own sweep record. ETH did NOT show the
# same benefit, so this is deployed BTC-only for now (own systemd
# unit, not a currency-agnostic env default). Own STRATEGY_NAME suffix
# ("_lock") so it never mixes history with the plain RSI-70/30 book.
DAILY_LOSS_LOCK_ENABLED = os.environ.get("CRYPTO_DAILY_LOSS_LOCK", "0") == "1"
MAX_CONSECUTIVE_LOSSES = int(os.environ.get("CRYPTO_MAX_CONSECUTIVE_LOSSES", 2))

STRATEGY_NAME = f"rsi_momentum_crypto_{CURRENCY.lower()}"
STRATEGY_NAME += "_quote" if QUOTE_BASED else ""
STRATEGY_NAME += "_profitlock" if PROFIT_LOCK_ENABLED else ""
STRATEGY_NAME += f"_rsi{int(RSI_CE_THRESHOLD)}" if RSI_THRESHOLD_CHANGED else ""
STRATEGY_NAME += "_lock" if DAILY_LOSS_LOCK_ENABLED else ""


def _seed_candles(currency):
    """
    Real historical 5-min BTC-PERPETUAL/ETH-PERPETUAL bars (see
    crypto_options_backtest.py's own module docstring for why the
    perpetual, not the index itself, is used - Deribit's tradingview
    endpoint rejects instrument_name="btc_usd" outright), so RSI is
    available from the first live tick instead of needing ~75 minutes
    of live ticks to warm up MIN_CANDLES_FOR_RSI candles from scratch -
    same reasoning as event_driven_runner.py's own _seed_candles() for
    the NIFTY/BankNifty engine.

    Returns None (not raises) on any fetch problem - RSI just stays
    unready until enough live ticks arrive, same graceful-degradation
    rule every other network-sourced signal in this project follows;
    a startup hiccup here must never block the engine from starting.
    """

    try:
        perpetual = "BTC-PERPETUAL" if currency.upper() == "BTC" else "ETH-PERPETUAL"
        now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
        start_ms = now_ms - CANDLE_SEED_HOURS * 3600 * 1000

        bars = get_tradingview_chart_data(perpetual, start_ms, now_ms, resolution_minutes=5)

        if len(bars) < MIN_CANDLES_FOR_RSI:
            print(f"Only {len(bars)} historical bars available - RSI will warm up live instead.")
            return None

        rows = [{"Open": close, "High": close, "Low": close, "Close": close} for _, close in bars]
        idx = [datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc) for ts, _ in bars]

        return pd.DataFrame(rows, index=idx)
    except Exception as error:
        print(f"Could not seed candles ({error}) - RSI will warm up live instead.")
        return None


def build_runner():
    """
    One real REST snapshot (spot + today's option chain) to pick the
    ATM CE/PE instrument pair, then a fresh/persisted portfolio loaded
    via strategy/crypto_tick_runner.py's own atomic load_portfolio().
    Same "network call, not pure logic" boundary this project always
    draws (see strategy/event_driven_runner.py's build_runners(), never
    unit-tested either) - every piece it hands off to (decide_fn, the
    runner class) already is tested.

    KNOWN LIMITATION, same one event_driven_runner.py's build_runners()
    already accepts for NIFTY/BankNifty: ATM is picked ONCE here, at
    startup, not re-derived as spot drifts - a fast-follow if this
    matters in practice once it's actually running.
    """

    spot = get_index_price(CURRENCY)
    instruments = get_instruments(CURRENCY)
    expiry, atm_strike, ce_symbol, pe_symbol = pick_atm_instruments(instruments, spot)

    print(f"ATM picked: {ce_symbol} / {pe_symbol} (strike {atm_strike}, spot {spot})")

    cfg = make_st2_threshold_event_cfg(index=CURRENCY, lot_size=1, initial_capital=INITIAL_CAPITAL,
                                        cost_fn=calculate_crypto_options_round_trip_cost,
                                        daily_profit_lock=PROFIT_LOCK_ENABLED,
                                        daily_profit_lock_pct=PROFIT_LOCK_PCT or 2.0,
                                        rsi_ce_threshold=RSI_CE_THRESHOLD,
                                        rsi_pe_threshold=RSI_PE_THRESHOLD,
                                        # Added 01-Sep-2026, user's own
                                        # explicit ask, applied to EVERY
                                        # crypto book unconditionally
                                        # (not opt-in per book like the
                                        # experiments above) - a real
                                        # risk-control fix, not a
                                        # performance experiment to A/B
                                        # test. See event_driven_engine.
                                        # py's own matching note.
                                        stop_at_zero_capital=True,
                                        daily_loss_lock=DAILY_LOSS_LOCK_ENABLED,
                                        max_consecutive_losses=MAX_CONSECUTIVE_LOSSES)
    portfolio = load_portfolio(STRATEGY_NAME, INITIAL_CAPITAL)

    return CryptoTickRunner(
        decide_fn=DECIDE_FN,
        cfg=cfg,
        portfolio=portfolio,
        underlying_index_name=CURRENCY,
        ce_symbol=ce_symbol,
        pe_symbol=pe_symbol,
        initial_candles=_seed_candles(CURRENCY),
        execution_backend=PaperExecutionBackend(),
        profit_lock_window_hours=PROFIT_LOCK_WINDOW_HOURS,
    )


def main():

    runner = build_runner()

    print(f"Starting {STRATEGY_NAME} - watching {runner.ce_symbol} / {runner.pe_symbol}")

    def _persist(action):
        # Local JSON stays the source of truth (see save_portfolio()'s
        # own docstring) - sync_portfolio() is purely an ADDITIONAL live
        # read-path for the mobile app, and degrades gracefully (never
        # raises) if Firebase isn't configured yet, same as strategy/
        # event_driven_runner.py's own save_all().
        print(f"[{STRATEGY_NAME}] {action}")
        save_portfolio(STRATEGY_NAME, runner.portfolio)
        sync_portfolio(STRATEGY_NAME, runner.portfolio)

    # Added 29-Aug-2026, at the user's own request - a live CE/PE
    # premium candlestick chart in crypto_app, same real-data (not
    # spot-approximated) chart strategy/event_driven_runner.py already
    # builds for the NIFTY side (strategy_ticks/strategy_candles paths,
    # see that module's own 21-Aug-2026 note). firebase_executor keeps
    # every sync call off this hot path - Deribit's ticker channel ticks
    # at 100ms, far faster than Fyers' ticks, so a blocking network call
    # per tick here would stall the WebSocket read loop badly (the exact
    # "blocking-Firebase-call latency bug" event_driven_runner.py's own
    # history already found once on the NIFTY side).
    firebase_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="firebase-sync")
    candle_aggregators = {"CE": LiveCandleAggregator(), "PE": LiveCandleAggregator()}

    def _sync_premium_tick(instrument_name, timestamp, usd_premium):
        if usd_premium is None:
            return

        leg = "CE" if instrument_name == runner.ce_symbol else "PE" if instrument_name == runner.pe_symbol else None
        if leg is None:
            return

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        firebase_executor.submit(
            sync_strategy_tick, STRATEGY_NAME, leg, {"ltp": usd_premium, "timestamp": timestamp_str}
        )

        agg = candle_aggregators[leg]
        if agg.on_tick(timestamp_str, usd_premium):
            firebase_executor.submit(sync_strategy_candles, STRATEGY_NAME, leg, agg.as_list())

    connect_and_run(
        runner, runner.ce_symbol, runner.pe_symbol, runner.underlying_index_name,
        on_action=_persist, on_tick=_sync_premium_tick,
    )


if __name__ == "__main__":
    main()
