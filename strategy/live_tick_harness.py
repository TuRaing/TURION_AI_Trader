import datetime

import pandas as pd

from indicators.rsi import calculate_rsi
from strategy.backtest_live_engine import run_live_check
from strategy.execution_backend import PaperExecutionBackend
from strategy.fyers_options_engine import MARKET_OPEN_TIME
from strategy.fyers_options_oi_footprint import _classify_buildup
from strategy.squareoff import is_past_squareoff

# Added 17-Aug-2026 - task #17 of the WebSocket code-prep (see strategy/
# event_driven_engine.py's module docstring for the full plan/context).
# This is the piece that turns a real-time tick stream into the
# data_point shape event_driven_engine.py's decide_fn expects - LOCAL
# test harness only, no VPS, no real WebSocket connection tested yet
# (see the CandleAggregator/LiveTickRunner split below for exactly
# which parts are and aren't verified).
#
# SPLIT BY DESIGN, so the untestable part stays as small as possible:
#   - CandleAggregator + LiveTickRunner: pure, no network - builds 5m
#     candles from ticks and RSI from those candles (reusing indicators/
#     rsi.py's calculate_rsi() unchanged, same function every existing
#     strategy already relies on), assembles data_points, calls decide_
#     fn via run_live_check(). Fully unit-tested with synthetic ticks.
#   - connect_and_run(): the actual fyers_apiv3 FyersDataSocket wiring.
#     Written to match the REAL, verified SDK pattern (see PROJECT_
#     STATUS.md's 17-Aug WebSocket-research entry for sources) but
#     COULD NOT be live-tested before committing - local session's
#     Fyers token is expired AND Fyers' own daily API quota was
#     exhausted today (same blocker as the depth collector's own
#     caveat). Treat the first real run as a verification run.

CANDLE_INTERVAL_MINUTES = 5
MIN_CANDLES_FOR_RSI = 15  # RSI(14) needs 14 diffs = 15 closes minimum


class CandleAggregator:
    """
    Builds rolling 5-minute OHLC candles from a live tick stream (one
    on_tick(timestamp, price) call per tick), and computes RSI(14) on
    the resulting candle series using the EXACT SAME calculate_rsi()
    every polling-based strategy in this project already uses on
    fyers_download's 5m candles - so a live RSI reading here means the
    same thing as the original engine's RSI reading, not a re-derived
    approximation.

    Seed with real historical candles (e.g. from fyers_download(...,
    interval="5m")) via `initial_candles` so RSI is available from the
    first live tick instead of needing ~70 minutes of live ticks to
    warm up 15 candles from scratch.
    """

    def __init__(self, initial_candles=None):

        self.candles = (
            initial_candles.copy() if initial_candles is not None
            else pd.DataFrame(columns=["Open", "High", "Low", "Close"])
        )
        self._bucket_start = None
        self._bucket = None

    @staticmethod
    def _floor_to_bucket(timestamp):

        minute = (timestamp.minute // CANDLE_INTERVAL_MINUTES) * CANDLE_INTERVAL_MINUTES

        return timestamp.replace(minute=minute, second=0, microsecond=0)

    def on_tick(self, timestamp, price):

        bucket_start = self._floor_to_bucket(timestamp)

        if self._bucket_start is None:
            self._bucket_start = bucket_start
            self._bucket = {"Open": price, "High": price, "Low": price, "Close": price}
            return

        if bucket_start == self._bucket_start:
            self._bucket["High"] = max(self._bucket["High"], price)
            self._bucket["Low"] = min(self._bucket["Low"], price)
            self._bucket["Close"] = price
            return

        self._close_bucket()
        self._bucket_start = bucket_start
        self._bucket = {"Open": price, "High": price, "Low": price, "Close": price}

    def _close_bucket(self):

        row = pd.DataFrame([self._bucket], index=[self._bucket_start])
        self.candles = pd.concat([self.candles, row]).tail(200)

    def current_rsi(self):
        """
        RSI over closed candles only (the current, still-forming bucket
        is deliberately excluded - matches the original engine reading
        RSI off completed 5m candles, not a partial one).
        """

        if len(self.candles) < MIN_CANDLES_FOR_RSI:
            return None

        rsi_series = calculate_rsi(self.candles)
        latest = rsi_series.iloc[-1]

        return float(latest) if pd.notna(latest) else None


def _notify_execution_backend(execution_backend, cfg, portfolio, action):
    """
    Added 18-Aug-2026 - shared by both LiveTickRunner and
    OIFootprintTickRunner below, so the "which action string means
    what" mapping exists in exactly one place. decide_fn's action
    strings already encode what happened (see strategy/event_driven_
    engine.py) - "OPENED"/"CLOSED" prefixes, no need to diff portfolio
    state before/after. A no-op for the default PaperExecutionBackend;
    see strategy/execution_backend.py.
    """

    if not action:
        return

    if action.startswith("OPENED"):
        execution_backend.on_open(cfg, portfolio["Position"])
    elif action.startswith("CLOSED"):
        execution_backend.on_close(cfg, portfolio["Closed Trades"][-1])


def _maybe_top_up_capital(cfg, portfolio, timestamp):
    """
    Added 24-Aug-2026, user's own explicit request - paper-trading
    capital is virtual bookkeeping only: neither rsi_momentum_decide_fn
    nor oi_footprint_decide_fn (strategy/event_driven_engine.py) ever
    reads portfolio["Cash"] - both always size a new trade's lots off
    the FIXED cfg["initial_capital"] (decide_fn doesn't even take
    portfolio as a parameter). That means Cash is purely a running P&L
    display, never a real spending constraint, and topping it up does
    NOT change future lot sizes either way - lots were never reduced
    by losses in the first place. This tops Cash back up to cfg[
    "initial_capital"] once it has drawn down 40% or more (user's own
    threshold, CHANGED same day from "only at zero/negative") so a
    paper book's own numbers stay legible through a long losing
    stretch, rather than sitting deeply negative for the rest of its
    life. A real trading account never gets to do this (CLAUDE.md:
    Claude never executes a real trade), but this never touches
    anything but a local JSON portfolio file, exactly like every other
    paper-only bookkeeping field already on this record.

    Shared by both LiveTickRunner and OIFootprintTickRunner below, same
    "one place, not two copies" reasoning as _notify_execution_backend
    above. Never applies mid-position (Position is not None) - a
    Position's own "Capital Deployed" is tied to the Cash basis at
    entry; topping up under an open trade would make that figure
    (and the eventual Net PnL %% calculation, which divides by cfg
    ["initial_capital"] anyway, not Cash - unaffected either way)
    meaningless. Every top-up is recorded in portfolio["Capital
    Top-ups"], never silent, so a book's own history always explains
    where its Cash came from.
    """

    DRAWDOWN_TRIGGER_PCT = 40.0

    if portfolio.get("Position") is not None:
        return

    trigger_level = cfg["initial_capital"] * (1 - DRAWDOWN_TRIGGER_PCT / 100)

    if portfolio["Cash"] > trigger_level:
        return

    cash_before = portfolio["Cash"]
    portfolio["Cash"] = cfg["initial_capital"]

    portfolio.setdefault("Capital Top-ups", []).append({
        "Time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Cash Before": cash_before,
        "Topped Up To": cfg["initial_capital"],
    })


def _today_consecutive_losses(portfolio, timestamp):
    """
    The CURRENT losing streak among timestamp's own calendar day's
    closed trades, counting backward from the most recent trade until
    a win breaks the streak - the upstream half of the optional
    daily_loss_lock gate (_rsi_momentum_decide/oi_footprint_decide_fn,
    strategy/event_driven_engine.py).

    MOVED to module level 24-Aug-2026 (was a LiveTickRunner-only
    method) - real gap found live the same day: oi_footprint_
    banknifty whipsawed 141 real trades (69 losses, -Rs 23,952) with
    no breaker at all, because oi_footprint_decide_fn never had this
    computed for it - OIFootprintTickRunner had no equivalent method.
    Same "one place, not two copies" reasoning as _notify_execution_
    backend/_maybe_top_up_capital above, now shared by both runners
    instead of duplicating this a second time for OIFootprintTickRunner.

    Originally ported from strategy/fyers_options_engine.py's own
    MAX_CONSECUTIVE_LOSSES/_today_consecutive_losses() (already proven/
    backtested there) - NOT a blind copy: that version assumes "Exit
    Time" is naive-UTC; this uses the SAME date convention as
    LiveTickRunner._today_realized_pnl() (already-IST, compared
    directly), for the same reason that method's own docstring gives.
    """

    today = timestamp.date()
    today_trades = []

    for trade in portfolio.get("Closed Trades", []):

        exit_time_str = trade.get("Exit Time")

        if not exit_time_str:
            continue

        exit_naive = datetime.datetime.strptime(exit_time_str, "%Y-%m-%d %H:%M:%S")

        if exit_naive.date() == today:
            today_trades.append(trade)

    streak = 0

    for trade in reversed(today_trades):

        if trade.get("Net PnL", 0) <= 0:
            streak += 1
        else:
            break

    return streak


class LiveTickRunner:
    """
    Owns one strategy's live decide_fn loop. Feed it every tick for the
    symbols it cares about (underlying spot, ATM CE, ATM PE) via
    on_tick(); it maintains the latest known state, and once enough
    state exists to build a full data_point, calls decide_fn through
    run_live_check() - the SAME function a batch backtest replay uses
    (see event_driven_engine.py / backtest_live_engine.py), so there is
    no second copy of the decision logic here, only state-assembly.
    """

    def __init__(self, decide_fn, cfg, portfolio, underlying_symbol, ce_symbol, pe_symbol,
                 squareoff_time, initial_candles=None, execution_backend=None, previous_close=None):

        self.decide_fn = decide_fn
        self.cfg = cfg
        self.portfolio = portfolio
        self.underlying_symbol = underlying_symbol
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol
        self.squareoff_time = squareoff_time
        # Added 20-Aug-2026 - indicators/circuit_band.py's proactive
        # square-off gate (event_driven_engine.py's _near_circuit()) -
        # None (default) means the gate is simply skipped, same as
        # every other optional signal in this class - see
        # build_runners()'s own fetch-can-fail comment.
        self.previous_close = previous_close
        self.aggregator = CandleAggregator(initial_candles)
        # Added 18-Aug-2026 - see strategy/execution_backend.py's module
        # docstring. Defaults to a no-op paper backend so every existing
        # call site (tests, build_runners()) keeps working unchanged.
        self.execution_backend = execution_backend or PaperExecutionBackend()

        self._latest = {"spot": None, "ce_ltp": None, "ce_bid": None, "ce_ask": None,
                         "pe_ltp": None, "pe_bid": None, "pe_ask": None}
        self.last_action = None

    def _past_squareoff(self, timestamp):
        """
        FIXED 19-Aug-2026 - was date-blind (only compared hour:minute),
        the exact same gap already found and fixed in the older polling
        engine (see strategy/squareoff.py's module docstring for the
        real incident) - a position still open when this process
        restarts the next morning (e.g. deploy.sh's daily 08:00 IST
        cron restart) would otherwise sit unprotected until the
        ordinary Stop-Loss math eventually caught up, same as the
        Rs 1,23,027 live loss that prompted this fix. No open position
        yet -> nothing to have carried over, same-day time check only.
        """

        position = self.portfolio.get("Position")

        if position is None:
            return (timestamp.hour, timestamp.minute) >= self.squareoff_time

        return is_past_squareoff(
            position["Entry Time"], timestamp, self.squareoff_time, entry_stored_as_utc=False
        )

    def _today_realized_pnl(self, timestamp):
        """
        Sum of Net PnL for trades already closed on timestamp's own
        calendar day - the upstream half of the optional daily_profit_
        lock gate (rsi_momentum_decide_fn, strategy/event_driven_
        engine.py), added 21-Aug-2026 at the user's own request. decide_
        fn never sees Closed Trades directly (only "position", per this
        module's pure-function contract) so this has to be computed
        here, where self.portfolio is available.

        "Exit Time" is stored as the tick's own already-IST timestamp
        directly (see is_past_squareoff()'s own entry_stored_as_utc=
        False note above) - unlike fyers_options_engine.py's own
        _today_realized_pnl(), which assumes naive-UTC storage and
        would misjudge the date boundary if reused here unchanged.
        """

        today = timestamp.date()
        total = 0.0

        for trade in self.portfolio.get("Closed Trades", []):

            exit_time_str = trade.get("Exit Time")

            if not exit_time_str:
                continue

            exit_naive = datetime.datetime.strptime(exit_time_str, "%Y-%m-%d %H:%M:%S")

            if exit_naive.date() == today:
                total += trade.get("Net PnL", 0)

        return total

    # _today_consecutive_losses moved to module level 24-Aug-2026 - see
    # that function's own docstring above for why (shared with
    # OIFootprintTickRunner now).

    def on_tick(self, symbol, timestamp, ltp, bid=None, ask=None):
        """
        Call once per incoming WebSocket SymbolUpdate message. Updates
        internal state; if this tick carries enough NEW information to
        act on (underlying tick -> RSI/spot changed; CE/PE tick -> that
        leg's price changed), calls decide_fn once via run_live_check().
        Ticks for symbols this runner doesn't track are ignored.

        Returns the action string if decide_fn ran this call, else None.
        """

        if symbol == self.underlying_symbol:
            self.aggregator.on_tick(timestamp, ltp)
            self._latest["spot"] = ltp
        elif symbol == self.ce_symbol:
            self._latest["ce_ltp"] = ltp
            self._latest["ce_bid"] = bid
            self._latest["ce_ask"] = ask
        elif symbol == self.pe_symbol:
            self._latest["pe_ltp"] = ltp
            self._latest["pe_bid"] = bid
            self._latest["pe_ask"] = ask
        else:
            return None

        if self._latest["spot"] is None:
            return None  # no RSI/spot context yet

        data_point = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "spot": self._latest["spot"],
            "rsi": self.aggregator.current_rsi(),
            "ce_symbol": self.ce_symbol, "ce_ltp": self._latest["ce_ltp"],
            "ce_bid": self._latest["ce_bid"], "ce_ask": self._latest["ce_ask"],
            "pe_symbol": self.pe_symbol, "pe_ltp": self._latest["pe_ltp"],
            "pe_bid": self._latest["pe_bid"], "pe_ask": self._latest["pe_ask"],
            "past_squareoff": self._past_squareoff(timestamp),
            "before_market_open": (timestamp.hour, timestamp.minute) < MARKET_OPEN_TIME,
            "today_realized_pnl": self._today_realized_pnl(timestamp),
            "today_consecutive_losses": _today_consecutive_losses(self.portfolio, timestamp),
            "previous_close": self.previous_close,
        }

        action, self.portfolio = run_live_check(self.decide_fn, self.cfg, self.portfolio, data_point)
        self.last_action = action
        _notify_execution_backend(self.execution_backend, self.cfg, self.portfolio, action)
        _maybe_top_up_capital(self.cfg, self.portfolio, timestamp)

        return action


class OIBuildupTracker:
    """
    Added 18-Aug-2026, for oi_footprint_decide_fn (event_driven_engine.
    py) - the OI-buildup equivalent of CandleAggregator above. Reuses
    fyers_options_oi_footprint.py's own _classify_buildup() UNCHANGED
    (imported, not copied) - no second copy of that decision rule to
    drift out of sync, same principle the whole decide_fn pattern
    exists for.

    OI is not a field the real-time SymbolUpdate tick stream carries
    (confirmed against the real schema found during 17-Aug's WebSocket
    research - ltp/bid/ask/volume/etc., no OI) - so unlike price/RSI,
    this is fed via periodic snapshots (still a REST option-chain call,
    same source the original polling engine already uses, just called
    far less often than price needs to be checked), not from the tick
    stream itself.
    """

    def __init__(self):
        self._last_snapshot = None
        self.latest_signal = None

    def on_oi_snapshot(self, spot, strike, ce_oi, pe_oi):

        current = {"spot": spot, "strike": strike, "ce_oi": ce_oi, "pe_oi": pe_oi}
        self.latest_signal = _classify_buildup(self._last_snapshot, current)
        self._last_snapshot = current

        return self.latest_signal


class OIFootprintTickRunner:
    """
    Analogous to LiveTickRunner, wired for oi_footprint_decide_fn
    instead of an RSI-momentum decide_fn - separate class rather than
    generalizing LiveTickRunner, since the signal source is genuinely
    different in kind (periodic OI snapshots, not continuous ticks) and
    there is only one example of each shape so far; a shared abstraction
    would be guessing at a pattern from a sample of one.
    """

    def __init__(self, decide_fn, cfg, portfolio, ce_symbol, pe_symbol, squareoff_time,
                 execution_backend=None, previous_close=None):

        self.decide_fn = decide_fn
        self.cfg = cfg
        self.portfolio = portfolio
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol
        self.squareoff_time = squareoff_time
        # See LiveTickRunner's matching comment above.
        self.previous_close = previous_close
        self.oi_tracker = OIBuildupTracker()
        # See LiveTickRunner's matching comment - strategy/execution_backend.py.
        self.execution_backend = execution_backend or PaperExecutionBackend()

        self._latest = {"spot": None, "ce_ltp": None, "ce_bid": None, "ce_ask": None,
                         "pe_ltp": None, "pe_bid": None, "pe_ask": None}
        self.last_action = None

    def _past_squareoff(self, timestamp):
        """FIXED 19-Aug-2026 - see LiveTickRunner's matching fix above
        and strategy/squareoff.py's module docstring for the real
        incident behind it."""

        position = self.portfolio.get("Position")

        if position is None:
            return (timestamp.hour, timestamp.minute) >= self.squareoff_time

        return is_past_squareoff(
            position["Entry Time"], timestamp, self.squareoff_time, entry_stored_as_utc=False
        )

    def on_oi_snapshot(self, timestamp, spot, strike, ce_oi, pe_oi):
        """
        Call this far less often than on_tick() - once per real option-
        chain poll (the original engine's own cadence), not per price
        tick. Updates the OI-buildup signal and immediately runs
        decide_fn once, so a fresh signal is acted on right away rather
        than waiting for the next incidental price tick.
        """

        self.oi_tracker.on_oi_snapshot(spot, strike, ce_oi, pe_oi)
        self._latest["spot"] = spot

        return self._maybe_decide(timestamp)

    def on_tick(self, symbol, timestamp, ltp, bid=None, ask=None):

        if symbol == self.ce_symbol:
            self._latest["ce_ltp"] = ltp
            self._latest["ce_bid"] = bid
            self._latest["ce_ask"] = ask
        elif symbol == self.pe_symbol:
            self._latest["pe_ltp"] = ltp
            self._latest["pe_bid"] = bid
            self._latest["pe_ask"] = ask
        else:
            return None

        return self._maybe_decide(timestamp)

    def _maybe_decide(self, timestamp):

        if self._latest["spot"] is None:
            return None  # no OI snapshot yet at all

        data_point = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "spot": self._latest["spot"],
            "oi_signal": self.oi_tracker.latest_signal,
            "ce_symbol": self.ce_symbol, "ce_ltp": self._latest["ce_ltp"],
            "ce_bid": self._latest["ce_bid"], "ce_ask": self._latest["ce_ask"],
            "pe_symbol": self.pe_symbol, "pe_ltp": self._latest["pe_ltp"],
            "pe_bid": self._latest["pe_bid"], "pe_ask": self._latest["pe_ask"],
            "past_squareoff": self._past_squareoff(timestamp),
            "before_market_open": (timestamp.hour, timestamp.minute) < MARKET_OPEN_TIME,
            "previous_close": self.previous_close,
            # Added 24-Aug-2026 - see _today_consecutive_losses' own
            # module-level docstring for the real incident (oi_
            # footprint_banknifty: 141 trades, 69 losses, -Rs 23,952,
            # no breaker) this closes the gap for.
            "today_consecutive_losses": _today_consecutive_losses(self.portfolio, timestamp),
        }

        action, self.portfolio = run_live_check(self.decide_fn, self.cfg, self.portfolio, data_point)
        self.last_action = action
        _notify_execution_backend(self.execution_backend, self.cfg, self.portfolio, action)
        _maybe_top_up_capital(self.cfg, self.portfolio, timestamp)

        return action


def handle_symbol_update_message(message, runner):
    """
    Added 18-Aug-2026 - pulled out of connect_and_run()'s on_message
    closure so this ONE piece (parsing a real Fyers SymbolUpdate tick
    dict and calling the right runner method) can be unit-tested
    without a live connection - the user asked directly whether
    connect_and_run() can be backtest-checked; this is the honest
    answer: the socket I/O itself cannot (there is no "historical
    WebSocket" to replay), but this parsing/wiring step is pure and
    CAN be, so it now is (see tests/test_live_tick_harness.py). What
    still can't be verified without a real connection: auth actually
    succeeding over the socket, subscribe() actually receiving real
    ticks, reconnect behavior, and any production quirk (message
    ordering, a field being unexpectedly absent, etc.).

    `runner` may be a LiveTickRunner (RSI-momentum books) or an
    OIFootprintTickRunner (oi_footprint) - both expose the same
    on_tick(symbol, timestamp, ltp, bid, ask) shape, so this one
    function works for either.
    """

    timestamp = datetime.datetime.fromtimestamp(
        message.get("exch_feed_time", message.get("last_traded_time")),
        tz=datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
    )

    return runner.on_tick(
        symbol=message["symbol"],
        timestamp=timestamp,
        ltp=message.get("ltp"),
        bid=message.get("bid_price"),
        ask=message.get("ask_price"),
    )


def connect_and_run(access_token, runner, symbols):
    """
    NOT LIVE-TESTED - see module docstring's caveat. Written to match
    the verified fyers_apiv3 SDK pattern (FyersDataSocket, on_message
    callback receiving a dict per tick, subscribe(symbols=..., data_
    type="SymbolUpdate")). Kept deliberately thin - all the actual
    logic lives in LiveTickRunner.on_tick() and handle_symbol_update_
    message() above, both already unit-tested.
    """

    from fyers_apiv3.FyersWebsocket import data_ws  # imported here, not
    # at module level, so this module can be imported (and its tested
    # parts used) even in an environment without fyers_apiv3 installed
    # - this project's other Fyers integration uses plain `requests`
    # calls, not this SDK, so it is not yet a project dependency (see
    # requirements.txt) - add it before running this function for real.

    def on_message(message):
        handle_symbol_update_message(message, runner)

    def on_error(message):
        print(f"[fyers websocket error] {message}")

    def on_close(message):
        print(f"[fyers websocket closed] {message}")

    def on_open():
        socket.subscribe(symbols=symbols, data_type="SymbolUpdate")
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
