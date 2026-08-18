# Added 18-Aug-2026, at the user's request: build the event-driven
# engine so that switching it from paper trading to real (live) trading
# later is a CONFIGURATION change, not a code change. Scoped ONLY to
# the 4 event-driven/VPS strategies (confirmed with the user) - the
# ~60 existing live books on the older polling engine each have their
# own hand-copied open/close logic across 13 separate files and are
# explicitly out of scope; touching them would risk regressions in
# currently-profitable, real-capital-adjacent code.
#
# This module does NOT build real order placement - per CLAUDE.md,
# "Claude never executes a real trade - final action is always the
# user's, even after Broker Integration exists." It builds the SEAM so
# that when real execution is built later (a separate, much larger
# effort - needs a general buy/sell order function, since strategy/
# fyers_order_execution.py today only has a stop-loss SELL order, plus
# a human-approval step before any order fires), it plugs in via ONE
# more branch in resolve_execution_backend() below - zero changes
# needed to event_driven_engine.py, event_driven_runner.py, live_tick_
# harness.py, or any decide_fn.


class PaperExecutionBackend:
    """
    No-op - the default, and today's only real implementation. The
    paper portfolio is already updated by backtest_live_engine.py's
    _step() before either hook below ever runs (see that module's
    docstring); this class exists only so every runner has a real
    object to call on_open()/on_close() against, matching the
    interface a future live-execution backend will need to implement.
    """

    def on_open(self, cfg, position):
        pass

    def on_close(self, cfg, trade_record):
        pass


def resolve_execution_backend(mode):
    """
    The ONLY place that needs to change when a real LiveExecutionBackend
    is eventually built - every runner already accepts an
    execution_backend object (strategy/live_tick_harness.py) and never
    needs to know how it was chosen. Called once, at VPS startup, from
    run_event_driven_engine.py - same "top-level script resolves real
    config, the strategy/ module underneath takes it as a plain
    parameter" split this project already uses for the Firebase
    access-token handoff.
    """

    if mode == "paper":
        return PaperExecutionBackend()

    if mode == "live":
        raise NotImplementedError(
            "Live execution backend not built yet - requires a general buy/sell "
            "order function (fyers_order_execution.py today only has a stop-loss "
            "SELL order) and a user-approval step before any order is sent "
            "(CLAUDE.md: Claude never executes a real trade). TURION_EXECUTION_MODE "
            "must stay 'paper' until that exists."
        )

    raise ValueError(f"Unknown TURION_EXECUTION_MODE: {mode!r} (expected 'paper' or 'live')")
