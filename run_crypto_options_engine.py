import datetime
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
# See run_event_driven_engine.py's own matching note - under systemd,
# stdout isn't a TTY, so Python defaults to full block buffering
# instead of line buffering, which would sit every print() unflushed
# for a long time rather than reaching `journalctl` promptly.

from report.firebase_realtime_sync import sync_portfolio
from strategy.crypto_tick_runner import CryptoTickRunner, load_portfolio, save_portfolio
from strategy.deribit_data import (
    get_index_price, get_instruments, get_tradingview_chart_data, pick_atm_instruments, connect_and_run,
)
from strategy.event_driven_engine import rsi_momentum_decide_fn, make_st2_threshold_event_cfg
from strategy.execution_backend import PaperExecutionBackend
from strategy.live_tick_harness import MIN_CANDLES_FOR_RSI

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
# "try the current strategy first" rule - already backtest-validated
# against real historical Deribit data (crypto_options_backtest.py: 16
# trades, 50% win rate, net +$7,716 on $10,000 over a real 7-day
# window) before this live-wiring step was written.
#
# ONE book only for now (BTC) - per the plan's own "no multi-book
# proliferation, one BTC book first" rule - so this deliberately skips
# strategy/event_driven_runner.py's MultiStrategyRouter (built for
# routing one WebSocket connection's ticks across several concurrent
# runners); a single runner + connect_and_run()'s own on_action hook
# is simpler and sufficient until ETH is added as a genuinely second,
# concurrent connect_and_run() process.
#
# NOT LIVE-TESTED beyond this session's own manual WebSocket
# verification (see strategy/deribit_data.py's connect_and_run()
# docstring) - actually running this needs the standalone VM from
# Phase 4 of the plan, which doesn't exist yet.

CURRENCY = "BTC"
STRATEGY_NAME = "rsi_momentum_crypto_btc"
INITIAL_CAPITAL = 10000.0
CANDLE_SEED_HOURS = 12  # comfortably more than MIN_CANDLES_FOR_RSI * 5min needs


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

    cfg = make_st2_threshold_event_cfg(index=CURRENCY, lot_size=1, initial_capital=INITIAL_CAPITAL)
    portfolio = load_portfolio(STRATEGY_NAME, INITIAL_CAPITAL)

    return CryptoTickRunner(
        decide_fn=rsi_momentum_decide_fn,
        cfg=cfg,
        portfolio=portfolio,
        underlying_index_name=CURRENCY,
        ce_symbol=ce_symbol,
        pe_symbol=pe_symbol,
        initial_candles=_seed_candles(CURRENCY),
        execution_backend=PaperExecutionBackend(),
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

    connect_and_run(runner, runner.ce_symbol, runner.pe_symbol, runner.underlying_index_name, on_action=_persist)


if __name__ == "__main__":
    main()
