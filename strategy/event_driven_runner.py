import datetime
import json
import os

from strategy.fyers_options_engine import INDEX_CONFIG, _fetch_option_chain
from strategy.fyers_options_oi_footprint import _read_atm_oi_snapshot
from strategy.fyers_data import fyers_download
from strategy.event_driven_engine import (
    rsi_momentum_decide_fn, make_st2_threshold_event_cfg, make_simple_st1_threshold_event_cfg,
    oi_footprint_decide_fn, make_oi_footprint_event_cfg,
)
from strategy.live_tick_harness import LiveTickRunner, OIFootprintTickRunner, handle_symbol_update_message

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

# Distinct names from every existing live book - see module docstring.
STRATEGY_NAMES = {
    "st2_threshold": "st2_threshold_eventdriven",
    "simple_st1_threshold": "simple_st1_threshold_eventdriven",
    "oi_footprint_nifty": "oi_footprint_eventdriven_nifty",
    "oi_footprint_banknifty": "oi_footprint_eventdriven_banknifty",
}


def _portfolio_path(name):
    return os.path.join(PORTFOLIO_DIR, f"fyers_options_{name}_portfolio.json")


def load_portfolio(name, initial_capital=100000):

    path = _portfolio_path(name)

    if not os.path.exists(path):
        return {"Cash": initial_capital, "Position": None, "Closed Trades": []}

    with open(path, "r") as f:
        return json.load(f)


def save_portfolio(name, portfolio):

    os.makedirs(PORTFOLIO_DIR, exist_ok=True)

    with open(_portfolio_path(name), "w") as f:
        json.dump(portfolio, f, indent=2)


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


def build_runners():
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

    Returns
    -------
    router : MultiStrategyRouter
    runners : dict of {STRATEGY_NAMES key: runner instance}
    """

    router = MultiStrategyRouter()
    runners = {}

    for index, cfg_builder, decide_fn, key in (
        ("NIFTY", make_st2_threshold_event_cfg, rsi_momentum_decide_fn, "st2_threshold"),
        ("NIFTY", make_simple_st1_threshold_event_cfg, rsi_momentum_decide_fn, "simple_st1_threshold"),
    ):
        name = STRATEGY_NAMES[key]
        index_cfg = INDEX_CONFIG[index]
        cfg = cfg_builder(index=index, lot_size=index_cfg["lot_size"])

        spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)

        runner = LiveTickRunner(
            decide_fn=decide_fn,
            cfg=cfg,
            portfolio=load_portfolio(name, cfg["initial_capital"]),
            underlying_symbol=index_cfg["underlying_symbol"],
            ce_symbol=ce_symbol,
            pe_symbol=pe_symbol,
            squareoff_time=SQUAREOFF_TIME,
            initial_candles=_seed_candles(index),
        )

        router.register(index_cfg["underlying_symbol"], runner)
        router.register(ce_symbol, runner)
        router.register(pe_symbol, runner)
        runners[key] = runner

    for index, key in (("NIFTY", "oi_footprint_nifty"), ("BANKNIFTY", "oi_footprint_banknifty")):
        name = STRATEGY_NAMES[key]
        index_cfg = INDEX_CONFIG[index]
        cfg = make_oi_footprint_event_cfg(index=index, lot_size=index_cfg["lot_size"])

        spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)

        runner = OIFootprintTickRunner(
            decide_fn=oi_footprint_decide_fn,
            cfg=cfg,
            portfolio=load_portfolio(name, cfg["initial_capital"]),
            ce_symbol=ce_symbol,
            pe_symbol=pe_symbol,
            squareoff_time=SQUAREOFF_TIME,
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
    """

    now = datetime.datetime.now()

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


def save_all(runners):
    """
    Local JSON stays the source of truth (same file this project's own
    verification/replay tooling reads) - the Firebase Realtime Database
    push is purely an ADDITIONAL live read-path for the app (see report/
    firebase_realtime_sync.py's module docstring), never a replacement.
    sync_portfolio() degrades gracefully (never raises, returns False)
    if Firebase isn't configured yet, so this is safe to always call.
    """

    from report.firebase_realtime_sync import sync_portfolio

    for key, runner in runners.items():
        name = STRATEGY_NAMES[key]
        save_portfolio(name, runner.portfolio)
        sync_portfolio(name, runner.portfolio)


def main(access_token):
    """
    NOT LIVE-TESTED - see module docstring's caveats (no VPS, fyers_
    apiv3 not installed locally, real socket connection unverified).
    Written to match the same connect_and_run() pattern already
    verified against real Fyers SDK documentation - one socket, one
    on_message callback, routed via MultiStrategyRouter instead of a
    single runner. Kept deliberately thin - all real logic lives in
    already-tested code this function only wires together.
    """

    from fyers_apiv3.FyersWebsocket import data_ws
    from report.push_notifier import send_push_notification

    router, runners = build_runners()

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
        router.route(message)
        save_all(runners)  # persist after every real state change

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

    socket.connect()
