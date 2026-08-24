import concurrent.futures
import datetime
import json
import os
import threading
import time

from strategy.fyers_options_engine import INDEX_CONFIG, _fetch_option_chain
from strategy.fyers_options_oi_footprint import _read_atm_oi_snapshot
from strategy.fyers_data import fyers_download
from strategy.event_driven_engine import (
    rsi_momentum_decide_fn, rsi_momentum_quote_decide_fn,
    make_st2_threshold_event_cfg, make_simple_st1_threshold_event_cfg,
    oi_footprint_decide_fn, make_oi_footprint_event_cfg,
)
from strategy.execution_backend import PaperExecutionBackend
from strategy.live_tick_harness import LiveTickRunner, OIFootprintTickRunner, handle_symbol_update_message
from strategy.tick_collector import LiveCandleAggregator

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Added 18-Aug-2026 - the production entry point that ties together
# everything built tonight (backtest_live_engine.py's decide_fn
# contract, event_driven_engine.py's 2 decide_fns, live_tick_harness.
# py's runners/aggregators) into one script that would actually run on
# the VPS once it exists. NOT deployable yet - no VPS, fyers_apiv3
# isn't installed on this local session (18-Aug's Visual C++ Build
# Tools finding), and the raw socket connection itself still can't be
# verified without a real live attempt (see live_tick_harness.py's own
# caveat). This is the remaining glue code-prep, same "prove the
# pattern, verify what's verifiable now" discipline as the rest of
# tonight's work.
#
# SEPARATE PORTFOLIO FILES, never touches the 63 existing live books
# (per this repo's "never modify a working module" rule) - these
# event-driven books are a NEW, parallel comparison, matching how
# every other variant in this project (_slcap, oi_footprint variants,
# etc.) was added as its own book rather than replacing an original.
#
# KNOWN LIMITATION, stated plainly rather than glossed over: ATM
# strike/symbols are picked ONCE at startup (build_runners()) via a
# fresh option-chain snapshot, not re-picked continuously. The
# original polling engine re-derives ATM fresh at every entry attempt
# (fyers_options_engine.py's _pick_atm_leg()) - if spot drifts far
# enough intraday that ATM shifts meaningfully BEFORE this runner's
# next restart, it would keep watching the now-stale strike until
# restarted. Acceptable for a first real-world test (ATM drift within
# a session is usually small relative to the strike step), but a real
# gap versus the original engine's behavior - flagged for whoever
# extends this before treating it as production-final.

PORTFOLIO_DIR = "reports"
SQUAREOFF_TIME = (15, 15)
RSI_SEED_PERIOD = "10d"
RSI_SEED_INTERVAL = "5m"
# Added 21-Aug-2026, alongside the refresh_oi_snapshots() wiring fix
# below - matches "the original polling engine's own cadence is fine"
# per that function's own docstring (the old engine's real-world
# oi_footprint checks ran on a 5-min external cron-job.org trigger -
# see .github/workflows/fyers_multi_strategy_options.yml's own "moved
# here (from the 5-min fyers_scheduled_..." comment). Frequent enough
# for OI buildup (not tick-level data to begin with), infrequent
# enough not to hammer the option-chain REST endpoint every few
# seconds for no real benefit.
OI_REFRESH_SECONDS = 5 * 60

# Distinct names from every existing live book - see module docstring.
STRATEGY_NAMES = {
    "st2_threshold": "st2_threshold_eventdriven",
    "simple_st1_threshold": "simple_st1_threshold_eventdriven",
    "oi_footprint_nifty": "oi_footprint_eventdriven_nifty",
    "oi_footprint_banknifty": "oi_footprint_eventdriven_banknifty",
    # Added 21-Aug-2026, user's own explicit ask after today's real
    # -Rs 22,949.63 stale-data incident (see event_driven_engine.py's
    # daily_profit_lock cfg note): a 2% daily-profit-lock variant
    # of each RSI-momentum book, running ALONGSIDE (not replacing) the
    # existing two - user explicitly asked to leave st2_threshold/
    # simple_st1_threshold themselves unchanged, matching this repo's
    # "add new functionality as separate engines" rule and the same
    # pattern the older polling engine already uses for its own
    # _slcap/_trailing2pct/_2pctlock variants (separate books, never a
    # mutation of the original).
    "st2_threshold_lock": "st2_threshold_lock_eventdriven",
    "simple_st1_threshold_lock": "simple_st1_threshold_lock_eventdriven",
    # Added 21-Aug-2026, same day, user's own explicit ask after real
    # depth-slippage analysis found the "_lock" books' LTP-based PnL
    # overstates realistic (bid/ask) PnL by ~87-91% on a thin ATM book
    # - 6 more variants (2 per daily-profit-lock tier: 2%/1%/0.5%),
    # running rsi_momentum_quote_decide_fn instead of rsi_momentum_
    # decide_fn (see that function's own docstring) so Target/Stop-Loss
    # trigger off real bid/ask from the start, not LTP reconstructed
    # afterward. Alongside, not replacing, the existing "_lock" books -
    # same "separate books, never mutate the original" rule as above.
    "st2_threshold_lock_quote2pct": "st2_threshold_lock_quote2pct_eventdriven",
    "simple_st1_threshold_lock_quote2pct": "simple_st1_threshold_lock_quote2pct_eventdriven",
    "st2_threshold_lock_quote1pct": "st2_threshold_lock_quote1pct_eventdriven",
    "simple_st1_threshold_lock_quote1pct": "simple_st1_threshold_lock_quote1pct_eventdriven",
    "st2_threshold_lock_quote0pt5pct": "st2_threshold_lock_quote0pt5pct_eventdriven",
    "simple_st1_threshold_lock_quote0pt5pct": "simple_st1_threshold_lock_quote0pt5pct_eventdriven",
}


def _portfolio_path(name):
    return os.path.join(PORTFOLIO_DIR, f"fyers_options_{name}_portfolio.json")


def load_portfolio(name, initial_capital=100000):
    """
    FIXED 24-Aug-2026 - real incident, took the WHOLE event-driven
    engine down live: save_portfolio() below used to open(path, "w"),
    which truncates the file to 0 bytes BEFORE writing the new content
    - a `systemctl restart` (SIGTERM) landing in that exact window
    during today's deploy left simple_st1_threshold_lock_quote1pct's
    portfolio file at 0 bytes. This function then raised
    json.JSONDecodeError trying to parse it, which propagated all the
    way up through build_runners() and crashed EVERY book, not just
    the one with the bad file - confirmed live via journalctl (the
    traceback's own last frame was this file's old, non-defensive
    `return json.load(f)`). That single book's real trade history for
    the day (4 trades, +Rs 1,498) was unrecoverable - the file was
    genuinely empty, not just malformed - restored to a fresh empty
    portfolio to get the engine back up, real data loss accepted.

    Two independent fixes for two independent risks: save_portfolio()
    now writes atomically (temp file + os.replace(), which is atomic
    on both POSIX and Windows) so a killed process can never again
    leave a truncated file on disk - THIS is the real fix, preventing
    the incident from recurring. This function ALSO now degrades
    gracefully instead of crashing if a portfolio file is ever empty
    or unparseable anyway (a corrupt disk, a manual edit mistake, or
    any other cause the atomic-write fix doesn't cover) - one bad
    book's history is lost, but the other 11 keep trading rather than
    the whole engine going down with them.
    """

    path = _portfolio_path(name)

    if not os.path.exists(path):
        return {"Cash": initial_capital, "Position": None, "Closed Trades": []}

    with open(path, "r") as f:
        content = f.read()

    if not content.strip():
        print(f"WARNING: {path} is empty (likely an interrupted write) - "
              f"starting {name} fresh. Any real trade history in this file is lost.")
        return {"Cash": initial_capital, "Position": None, "Closed Trades": []}

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        print(f"WARNING: {path} is corrupt ({error}) - "
              f"starting {name} fresh. Any real trade history in this file is lost.")
        return {"Cash": initial_capital, "Position": None, "Closed Trades": []}


def save_portfolio(name, portfolio):
    """
    Writes atomically (temp file + os.replace()) - see load_portfolio()'s
    own 24-Aug-2026 note for the real incident this fixes. A process
    killed mid-write now leaves either the OLD complete file or the
    NEW complete file, never a truncated one - os.replace() is atomic
    on both POSIX and Windows, unlike a plain open(path, "w") which
    truncates before the new content is ever written.
    """

    os.makedirs(PORTFOLIO_DIR, exist_ok=True)

    path = _portfolio_path(name)
    tmp_path = path + ".tmp"

    with open(tmp_path, "w") as f:
        json.dump(portfolio, f, indent=2)

    os.replace(tmp_path, path)


def pick_atm_symbols(index):
    """
    One fresh option-chain snapshot - returns (spot, atm_strike,
    ce_symbol, pe_symbol). Reuses fyers_options_engine.py's own
    _fetch_option_chain() and INDEX_CONFIG, same ATM formula every
    other strategy in this project already uses - not re-derived here.
    """

    index_cfg = INDEX_CONFIG[index]
    chain_cfg = {"underlying_symbol": index_cfg["underlying_symbol"]}

    data = _fetch_option_chain(chain_cfg)
    legs = data.get("optionsChain", [])

    spot = next((leg.get("ltp") for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        raise RuntimeError(f"Could not read spot price from {index}'s option chain response")

    atm_strike = round(spot / index_cfg["strike_step"]) * index_cfg["strike_step"]

    ce_symbol = next((leg.get("symbol") for leg in legs
                       if leg.get("strike_price") == atm_strike and leg.get("option_type") == "CE"), None)
    pe_symbol = next((leg.get("symbol") for leg in legs
                       if leg.get("strike_price") == atm_strike and leg.get("option_type") == "PE"), None)

    if ce_symbol is None or pe_symbol is None:
        raise RuntimeError(f"ATM strike {atm_strike} CE/PE not found in {index}'s option chain response")

    return spot, atm_strike, ce_symbol, pe_symbol


def _seed_candles(index):
    """Real historical 5m candles, for CandleAggregator's initial_candles
    - so RSI is available from the first live tick instead of needing
    ~70 minutes of live ticks to warm up 15 candles from scratch. Same
    source (fyers_download) fyers_options_engine.py's _get_direction()
    already uses for the polling engine's own RSI."""

    index_cfg = INDEX_CONFIG[index]
    frame = fyers_download(index_cfg["index_symbol_for_rsi"], period=RSI_SEED_PERIOD, interval=RSI_SEED_INTERVAL)

    return frame[["Open", "High", "Low", "Close"]] if frame is not None else None


def _previous_close(index):
    """
    Added 20-Aug-2026 - the previous trading day's real daily close, for
    indicators/circuit_band.py's proactive circuit-proximity gate (see
    event_driven_engine.py's _near_circuit()). Last COMPLETE daily
    candle from a short recent window - this only ever runs before/at
    market open (build_runners() is called once at startup), so the
    most recent daily candle Fyers returns is always yesterday's real
    close, never today's still-forming one.

    Returns None (not raises) on any fetch problem - the circuit gate
    treats None as "can't check", same graceful-degradation rule as
    every other network-sourced signal in this module (RSI seed
    candles, ATM symbols) - a startup network hiccup on this one
    feature must never block the whole engine from starting.
    """

    try:
        index_cfg = INDEX_CONFIG[index]
        frame = fyers_download(index_cfg["index_symbol_for_rsi"], period="5d", interval="1d")

        if frame is None or frame.empty:
            return None

        return float(frame["Close"].iloc[-1])
    except Exception as error:
        print(f"Could not fetch previous close for {index} (circuit gate will be skipped): {error}")
        return None


class MultiStrategyRouter:
    """
    Routes one incoming WebSocket tick to every runner subscribed to
    that symbol - the piece a single-strategy connect_and_run() didn't
    need, since production runs all 4 strategies over ONE real
    connection (Fyers' own subscription capacity note from 17-Aug's
    research covers up to 200 symbols - this project needs at most a
    handful: 2 underlyings + up to 4 ATM CE/PE pairs). Pure routing
    logic, no network - fully unit-tested (see tests/test_event_
    driven_runner.py).
    """

    def __init__(self):
        self._symbol_runners = {}

    def register(self, symbol, runner):
        self._symbol_runners.setdefault(symbol, []).append(runner)

    def all_symbols(self):
        return list(self._symbol_runners.keys())

    def runners_for(self, symbol):
        """
        Added 21-Aug-2026, alongside the on_message() latency fix in
        main() below - which runners were actually touched by a given
        symbol's tick, so the caller can save/sync only those instead
        of blindly re-touching every registered runner on every single
        tick (see save_all()'s own 21-Aug-2026 note for the real
        incident this fixes).
        """

        return list(self._symbol_runners.get(symbol, []))

    def route(self, message):
        """
        Dispatches one raw Fyers SymbolUpdate message dict to every
        runner registered for that symbol, via live_tick_harness.py's
        already-tested handle_symbol_update_message() - no second copy
        of that parsing logic.

        Returns the list of actions produced (one per matching runner).
        """

        symbol = message.get("symbol")
        actions = []

        for runner in self._symbol_runners.get(symbol, []):
            actions.append(handle_symbol_update_message(message, runner))

        return actions


def build_runners(execution_backend=None):
    """
    Constructs today's 4 event-driven runners (2 LiveTickRunner for the
    RSI-momentum books, 2 OIFootprintTickRunner for oi_footprint), each
    loaded from its own real (persisted) portfolio, seeded with real
    historical candles, and registered on a MultiStrategyRouter.

    Calls the real Fyers option-chain REST endpoint (via pick_atm_
    symbols/_seed_candles) - NOT unit-tested directly, same "network
    call, not pure logic" boundary this project has always drawn (see
    fyers_options_engine.py's own _check_position/_open_position,
    never unit-tested either) - but every piece it hands off to
    (decide_fn, runner classes, the router) already is.

    execution_backend : defaults to None -> PaperExecutionBackend()
        (strategy/execution_backend.py), same object passed to every
        runner - see that module's docstring for why this exists.

    Returns
    -------
    router : MultiStrategyRouter
    runners : dict of {STRATEGY_NAMES key: runner instance}
    """

    execution_backend = execution_backend or PaperExecutionBackend()

    router = MultiStrategyRouter()
    runners = {}

    # Added 21-Aug-2026, alongside the 2 new daily-profit-lock variants
    # below - pick_atm_symbols()/_seed_candles()/_previous_close() are
    # each one real network call; with 2 NEW cfg variants added for the
    # SAME index (NIFTY), calling them fresh per loop iteration would
    # double NIFTY's real API calls at every startup for no reason,
    # since the plain and locked variants share the same ATM strike/
    # candles/previous-close by design. Cached per index, computed once
    # on first use.
    _atm_cache = {}
    _seed_cache = {}
    _prev_close_cache = {}

    def _atm_for(index):
        if index not in _atm_cache:
            _atm_cache[index] = pick_atm_symbols(index)
        return _atm_cache[index]

    def _seed_for(index):
        if index not in _seed_cache:
            _seed_cache[index] = _seed_candles(index)
        return _seed_cache[index]

    def _prev_close_for(index):
        if index not in _prev_close_cache:
            _prev_close_cache[index] = _previous_close(index)
        return _prev_close_cache[index]

    for index, cfg_builder, decide_fn, key, cfg_overrides in (
        # Added 21-Aug-2026 - daily_loss_lock/max_consecutive_losses,
        # ported from fyers_options_engine.py (already proven there),
        # after these exact two books whipsawed for real today (81/106
        # trades, 71-79% Stop-Loss - see event_driven_engine.py's
        # daily_loss_lock cfg note). The "_lock"/"_lock_quote*" variants
        # below keep their existing daily_profit_lock gate unchanged -
        # a different failure mode (they already stop after one win).
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_decide_fn, "st2_threshold",
         {"daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_decide_fn, "simple_st1_threshold",
         {"daily_loss_lock": True, "max_consecutive_losses": 2}),
        # 2% daily-profit-lock variants - see STRATEGY_NAMES'
        # own 21-Aug-2026 note. Same cfg_builder/decide_fn/symbols as
        # the plain book above it - only daily_profit_lock differs -
        # registered on the SAME NIFTY CE/PE/spot symbols below
        # (MultiStrategyRouter.register() already supports multiple
        # runners per symbol, dispatching a tick to all of them).
        #
        # daily_loss_lock/max_consecutive_losses ADDED 24-Aug-2026 -
        # these 2 books were the only remaining RSI-momentum-family
        # books still missing the breaker (already on the un-locked
        # pair since 21-Aug, and on all 6 "_lock_quote*" books earlier
        # today). Backtested against today's own real trades first
        # (user's own explicit ask) - the breaker changes NOTHING for
        # either book's actual result today (Rs 3,396.45/Rs 3,078.38,
        # identical with or without it - neither ever hit 2 consecutive
        # losses, daily_profit_lock stopped them first). Added anyway,
        # user's own explicit call: same daily_profit_lock-only gate
        # already failed structurally-identical siblings 3 times today
        # (simple_st1_threshold_lock_quote2pct, oi_footprint_banknifty,
        # and the original 21-Aug whipsaw) - these two were protected
        # by today's favorable trade sequence, not by anything
        # structural, so there is no real downside to enabling a purely
        # protective, already-proven gate that happened not to bind
        # today.
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_decide_fn, "st2_threshold_lock",
         {"daily_profit_lock": True, "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_decide_fn, "simple_st1_threshold_lock",
         {"daily_profit_lock": True, "daily_loss_lock": True, "max_consecutive_losses": 2}),
        # 21-Aug-2026, same day - quote-based (bid/ask, not LTP)
        # siblings of the two "_lock" books above, at 3 daily-profit-
        # lock tiers (2%/1%/0.5%) - see STRATEGY_NAMES' own note and
        # rsi_momentum_quote_decide_fn's own docstring.
        #
        # daily_loss_lock/max_consecutive_losses ADDED 24-Aug-2026, real
        # incident found live the same day: daily_profit_lock only ever
        # watches for PROFIT reaching its threshold - it never stops a
        # book that's simply losing, since a book that never reaches
        # +2% for the day never trips the lock at all. simple_st1_
        # threshold_lock_quote2pct hit exactly this - 53 real trades,
        # 40 losses, -Rs 45,880 by mid-morning, never once close to its
        # own +2% lock. Backtested the SAME consecutive-loss breaker
        # already proven on st2_threshold/simple_st1_threshold (21-Aug)
        # against these 53 real trades: N=2 cut the loss to -Rs 4,107
        # (10x better than no breaker, and clearly best among N=2/3/4/5
        # tried) - user's own explicit choice after seeing that table.
        # Added to all 6 "_lock_quote*" books, not just the one that
        # actually misbehaved today - the other 5 stopped early via
        # daily_profit_lock today (good luck, not because they were
        # structurally safe), so the same uncontained-loss risk exists
        # in all of them.
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_quote_decide_fn, "st2_threshold_lock_quote2pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 2.0,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_quote_decide_fn,
         "simple_st1_threshold_lock_quote2pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 2.0,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_quote_decide_fn, "st2_threshold_lock_quote1pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 1.0,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_quote_decide_fn,
         "simple_st1_threshold_lock_quote1pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 1.0,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_quote_decide_fn, "st2_threshold_lock_quote0pt5pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 0.5,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_quote_decide_fn,
         "simple_st1_threshold_lock_quote0pt5pct",
         {"daily_profit_lock": True, "daily_profit_lock_pct": 0.5,
          "daily_loss_lock": True, "max_consecutive_losses": 2}),
    ):
        name = STRATEGY_NAMES[key]
        index_cfg = INDEX_CONFIG[index]
        cfg = cfg_builder(index=index, lot_size=index_cfg["lot_size"], **cfg_overrides)

        spot, atm_strike, ce_symbol, pe_symbol = _atm_for(index)

        runner = LiveTickRunner(
            decide_fn=decide_fn,
            cfg=cfg,
            portfolio=load_portfolio(name, cfg["initial_capital"]),
            underlying_symbol=index_cfg["underlying_symbol"],
            ce_symbol=ce_symbol,
            pe_symbol=pe_symbol,
            squareoff_time=SQUAREOFF_TIME,
            initial_candles=_seed_for(index),
            execution_backend=execution_backend,
            previous_close=_prev_close_for(index),
        )

        router.register(index_cfg["underlying_symbol"], runner)
        router.register(ce_symbol, runner)
        router.register(pe_symbol, runner)
        runners[key] = runner

    for index, key in (("NIFTY", "oi_footprint_nifty"), ("BANKNIFTY", "oi_footprint_banknifty")):
        name = STRATEGY_NAMES[key]
        index_cfg = INDEX_CONFIG[index]
        # hybrid_sl_cap_pct=2.0 - added 18-Aug-2026, same choice already
        # made by default for st2_threshold/simple_st1_threshold above.
        # oi_footprint's plain Rs 1,500 fixed Stop-Loss is exactly the
        # book that suffered real, live overshoot losses today (3
        # consecutive Stop-Loss exits between 04:04-04:12 IST losing
        # Rs 5,221/7,210/7,002 against an intended Rs 1,500 cap - the
        # periodic-check-not-tick-by-tick issue this whole VPS migration
        # exists to fix). Matches the hybrid-cap backtest already run
        # against oi_footprint's real trade history (see PROJECT_STATUS.
        # md/14-Aug's oi_footprint deep dive + its 18-Aug update): NIFTY
        # -Rs 47,607 actual -> +Rs 69,490 hybrid-capped, BANKNIFTY
        # -Rs 6,067 -> +Rs 4,839. The event-driven engine's tick-by-tick
        # checking should make the overshoot itself far smaller, but the
        # hybrid cap is a second, independent line of defense - no
        # reason to run this book without it once the fix is this cheap
        # (one flag, already implemented and tested).
        # daily_loss_lock/max_consecutive_losses=2 - added 24-Aug-2026,
        # same N=2 breaker already proven on st2_threshold/simple_st1_
        # threshold (21-Aug) and the 6 "_lock_quote*" books (24-Aug),
        # after oi_footprint_banknifty whipsawed 141 real trades today
        # (69 losses, -Rs 23,952) with no breaker at all - see
        # oi_footprint_decide_fn's own matching note.
        cfg = make_oi_footprint_event_cfg(index=index, lot_size=index_cfg["lot_size"], hybrid_sl_cap_pct=2.0,
                                           daily_loss_lock=True, max_consecutive_losses=2)

        spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)

        runner = OIFootprintTickRunner(
            decide_fn=oi_footprint_decide_fn,
            cfg=cfg,
            portfolio=load_portfolio(name, cfg["initial_capital"]),
            ce_symbol=ce_symbol,
            pe_symbol=pe_symbol,
            squareoff_time=SQUAREOFF_TIME,
            execution_backend=execution_backend,
            previous_close=_previous_close(index),
        )

        router.register(ce_symbol, runner)
        router.register(pe_symbol, runner)
        runners[key] = runner

    return router, runners


def refresh_oi_snapshots(runners):
    """
    Call periodically (the original polling engine's own cadence is
    fine - OI doesn't need tick-level freshness, see live_tick_
    harness.py's OIBuildupTracker docstring) for the 2 oi_footprint
    runners - fetches a real option-chain snapshot via fyers_options_
    oi_footprint.py's own _read_atm_oi_snapshot() (imported, not
    duplicated) and feeds it in.

    FIXED 21-Aug-2026 - real bug caught live: this function was never
    actually CALLED anywhere (grepped the whole codebase - only its own
    definition existed, no caller, no scheduled thread) - see main()'s
    matching fix below. Both oi_footprint books had been running since
    20-Aug with zero trades, ever (Cash still exactly the untouched
    initial_capital) - their OIBuildupTracker.latest_signal never had a
    chance to become anything but None, so oi_footprint_decide_fn's own
    first check ("SKIPPED (no meaningful OI buildup)") always fired.
    """

    now = datetime.datetime.now(IST)  # FIXED 21-Aug-2026 alongside the
    # above - was naive datetime.datetime.now() (this VPS's system
    # clock is UTC, see doc/PROJECT_STATUS.md's 21-Aug cron-timezone
    # entry), while every "Entry Time"/is_past_squareoff() comparison
    # this timestamp eventually reaches (via on_oi_snapshot() ->
    # _maybe_decide() -> _past_squareoff()) assumes an already-IST
    # value - a naive-UTC "now" here would misjudge squareoff/carried-
    # over-position checks by 5:30 hours, the same class of bug
    # strategy/squareoff.py's own module docstring already documents a
    # real incident for.

    for key, index in (("oi_footprint_nifty", "NIFTY"), ("oi_footprint_banknifty", "BANKNIFTY")):
        runner = runners.get(key)

        if runner is None:
            continue

        index_cfg = INDEX_CONFIG[index]
        oi_cfg = {"underlying_symbol": index_cfg["underlying_symbol"], "strike_step": index_cfg["strike_step"]}
        snapshot = _read_atm_oi_snapshot(oi_cfg)

        if snapshot is not None:
            runner.on_oi_snapshot(now, snapshot["spot"], snapshot["strike"], snapshot["ce_oi"], snapshot["pe_oi"])


# Added 18-Aug-2026 - connection-level monitoring, at the user's
# request while reviewing VPS readiness. The fyers_apiv3 SDK already
# self-heals transient WebSocket drops (reconnect=True, passed to
# FyersDataSocket in main() below) - on_error/on_close firing does NOT
# necessarily mean the engine is down, most are short blips the SDK
# recovers from within seconds. Alerting on every single one would be
# noise, not signal, so this rate-limits to at most one push per
# _CONNECTION_ALERT_COOLDOWN_SECONDS - a real prolonged outage still
# surfaces quickly, a flapping-then-recovering connection doesn't spam.
#
# App push notification ONLY (report/push_notifier.py's
# send_push_notification(), not report/notifier.py's notify()) - the
# user does not use Telegram, so this deliberately skips that channel
# rather than sending an alert through a channel nobody's watching.
# Reuses the SAME Firebase Cloud Messaging "trade_alerts" topic the
# app already subscribes to (mobile_app/lib/main.dart) - no new
# mobile app code needed, this alert just shows up as another push.
#
# This is DIFFERENT from, and does not replace, the systemd-level
# OnFailure= alert on the process actually dying (see deploy/turion-
# event-driven.service's OnFailure= + deploy/turion-engine-alert.
# service) - that covers the process getting killed outright; this
# covers the socket flapping while the process stays alive.
_CONNECTION_ALERT_COOLDOWN_SECONDS = 900


def _should_send_connection_alert(last_alert_at, now):
    """
    Pure/testable rate-limit decision, deliberately kept separate from
    the actual send_push_notification() call (which needs live
    Firebase credentials and can't be unit-tested) - same "extract the
    testable decision, keep the wiring thin" split this module already
    used for connect_and_run()'s message-parsing logic. True if no
    alert has been sent yet this run (last_alert_at is None), or if
    `now` is at least the cooldown past `last_alert_at`.
    """

    if last_alert_at is None:
        return True

    return (now - last_alert_at).total_seconds() >= _CONNECTION_ALERT_COOLDOWN_SECONDS


def save_all(runners, keys=None, firebase_executor=None):
    """
    Local JSON stays the source of truth (same file this project's own
    verification/replay tooling reads) - the Firebase Realtime Database
    push is purely an ADDITIONAL live read-path for the app (see report/
    firebase_realtime_sync.py's module docstring), never a replacement.
    sync_portfolio() degrades gracefully (never raises, returns False)
    if Firebase isn't configured yet, so this is safe to always call.

    keys - added 21-Aug-2026: iterable of runner keys to save/sync,
    default None = every runner (the original behavior). Real bug
    found live: main()'s on_message() called this for ALL runners on
    EVERY single tick regardless of which runner (if any) that tick
    actually touched - see MultiStrategyRouter.runners_for()'s own
    note for the fix on the caller side.

    firebase_executor - added 21-Aug-2026: submit sync_portfolio() (a
    real cross-region REST call, VPS-to-Firebase) to this executor
    instead of calling it synchronously and blocking the caller on a
    network round-trip. None (default) keeps the old synchronous call
    - confirmed live as the dominant cause of a real tick-latency
    incident (median 1.5s, up to 46.5s, across 92,124 measured ticks
    in run_tick_collector.py's own archive, same architecture) - see
    run_tick_collector.py's FIREBASE_SYNC_WORKERS comment for the full
    detail. A snapshot dict is built before submitting (not the live
    runner.portfolio reference) so a later tick mutating Position/
    Closed Trades can't race the background write.
    """

    from report.firebase_realtime_sync import sync_portfolio

    for key in (keys if keys is not None else runners.keys()):
        runner = runners[key]
        name = STRATEGY_NAMES[key]
        save_portfolio(name, runner.portfolio)

        if firebase_executor is None:
            sync_portfolio(name, runner.portfolio)
            continue

        snapshot = {
            "Cash": runner.portfolio["Cash"],
            "Position": dict(runner.portfolio["Position"]) if runner.portfolio["Position"] else None,
            "Closed Trades": list(runner.portfolio.get("Closed Trades", [])),
        }
        firebase_executor.submit(sync_portfolio, name, snapshot)


def main(access_token, execution_backend=None):
    """
    NOT LIVE-TESTED - see module docstring's caveats (no VPS, fyers_
    apiv3 not installed locally, real socket connection unverified).
    Written to match the same connect_and_run() pattern already
    verified against real Fyers SDK documentation - one socket, one
    on_message callback, routed via MultiStrategyRouter instead of a
    single runner. Kept deliberately thin - all real logic lives in
    already-tested code this function only wires together.

    execution_backend : defaults to None -> PaperExecutionBackend(),
        forwarded straight to build_runners() - see strategy/
        execution_backend.py's module docstring. run_event_driven_
        engine.py (the VPS entry point) is what actually resolves
        TURION_EXECUTION_MODE and passes the real object here.
    """

    from fyers_apiv3.FyersWebsocket import data_ws
    from report.push_notifier import send_push_notification
    from report.firebase_realtime_sync import sync_strategy_tick, sync_strategy_candles

    router, runners = build_runners(execution_backend)

    # See save_all()'s own 21-Aug-2026 note (firebase_executor param) -
    # bounded, not a raw thread per tick, so a tick burst can't spawn
    # unboundedly more outstanding Firebase writes than can actually
    # drain. runner_keys is the reverse of `runners` (id(runner) ->
    # key), built once here rather than per tick, so on_message() can
    # turn router.runners_for(symbol)'s runner OBJECTS back into the
    # STRATEGY_NAMES keys save_all() needs.
    firebase_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=4, thread_name_prefix="firebase-sync"
    )
    runner_keys = {id(runner): key for key, runner in runners.items()}

    # Added 21-Aug-2026, user's own request: a live option-PREMIUM chart
    # (Entry/Target/Stop-Loss overlaid, exact - not the earlier-discussed
    # spot-price approximation, matching how a real broker app charts an
    # option position against its own premium) for a specific book's
    # CURRENT position. One CE and one PE aggregator per runner - synced
    # regardless of which leg is actually open, so a fresh position
    # (possibly the OTHER leg) never hits a cold chart. Separate from
    # run_tick_collector.py's own index-level/SPOT candle_aggregators -
    # this is per-strategy, per-leg (a strategy's own ATM strike can
    # differ from that process's independent ATM pick for the same
    # index).
    strategy_candle_aggregators = {
        key: {"CE": LiveCandleAggregator(), "PE": LiveCandleAggregator()} for key in runners
    }

    _last_connection_alert = {"time": None}

    def _alert_connection_issue(kind, message):
        now = datetime.datetime.now()
        if _should_send_connection_alert(_last_connection_alert["time"], now):
            _last_connection_alert["time"] = now
            send_push_notification(
                "TURION Engine - Connection Issue",
                f"Event-driven engine WebSocket {kind}: {message}. "
                f"Check the VPS if this keeps repeating.",
            )

    def on_message(message):
        # FIXED 21-Aug-2026 - real bug caught live: this used to call
        # save_all(runners) with no `keys` filter and no executor - re-
        # saving/re-syncing ALL 6 runners, including a blocking Firebase
        # write per runner, on EVERY tick regardless of whether that
        # tick touched them at all. touched_keys narrows this to only
        # the runner(s) actually registered for this tick's symbol
        # (almost always 1, occasionally more per MultiStrategyRouter's
        # own multi-runner-per-symbol support); firebase_executor moves
        # the network part off this hot path entirely. See save_all()'s
        # own docstring for the full real-incident detail.
        symbol = message.get("symbol")
        touched = router.runners_for(symbol)
        touched_keys = [runner_keys[id(runner)] for runner in touched]
        router.route(message)
        save_all(runners, keys=touched_keys, firebase_executor=firebase_executor)

        # Added 21-Aug-2026 - see strategy_candle_aggregators' own note
        # above. Only a real CE/PE tick (not the underlying spot) feeds
        # a strategy's own premium chart; only sync a candle on an
        # actual close (once/min/leg/strategy, not per tick - a per-tick
        # sync here would reintroduce the blocking-Firebase-call latency
        # bug fixed earlier the same day).
        ltp = message.get("ltp")
        if ltp is not None:
            timestamp = datetime.datetime.fromtimestamp(
                message.get("exch_feed_time", message.get("last_traded_time")), tz=IST
            )
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            # vol_traded_today - added 21-Aug-2026 for chart volume bars.
            # Real traded volume (unlike the underlying index, an option
            # contract genuinely has one) - see LiveCandleAggregator.
            # on_tick()'s own note for how a per-candle figure gets
            # derived from this cumulative reading.
            volume = message.get("vol_traded_today")

            for runner, key in zip(touched, touched_keys):
                leg = "CE" if symbol == runner.ce_symbol else "PE" if symbol == runner.pe_symbol else None
                if leg is None:
                    continue

                name = STRATEGY_NAMES[key]
                firebase_executor.submit(
                    sync_strategy_tick, name, leg, {"ltp": ltp, "timestamp": timestamp_str, "volume": volume}
                )

                agg = strategy_candle_aggregators[key][leg]
                if agg.on_tick(timestamp_str, ltp, volume):
                    firebase_executor.submit(sync_strategy_candles, name, leg, agg.as_list())

    def on_error(message):
        print(f"[fyers websocket error] {message}")
        _alert_connection_issue("error", message)

    def on_close(message):
        print(f"[fyers websocket closed] {message}")
        _alert_connection_issue("closed", message)

    def on_open():
        socket.subscribe(symbols=router.all_symbols(), data_type="SymbolUpdate")
        socket.keep_running()

    socket = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=on_open,
        on_close=on_close,
        on_error=on_error,
        on_message=on_message,
    )

    # FIXED 21-Aug-2026 - real bug caught live: refresh_oi_snapshots()
    # existed, was fully wired to feed a real OI snapshot into both
    # oi_footprint runners, but was never actually CALLED anywhere in
    # this module - no thread, no scheduled trigger. Both oi_footprint
    # books had been running since 20-Aug with zero trades ever as a
    # direct result (OIBuildupTracker.latest_signal stuck at None
    # forever, so oi_footprint_decide_fn's first check always fired).
    # Same daemon-thread-with-sleep-loop pattern run_tick_collector.py
    # already uses for its own ATM re-check - one failed poll must not
    # kill the whole loop, matching that file's own try/except-and-
    # continue reasoning.
    def oi_refresh_loop():
        while True:
            time.sleep(OI_REFRESH_SECONDS)
            try:
                refresh_oi_snapshots(runners)
                # Added 21-Aug-2026 - a real, on-the-ground debugging gap
                # found live: refresh_oi_snapshots() succeeding is
                # completely silent (no print), making it indistinguishable
                # in the logs from the thread never having run at all -
                # exactly the ambiguity that made THIS bug take a manual
                # SSH diagnostic to confirm was actually fixed. One
                # confirmation line per successful cycle costs nothing at
                # a 5-min cadence and closes that gap for good.
                print(f"OI snapshot refresh OK ({datetime.datetime.now(IST).strftime('%H:%M:%S')} IST)")
            except Exception as error:
                print(f"OI snapshot refresh failed (continuing on the old signal): {error}")

    threading.Thread(target=oi_refresh_loop, daemon=True).start()

    socket.connect()

    # FIXED 21-Aug-2026 - see run_tick_collector.py's matching fix for
    # the full real-incident detail (identical root cause, identical
    # symptom: "cannot schedule new futures after interpreter shutdown"
    # on every firebase_executor.submit() call). FyersDataSocket.
    # connect() doesn't block, so without this, main()'s script finished
    # right after connect() returned and Python started real interpreter
    # shutdown seconds into every run - the OS process stayed alive only
    # because a non-daemon SDK thread blocked threading._shutdown()
    # forever, but concurrent.futures' own atexit hook had already fired
    # by then, permanently breaking new executor submissions.
    while True:
        time.sleep(3600)
