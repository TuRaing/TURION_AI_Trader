import datetime
import json
import os

from strategy.backtest_live_engine import run_live_check
from strategy.execution_backend import PaperExecutionBackend
from strategy.live_tick_harness import CandleAggregator, _today_consecutive_losses

# Added 24-Aug-2026 - the crypto paper-trading sub-project's own tick
# runner, a deliberately simpler sibling of strategy/live_tick_harness.
# py's LiveTickRunner (see the approved plan). Same on_tick(symbol,
# timestamp, ltp, bid, ask) shape and state-assembly role - builds a
# data_point and calls decide_fn via run_live_check(), the SAME
# function a batch backtest replay uses (strategy/backtest_live_engine.
# py) - but with NO squareoff_time parameter at all: LiveTickRunner's
# _past_squareoff() has no disabled/None mode (confirmed by reading
# that method), and Deribit is a 24/7 market with no daily-close
# concept, so past_squareoff/before_market_open are simply hardcoded
# False here instead of reusing that class.
#
# Deliberately does NOT import strategy/event_driven_runner.py - this
# subsystem's only coupling to the NIFTY/BankNifty codebase stays
# confined to the modules the approved plan explicitly designed to be
# shared (backtest_live_engine.py, event_driven_engine.py's rsi_
# momentum_decide_fn, live_tick_harness.py's CandleAggregator/_today_
# consecutive_losses, execution_backend.py's PaperExecutionBackend) -
# so this owns its own small atomic-write portfolio load/save below,
# same pattern as event_driven_runner.py's load_portfolio()/save_
# portfolio() (including that module's own 24-Aug-2026 fix: atomic
# temp-file + os.replace() write, and graceful degradation on an
# empty/corrupt file) rather than importing that module's version.
#
# today_consecutive_losses IS wired up (module-level _today_
# consecutive_losses, imported unchanged from live_tick_harness.py,
# same "one place, not two copies" reasoning that function's own
# 24-Aug-2026 note gives) since it's cheap and already shared - the
# daily_loss_lock gate itself still defaults off unless a book opts in.
#
# today_realized_pnl - added 30-Aug-2026, at the user's own request,
# for a real BTC/ETH backtest finding (doc/CRYPTO_PROJECT_STATUS.md's
# own record of the session): daily_profit_lock helps, but ONLY with a
# short ROLLING window (2-3h), not the UTC-calendar-day boundary
# _today_consecutive_losses above uses - see _realized_pnl_within_
# hours()'s own note for why a 24/7 market needs a rolling window
# instead of a clock-boundary reset. Computed only when a book actually
# opts into daily_profit_lock (cfg.get check below) - a no-op scan over
# Closed Trades on every tick would be needless cost for every book
# that doesn't use this gate.

PORTFOLIO_DIR = "reports"


def _realized_pnl_within_hours(portfolio, timestamp, hours):
    """
    Rolling-window sibling of strategy/live_tick_harness.py's
    LiveTickRunner._today_realized_pnl() - sums Net PnL for trades
    whose Exit Time falls within the last `hours` hours of `timestamp`,
    instead of that method's UTC-calendar-day boundary. Moved here
    (from crypto_options_backtest.py, where it was first written and
    proven during this session's backtest sweep) so the exact same
    function drives both the backtest and this live runner - no second
    copy to drift out of sync, same principle every other decide_fn
    helper in this project already follows.

    FIXED 30-Aug-2026, real crash caught live within minutes of
    deploy: `timestamp` here is timezone-AWARE when called from
    CryptoTickRunner.on_tick() (built via datetime.fromtimestamp(...,
    tz=utc) in strategy/deribit_data.py's connect_and_run()), but
    Entry/Exit Time strings are always stored and re-parsed NAIVE (no
    tzinfo, matching every other timestamp field in this project's
    portfolio JSON) - comparing the two raised "TypeError: can't
    compare offset-naive and offset-aware datetimes". Never caught in
    crypto_options_backtest.py's own testing because that script always
    builds a NAIVE timestamp via strptime() - the aware/naive mismatch
    only exists on the live path. Stripping tzinfo up front makes this
    match _today_consecutive_losses()'s own naive convention exactly.
    """

    if timestamp.tzinfo is not None:
        timestamp = timestamp.replace(tzinfo=None)

    cutoff = timestamp - datetime.timedelta(hours=hours)
    total = 0.0

    for trade in portfolio.get("Closed Trades", []):
        exit_time_str = trade.get("Exit Time")
        if not exit_time_str:
            continue

        exit_naive = datetime.datetime.strptime(exit_time_str, "%Y-%m-%d %H:%M:%S")
        if exit_naive >= cutoff:
            total += trade.get("Net PnL", 0)

    return total


def _portfolio_path(name):
    return os.path.join(PORTFOLIO_DIR, f"crypto_{name}_portfolio.json")


def load_portfolio(name, initial_capital=10000):
    """
    Same atomic-read/graceful-degradation contract as strategy/event_
    driven_runner.py's load_portfolio() - see that function's own
    24-Aug-2026 incident note for why (a killed process must never be
    able to crash the whole engine via one truncated/corrupt file).
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
    """Writes atomically (temp file + os.replace()) - see load_portfolio()'s
    own note and event_driven_runner.py's matching 24-Aug-2026 fix."""

    os.makedirs(PORTFOLIO_DIR, exist_ok=True)

    path = _portfolio_path(name)
    tmp_path = path + ".tmp"

    with open(tmp_path, "w") as f:
        json.dump(portfolio, f, indent=2)

    os.replace(tmp_path, path)


class CryptoTickRunner:
    """
    Owns one strategy's live decide_fn loop over a Deribit BTC/ETH
    options book. Feed it every tick for the symbols it cares about
    (the underlying index, ATM CE, ATM PE) via on_tick(); once enough
    state exists to build a full data_point, it calls decide_fn through
    run_live_check() - the SAME function a batch backtest replay uses,
    so there is no second copy of the decision logic here, only state-
    assembly (identical role to LiveTickRunner - see that class's own
    docstring in strategy/live_tick_harness.py).
    """

    def __init__(self, decide_fn, cfg, portfolio, underlying_index_name, ce_symbol, pe_symbol,
                 initial_candles=None, execution_backend=None, profit_lock_window_hours=24):

        self.decide_fn = decide_fn
        self.cfg = cfg
        self.portfolio = portfolio
        self.underlying_index_name = underlying_index_name
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol
        self.aggregator = CandleAggregator(initial_candles)
        self.execution_backend = execution_backend or PaperExecutionBackend()
        # profit_lock_window_hours - added 30-Aug-2026, only meaningful
        # when cfg["daily_profit_lock"] is True (see on_tick()'s own
        # note) - default 24 (a full rolling day) if a profit-lock book
        # doesn't override it; the real BTC/ETH-tuned values (2h/3h)
        # are passed explicitly by run_crypto_options_engine.py.
        self.profit_lock_window_hours = profit_lock_window_hours

        self._latest = {"spot": None, "ce_ltp": None, "ce_bid": None, "ce_ask": None,
                         "pe_ltp": None, "pe_bid": None, "pe_ask": None}
        self.last_action = None

    def on_tick(self, symbol, timestamp, ltp, bid=None, ask=None):
        """
        Call once per incoming Deribit tick (a parsed ticker.{instrument}
        .100ms message for ce_symbol/pe_symbol, or a parsed deribit_
        price_index.{...} message for underlying_index_name - see
        strategy/deribit_data.py's connect_and_run()). Ticks for symbols
        this runner doesn't track are ignored.

        Returns the action string if decide_fn ran this call, else None.
        """

        if symbol == self.underlying_index_name:
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
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),  # Deribit's own tick time, UTC
            "spot": self._latest["spot"],
            "rsi": self.aggregator.current_rsi(),
            "ce_symbol": self.ce_symbol, "ce_ltp": self._latest["ce_ltp"],
            "ce_bid": self._latest["ce_bid"], "ce_ask": self._latest["ce_ask"],
            "pe_symbol": self.pe_symbol, "pe_ltp": self._latest["pe_ltp"],
            "pe_bid": self._latest["pe_bid"], "pe_ask": self._latest["pe_ask"],
            "past_squareoff": False,       # always - no daily close for a 24/7 market
            "before_market_open": False,   # always - see module docstring
            "today_consecutive_losses": _today_consecutive_losses(self.portfolio, timestamp),
            # current_cash - added 01-Sep-2026, at the user's own
            # explicit request ("balance minus मध्ये जातायत... zero
            # झालं की stop व्हायला हवं") - feeds event_driven_engine.
            # py's opt-in stop_at_zero_capital gate. Always included
            # (unlike today_realized_pnl below, which is gated behind
            # its own cfg check) - this is just a dict read, no scan
            # over Closed Trades, so there's no meaningful cost to
            # always providing it even for a book that doesn't use it.
            "current_cash": self.portfolio.get("Cash"),
            # "previous_close" intentionally omitted - disables the
            # circuit-band gate for free, same as the plan's own note
            # (Deribit has no NSE-style circuit bands to begin with).
        }

        # Added 30-Aug-2026 - see this module's own top-of-file note.
        # Only computed for a book that actually opted into daily_
        # profit_lock (cfg.get check) - a no-op scan over every closed
        # trade on every single tick would be needless cost otherwise.
        if self.cfg.get("daily_profit_lock"):
            data_point["today_realized_pnl"] = _realized_pnl_within_hours(
                self.portfolio, timestamp, self.profit_lock_window_hours
            )

        action, self.portfolio = run_live_check(self.decide_fn, self.cfg, self.portfolio, data_point)
        self.last_action = action

        if action.startswith("OPENED"):
            self.execution_backend.on_open(self.cfg, self.portfolio["Position"])
        elif action.startswith("CLOSED"):
            self.execution_backend.on_close(self.cfg, self.portfolio["Closed Trades"][-1])

        return action
