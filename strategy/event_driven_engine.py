import datetime

from strategy.backtest_live_engine import run_backtest, run_live_check
from strategy.options_transaction_costs import calculate_options_round_trip_cost
from indicators.circuit_band import is_near_circuit_band

# Added 17-Aug-2026 - CODE-PREP for Stage 2 (VPS + Fyers WebSocket),
# per the plan already on record (PROJECT_STATUS.md's "LIVE-DATA
# ARCHITECTURE" entry, 06/07-Aug): this rewrite was always going to be
# needed before Stage 2's event-driven checking, so it is built THROUGH
# strategy/backtest_live_engine.py's decide_fn shape (added 15-Aug,
# unused until now) - one function, reused for both backtest replay and
# live event-driven checking, so there is no second hand-written copy
# to drift out of sync (the exact problem that framework exists to
# prevent). Deliberately started with ONE strategy (st2_threshold - the
# strongest of the 4 real-data-verified profitable books, see 17-Aug's
# fresh profitability check) as a working, tested prototype rather than
# porting all 4 at once - prove the pattern first.
#
# GENERALIZED 18-Aug: simple_st1_threshold uses the IDENTICAL RSI-
# momentum entry/exit shape as st2_threshold (only target_net_pct/
# stop_loss_pct differ - 3.0/3.0 vs 5.0/2.0), exactly like the original
# polling engine already shares ONE generic check_or_open() across both
# via cfg (fyers_options_engine.py's make_strategy()). Renamed st2_
# threshold_decide_fn -> rsi_momentum_decide_fn to match - two book-
# specific cfg builders (make_st2_threshold_event_cfg, make_simple_st1_
# threshold_event_cfg) share the one decide_fn, rather than a second,
# identical copy of the decision logic under a different name.
#
# Only the DECISION logic lives here - this module places NO real or
# paper orders itself. No VPS, no WebSocket connection code yet either
# (that is task next after this decide_fn is verified) - this is purely
# the caller-supplied pure function the Shared Backtest-Live Engine
# contract requires.
#
# DATA_POINT SHAPE (caller-defined, must be identical from both a live
# WebSocket feed and a historical replay source):
#   {
#       "timestamp": str,          # ISO-ish, informational only
#       "spot": float,             # underlying LTP
#       "rsi": float or None,      # underlying RSI(14) on 5m candles -
#                                   # computed UPSTREAM (same calculate_
#                                   # rsi() this project already uses on
#                                   # fyers_download 5m data), not inside
#                                   # decide_fn - RSI needs a rolling
#                                   # candle window, which is state a
#                                   # single data_point can't carry, so
#                                   # this keeps decide_fn itself pure.
#                                   # Required to OPEN a new position;
#                                   # None while flat and RSI isn't
#                                   # ready yet (still gathering candles).
#       "ce_symbol": str, "ce_ltp": float, "ce_bid": float, "ce_ask": float,
#       "pe_symbol": str, "pe_ltp": float, "pe_bid": float, "pe_ask": float,
#                                   # ATM CE/PE quotes - ATM strike
#                                   # selection (round(spot/strike_step)*
#                                   # strike_step) happens UPSTREAM too
#                                   # (same formula as fyers_options_
#                                   # engine.py's _pick_atm_leg), since
#                                   # re-deriving it from spot alone
#                                   # inside decide_fn would silently
#                                   # diverge if the strike-selection
#                                   # logic is ever tuned later in only
#                                   # one place.
#       "past_squareoff": bool,    # now_ist >= squareoff_time, computed
#                                   # upstream (decide_fn has no clock)
#       "before_market_open": bool,
#                                   # now_ist < MARKET_OPEN_TIME (9:15
#                                   # IST), computed upstream. Added
#                                   # 21-Aug-2026 - real bug caught live:
#                                   # a WebSocket connection replays
#                                   # Fyers' last-known pre-market
#                                   # snapshot (often yesterday's closing
#                                   # quote) on connect, and this engine
#                                   # had NO market-hours gate anywhere,
#                                   # so it opened a real-tracked
#                                   # position off that stale data before
#                                   # 09:15 IST (confirmed live: entered
#                                   # 07:59:55 IST at yesterday's closing
#                                   # spot price). Only gates NEW entries
#                                   # (matches fyers_options_engine.py's
#                                   # check_or_open()'s own established
#                                   # MARKET_OPEN_TIME pattern) - an
#                                   # already-open position still gets
#                                   # checked for Target/Stop-Loss/
#                                   # Square-Off regardless of time, same
#                                   # as the older polling engine.
#       "today_realized_pnl": float,
#                                   # Sum of Net PnL of trades already
#                                   # closed TODAY (IST calendar day),
#                                   # computed upstream from the
#                                   # runner's own portfolio (decide_fn
#                                   # never sees Closed Trades directly -
#                                   # only "position", per this module's
#                                   # pure-function contract). Added
#                                   # 21-Aug-2026 for the optional
#                                   # daily_profit_lock gate - only
#                                   # meaningful when cfg["daily_
#                                   # profit_lock"] is True (see
#                                   # make_st2_threshold_event_cfg()'s
#                                   # own note); 0 is a safe default
#                                   # (data_point.get(..., 0)) when the
#                                   # caller doesn't compute it.
#       "today_consecutive_losses": int,
#                                   # The CURRENT losing streak among
#                                   # TODAY's closed trades, computed
#                                   # upstream (same "decide_fn never
#                                   # sees Closed Trades directly" rule
#                                   # as today_realized_pnl above).
#                                   # Added 21-Aug-2026, ported from
#                                   # strategy/fyers_options_engine.py's
#                                   # MAX_CONSECUTIVE_LOSSES/_today_
#                                   # consecutive_losses() (already
#                                   # proven there) after a real whipsaw
#                                   # day - re-entering on the very next
#                                   # tick after every close, no cooldown.
#                                   # Only meaningful when cfg["daily_
#                                   # loss_lock"] is True; 0 is a safe
#                                   # default when the caller doesn't
#                                   # compute it.
#       "previous_close": float or None,
#                                   # Added 20-Aug-2026 - the underlying
#                                   # index's previous trading day close,
#                                   # for indicators/circuit_band.py's
#                                   # proactive circuit-proximity gate
#                                   # (see doc/PROJECT_STATUS.md's 14-Aug
#                                   # "CIRCUIT-BREAKER PROTECTION IDEAS"
#                                   # entry, candidate #3 - built and
#                                   # backtest-checked that day, wired
#                                   # into a live decide_fn for the first
#                                   # time here). None (not fetched, or
#                                   # a caller/test that doesn't supply
#                                   # it) SKIPS the gate entirely rather
#                                   # than raising - same "missing means
#                                   # can't check, not an error" rule
#                                   # this whole module already uses for
#                                   # rsi/oi_signal being None.
#   }
#
# POSITION SHAPE (what this decide_fn stores as portfolio["Position"]):
#   {"Option Type": "CE"/"PE", "Symbol": str, "Entry Premium": float,
#    "Entry Premium (Quote)": float or None,   # ADDED 21-Aug-2026 - the
#                                   # ask side of the book at entry,
#                                   # reporting-only (see new_position's
#                                   # own note in rsi_momentum_decide_fn/
#                                   # oi_footprint_decide_fn below) - NOT
#                                   # read by any decision above, only
#                                   # carried through to the eventual
#                                   # trade_record's "Net PnL (Quote)".
#    "Entry Spot": float, "Entry Time": str, "Lots": int,
#    "Capital Deployed": float}
#
# cfg fields used: lot_size, strike_step (unused here, ATM already
# picked upstream - kept for interface parity), initial_capital,
# target_net_pct, hybrid_sl_cap_pct, spread_pct (opt-in, None = same
# behavior as every live book today - see options_transaction_costs.py).


def _near_circuit(data_point):
    """
    True only when previous_close is actually available AND spot is
    within the default 2% proximity threshold of NSE's 10% circuit
    tier (indicators/circuit_band.py's own defaults - the same
    threshold and tier already backtest-checked against real
    oi_footprint trades on 14-Aug, zero false positives). Missing
    previous_close (upstream fetch failed, or a test data_point that
    doesn't set it) returns False - "can't check" must never be
    treated as "must exit", which would make a data gap MORE
    dangerous, not less.
    """

    previous_close = data_point.get("previous_close")

    if previous_close is None:
        return False

    return is_near_circuit_band(data_point["spot"], previous_close)


def _hybrid_stop_loss_cap(cfg, capital_deployed):
    """Same formula as fyers_options_engine.py's _hybrid_stop_loss_cap -
    duplicated (not imported) because that module's version reads from
    a portfolio-style cfg with different key names; this is a small
    enough pure calculation that a second copy in a different data
    shape doesn't create the drift risk the decide_fn pattern exists to
    avoid (the risk is in ENTRY/EXIT DECISION logic, not this one-line
    min())."""

    pct = cfg["hybrid_sl_cap_pct"]
    flat_cap = cfg["initial_capital"] * (pct / 100)
    pct_cap = capital_deployed * (pct / 100)

    return min(flat_cap, pct_cap)


def _net_pnl(cfg, entry_premium, exit_premium, lots):

    quantity = lots * cfg["lot_size"]
    gross_pnl = (exit_premium - entry_premium) * quantity
    cost = calculate_options_round_trip_cost(
        entry_premium, exit_premium, cfg["lot_size"], lots, spread_pct=cfg.get("spread_pct")
    )

    return gross_pnl - cost


def _quote_net_pnl(cfg, entry_quote, exit_quote, lots):
    """
    Added 21-Aug-2026 - same reporting-only quote fields as new_
    position/trade_record's own 21-Aug-2026 notes above, reused so
    "Net PnL (Quote)" is right there on the trade record instead of
    needing a separate offline script every time. None (not 0) when
    either side's quote is missing - live ticks arriving before a bid/
    ask has ever been seen for that leg, or backtest replay (no bid/ask
    columns at all) - so a genuinely-unknown quote PnL never gets
    silently reported as a real zero.
    """

    if entry_quote is None or exit_quote is None:
        return None

    return _net_pnl(cfg, entry_quote, exit_quote, lots)


def _rsi_momentum_decide(cfg, position, data_point, entry_field, exit_field):
    """
    Shared core behind rsi_momentum_decide_fn (entry_field=exit_field=
    "ltp") and rsi_momentum_quote_decide_fn (entry_field="ask",
    exit_field="bid") below - added 21-Aug-2026 so the RSI/lock/
    circuit-band/squareoff rules live in exactly one place regardless
    of which data_point field a given book's Target/Stop-Loss actually
    triggers off, same "no second copy to drift out of sync" principle
    this whole decide_fn pattern already exists for.

    entry_field/exit_field pick the data_point suffix - "{leg}_{field}"
    - read at entry/exit respectively; kept separate (not one shared
    field) because a real fill is never symmetric: buying pays the ASK,
    selling realizes the BID, never the same price.

    Returns
    -------
    (action, new_position, trade_record)
    """

    if position is None:

        if data_point.get("rsi") is None:
            return "SKIPPED (RSI not ready yet)", None, None

        if data_point.get("before_market_open"):
            return "SKIPPED (before market open)", None, None

        if data_point.get("past_squareoff"):
            return "SKIPPED (past square-off time)", None, None

        if cfg.get("daily_profit_lock"):
            # CHANGED 21-Aug-2026, user's own follow-up ask - percentage
            # of initial_capital (scales with capital), not a flat
            # rupee figure - matches fyers_options_engine.py's own
            # daily_profit_lock_pct convention. ">=", not "==" or a hard
            # cap on the triggering trade itself - a single trade is
            # free to close above the threshold (its own Target/Stop-
            # Loss decides that), this only blocks the NEXT new entry
            # once today's cumulative realized PnL has reached it.
            threshold = cfg["initial_capital"] * (cfg.get("daily_profit_lock_pct", 2.0) / 100)
            if data_point.get("today_realized_pnl", 0) >= threshold:
                return "SKIPPED (today's profit lock reached)", None, None

        if cfg.get("daily_loss_lock"):
            # Added 21-Aug-2026, ported from strategy/fyers_options_
            # engine.py's MAX_CONSECUTIVE_LOSSES/_today_consecutive_
            # losses() (already proven/backtested there - NOT
            # reinvented here) after a real whipsaw day: st2_threshold/
            # simple_st1_threshold took 81/106 trades on 21-Aug (71-79%
            # Stop-Loss), re-entering on the very next tick after every
            # close, no cooldown. today_consecutive_losses is computed
            # upstream (see DATA_POINT SHAPE's own note above for why
            # it must use THIS module's naive-IST convention, not the
            # polling engine's naive-UTC one). Opt-in, defaults off -
            # every existing book keeps its current behavior unchanged
            # unless daily_loss_lock=True.
            max_losses = cfg.get("max_consecutive_losses", 2)
            if data_point.get("today_consecutive_losses", 0) >= max_losses:
                return (f"SKIPPED (today already has {max_losses}+ consecutive losses, "
                        f"no more new trades today)", None, None)

        if _near_circuit(data_point):
            return "SKIPPED (near circuit band)", None, None

        option_type = "CE" if data_point["rsi"] >= 50 else "PE"
        symbol = data_point[f"{option_type.lower()}_symbol"]
        entry_premium = data_point.get(f"{option_type.lower()}_{entry_field}")

        if not entry_premium or entry_premium <= 0:
            return "SKIPPED (no valid premium quote)", None, None

        lots = int(cfg["initial_capital"] // (entry_premium * cfg["lot_size"]))

        if lots < 1:
            return f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})", None, None

        new_position = {
            "Option Type": option_type,
            "Symbol": symbol,
            "Entry Premium": entry_premium,
            "Entry Spot": data_point["spot"],
            "Entry Time": data_point["timestamp"],
            "Lots": lots,
            "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        }

        if entry_field == "ltp":
            # Added 21-Aug-2026, at the user's own request after today's
            # depth-based slippage analysis found "Entry/Exit Premium"
            # (LTP) overstates real PnL by ~87-91% on a thin ATM book -
            # ce_bid/ce_ask/pe_bid/pe_ask were already plumbed all the
            # way from the raw Fyers tick (see handle_symbol_update_
            # message() in live_tick_harness.py) into data_point, just
            # never read here. REPORTING ONLY - entry_premium (LTP,
            # above) still drives lots sizing and Capital Deployed
            # unchanged; this is purely an extra field for a more
            # realistic PnL view. Skipped for rsi_momentum_quote_
            # decide_fn (entry_field="ask") - redundant there, since
            # Entry Premium above already IS the quote. .get(), not []
            # - absent on backtest replay data_points, which carry no
            # bid/ask columns.
            new_position["Entry Premium (Quote)"] = data_point.get(f"{option_type.lower()}_ask")

        return f"OPENED {option_type} @ {entry_premium}", new_position, None

    option_type = position["Option Type"]
    current_premium = data_point.get(f"{option_type.lower()}_{exit_field}")

    if not current_premium or current_premium <= 0:
        return "HELD (no valid premium quote)", position, None

    net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])
    net_pnl_pct = net_pnl / cfg["initial_capital"] * 100

    reason = None

    if net_pnl_pct >= cfg["target_net_pct"]:
        reason = "Target"
    elif cfg.get("hybrid_sl_cap_pct") is not None:
        if net_pnl <= -_hybrid_stop_loss_cap(cfg, position["Capital Deployed"]):
            reason = "Stop Loss"
    elif net_pnl_pct <= -cfg["stop_loss_pct"]:
        reason = "Stop Loss"

    if reason is None and _near_circuit(data_point):
        reason = "Circuit Risk"
    if reason is None and data_point.get("past_squareoff"):
        reason = "Square-Off"

    if reason is None:
        return f"HELD (net {round(net_pnl, 2)} / {round(net_pnl_pct, 3)}%)", position, None

    trade_record = {
        "Symbol": position["Symbol"],
        "Option Type": option_type,
        "Entry Time": position["Entry Time"],
        "Entry Premium": position["Entry Premium"],
        "Entry Spot": position["Entry Spot"],
        "Exit Time": data_point["timestamp"],
        "Exit Premium": current_premium,
        "Exit Spot": data_point["spot"],
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl_pct, 3),
    }

    if entry_field == "ltp":
        # See new_position's own 21-Aug-2026 note above - carried
        # through unchanged from open, reporting only, skipped for
        # rsi_momentum_quote_decide_fn.
        exit_quote = data_point.get(f"{option_type.lower()}_bid")
        net_pnl_quote = _quote_net_pnl(cfg, position.get("Entry Premium (Quote)"), exit_quote, position["Lots"])
        trade_record["Entry Premium (Quote)"] = position.get("Entry Premium (Quote)")
        trade_record["Exit Premium (Quote)"] = exit_quote
        trade_record["Net PnL (Quote)"] = round(net_pnl_quote, 2) if net_pnl_quote is not None else None

    return f"CLOSED ({reason}) net {round(net_pnl, 2)}", None, trade_record


def rsi_momentum_decide_fn(cfg, position, data_point):
    """
    Faithful event-driven port of the shared RSI-momentum rules behind
    both st2_threshold and simple_st1_threshold (RSI>=50 -> CE else PE,
    ATM, Target %/hybrid Stop-Loss cap from cfg, Square-Off at
    squareoff_time) - see strategy/fyers_options_engine.py's
    make_strategy()/_check_position()/_open_position() for the original
    polling version this must match. Pure function, per the Shared
    Backtest-Live Engine contract - no I/O, no clock, no network.

    Thin wrapper around _rsi_momentum_decide() (added 21-Aug-2026,
    alongside rsi_momentum_quote_decide_fn below, for the refactor's
    own reasoning) - Target/Stop-Loss trigger off LTP, same as always.
    Byte-identical to this function's pre-21-Aug-2026 behavior.

    Returns
    -------
    (action, new_position, trade_record)
    """

    return _rsi_momentum_decide(cfg, position, data_point, "ltp", "ltp")


def rsi_momentum_quote_decide_fn(cfg, position, data_point):
    """
    Added 21-Aug-2026, at the user's own request after today's real
    depth-slippage finding that LTP-based Entry/Exit Premium overstates
    realized PnL by ~87-91% on a thin ATM book (st2_threshold_lock/
    simple_st1_threshold_lock's real 2%-target trade). Same RSI/lock/
    circuit-band/squareoff rules as rsi_momentum_decide_fn (shared via
    _rsi_momentum_decide) - the ONLY difference is which data_point
    field Target/Stop-Loss actually trigger off: the real ASK (buying)
    at entry, the real BID (selling) at exit, instead of LTP - so the
    recorded PnL is realistic the moment a trade closes, not something
    reconstructed afterward. Missing/zero ask at entry -> SKIPPED
    (never silently falls back to LTP); missing bid while holding ->
    HELD (waits for the next tick with a real quote, same as a missing
    LTP tick would today for rsi_momentum_decide_fn).

    Returns
    -------
    (action, new_position, trade_record)
    """

    return _rsi_momentum_decide(cfg, position, data_point, "ask", "bid")


def make_st2_threshold_event_cfg(index, lot_size, initial_capital=100000,
                                  hybrid_sl_cap_pct=2.0, spread_pct=None,
                                  daily_profit_lock=False, daily_profit_lock_pct=2.0,
                                  daily_loss_lock=False, max_consecutive_losses=2):
    """
    cfg builder for rsi_momentum_decide_fn/rsi_momentum_quote_decide_fn
    - mirrors fyers_options_engine.py's make_strategy() field names
    where they overlap, so a real Fyers response can be mapped into a
    data_point without a second translation layer to keep in sync
    later.

    daily_profit_lock/daily_profit_lock_pct - added 21-Aug-2026, at the
    user's own request after today's real -Rs 22,949.63 stale-data
    incident (see event_driven_runner.py's own STRATEGY_NAMES comment
    for the "separate locked variant, not a change to the existing
    live books" reasoning). Defaults to False/no behavior change for
    every existing call site. CHANGED same day to percentage-of-
    capital (matches fyers_options_engine.py's own daily_profit_lock_
    pct convention) rather than the original flat Rs 2000 - user's own
    explicit follow-up ask, so the lock scales if initial_capital ever
    changes rather than staying pinned to a number that only happened
    to equal 2% at Rs 100,000. Does NOT cap the triggering trade itself
    - that trade's own Target/Stop-Loss decides its exit; this only
    blocks the NEXT new entry once today's cumulative realized PnL has
    reached the threshold (user's own explicit "जर तो trade 2% च्या
    वरती... close झाला तरी चालेल" - a single trade closing above 2% is
    fine, the daily minimum just has to be reached before the lock).

    daily_loss_lock/max_consecutive_losses - added 21-Aug-2026, same
    day, after real production data (st2_threshold/simple_st1_threshold
    both whipsawing - 81/106 trades, 71-79% Stop-Loss) proved out the
    exact rule already used (and proven) by strategy/fyers_options_
    engine.py's MAX_CONSECUTIVE_LOSSES/daily_loss_lock - see _rsi_
    momentum_decide()'s own note. Defaults to False/2, no behavior
    change unless explicitly turned on per book.
    """

    return {
        "index": index,
        "lot_size": lot_size,
        "initial_capital": initial_capital,
        "target_net_pct": 5.0,
        "stop_loss_pct": 2.0,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "spread_pct": spread_pct,
        "daily_profit_lock": daily_profit_lock,
        "daily_profit_lock_pct": daily_profit_lock_pct,
        "daily_loss_lock": daily_loss_lock,
        "max_consecutive_losses": max_consecutive_losses,
    }


def make_simple_st1_threshold_event_cfg(index, lot_size, initial_capital=100000,
                                         hybrid_sl_cap_pct=2.0, spread_pct=None,
                                         daily_profit_lock=False, daily_profit_lock_pct=2.0,
                                         daily_loss_lock=False, max_consecutive_losses=2):
    """
    cfg builder for rsi_momentum_decide_fn/rsi_momentum_quote_decide_fn,
    simple_st1_threshold's real ratios (Target 3%, Stop-Loss 3% -
    symmetric, vs st2_threshold's 5%/2%) - same decide_fn, only cfg
    differs, per this module's 18-Aug generalization note above.

    daily_profit_lock/daily_profit_lock_pct - see make_st2_threshold_
    event_cfg()'s matching 21-Aug-2026 note above.

    daily_loss_lock/max_consecutive_losses - see make_st2_threshold_
    event_cfg()'s matching 21-Aug-2026 note above.
    """

    return {
        "index": index,
        "lot_size": lot_size,
        "initial_capital": initial_capital,
        "target_net_pct": 3.0,
        "stop_loss_pct": 3.0,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "spread_pct": spread_pct,
        "daily_profit_lock": daily_profit_lock,
        "daily_profit_lock_pct": daily_profit_lock_pct,
        "daily_loss_lock": daily_loss_lock,
        "max_consecutive_losses": max_consecutive_losses,
    }


# Added 18-Aug-2026 - second decide_fn, oi_footprint - the user's own
# follow-up pick after today's merged 18-Aug cloud-session PR found the
# SAME polling-overshoot root cause independently for this specific
# book (oi_footprint/NIFTY: +Rs 56,330 peak on 14-Aug down to -Rs
# 47,607 by 18-Aug, almost entirely from overshot Rs 1,500 Stop-
# Losses - see PROJECT_STATUS.md's "oi_footprint EXIT-MECHANISM DEEP
# DIVE" entry and its 18-Aug updates) - the book with the tightest
# Target/Stop-Loss band in the project, so the most exposed to exactly
# the check-frequency gap this whole WebSocket rewrite exists to close.
#
# KEY DIFFERENCE from rsi_momentum_decide_fn: the entry signal is OI-
# BUILDUP (price direction + Open Interest change at the ATM strike
# between two checks - see fyers_options_oi_footprint.py's module
# docstring for the full Long/Short Buildup/Covering/Unwinding
# framework), not RSI. Classifying that needs a PREVIOUS OI snapshot to
# compare against - the exact same kind of rolling state RSI needed,
# so the same design rule applies: classification happens UPSTREAM
# (see live_tick_harness.py's OIBuildupTracker, which reuses fyers_
# options_oi_footprint.py's own _classify_buildup() unchanged - no
# second copy of that decision rule), and decide_fn receives an already-
# resolved `oi_signal` field ("CE"/"PE"/None) on the data_point, keeping
# decide_fn itself pure. Target/Stop-Loss stay Rs 1,500 FIXED (rupee,
# not %-of-capital) matching the original design's own explicit "quick
# in and out, not a big bet" choice - hybrid_sl_cap_pct is offered as
# an opt-in override (default None keeps the original fixed-Rs
# behavior) since today's cloud-session backtest found it edges out a
# flat -Rs 2,000 cap slightly for this book too, same direction as the
# original 8-book HYBRID SL CAP finding.


def oi_footprint_decide_fn(cfg, position, data_point):
    """
    Faithful event-driven port of oi_footprint's real rules. See this
    module's own header comment above for the OI-signal-precomputed-
    upstream design note. Pure function, per the Shared Backtest-Live
    Engine contract - no I/O, no clock, no network.

    data_point adds `oi_signal` ("CE"/"PE"/None, precomputed upstream)
    to the same ce/pe_symbol/ce/pe_ltp/spot/timestamp/past_squareoff
    shape rsi_momentum_decide_fn's data_point already uses.

    Returns
    -------
    (action, new_position, trade_record)
    """

    if position is None:

        oi_signal = data_point.get("oi_signal")

        if oi_signal is None:
            return "SKIPPED (no meaningful OI buildup)", None, None

        if data_point.get("before_market_open"):
            return "SKIPPED (before market open)", None, None

        if data_point.get("past_squareoff"):
            return "SKIPPED (past square-off time)", None, None

        if cfg.get("daily_profit_lock"):
            # CHANGED 21-Aug-2026, user's own follow-up ask - percentage
            # of initial_capital (scales with capital), not a flat
            # rupee figure - matches fyers_options_engine.py's own
            # daily_profit_lock_pct convention. ">=", not "==" or a hard
            # cap on the triggering trade itself - a single trade is
            # free to close above the threshold (its own Target/Stop-
            # Loss decides that), this only blocks the NEXT new entry
            # once today's cumulative realized PnL has reached it.
            threshold = cfg["initial_capital"] * (cfg.get("daily_profit_lock_pct", 2.0) / 100)
            if data_point.get("today_realized_pnl", 0) >= threshold:
                return "SKIPPED (today's profit lock reached)", None, None

        # Added 24-Aug-2026, ported from _rsi_momentum_decide's own
        # 21-Aug-2026 daily_loss_lock (see that function's matching
        # note) after a real incident found live the same day:
        # oi_footprint_banknifty whipsawed 141 real trades (69 losses,
        # -Rs 23,952) with no breaker at all - daily_profit_lock above
        # only ever watches for PROFIT, never stops a book that's
        # simply losing. Opt-in, defaults off - every existing
        # oi_footprint book's behavior is unchanged unless
        # daily_loss_lock=True.
        if cfg.get("daily_loss_lock"):
            max_losses = cfg.get("max_consecutive_losses", 2)
            if data_point.get("today_consecutive_losses", 0) >= max_losses:
                return (f"SKIPPED (today already has {max_losses}+ consecutive losses, "
                        f"no more new trades today)", None, None)

        if _near_circuit(data_point):
            return "SKIPPED (near circuit band)", None, None

        option_type = oi_signal
        symbol = data_point[f"{option_type.lower()}_symbol"]
        entry_premium = data_point[f"{option_type.lower()}_ltp"]

        if not entry_premium or entry_premium <= 0:
            return "SKIPPED (no valid premium quote)", None, None

        lots = int(cfg["initial_capital"] // (entry_premium * cfg["lot_size"]))

        if lots < 1:
            return f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})", None, None

        new_position = {
            "Option Type": option_type,
            "Symbol": symbol,
            "Entry Premium": entry_premium,
            # See rsi_momentum_decide_fn's matching 21-Aug-2026 note
            # above - same reporting-only quote field, same reasoning.
            "Entry Premium (Quote)": data_point.get(f"{option_type.lower()}_ask"),
            "Entry Spot": data_point["spot"],
            "Entry Time": data_point["timestamp"],
            "Lots": lots,
            "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        }

        return f"OPENED {option_type} @ {entry_premium} (OI buildup signal)", new_position, None

    option_type = position["Option Type"]
    current_premium = data_point[f"{option_type.lower()}_ltp"]

    if not current_premium or current_premium <= 0:
        return "HELD (no valid premium quote)", position, None

    net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])

    reason = None

    if net_pnl >= cfg["target_rupees"]:
        reason = "Target"
    elif cfg.get("hybrid_sl_cap_pct") is not None:
        if net_pnl <= -_hybrid_stop_loss_cap(cfg, position["Capital Deployed"]):
            reason = "Stop Loss"
    elif net_pnl <= -cfg["stop_loss_rupees"]:
        reason = "Stop Loss"

    if reason is None and _near_circuit(data_point):
        reason = "Circuit Risk"
    if reason is None and data_point.get("past_squareoff"):
        reason = "Square-Off"

    if reason is None:
        return f"HELD (net {round(net_pnl, 2)})", position, None

    exit_quote = data_point.get(f"{option_type.lower()}_bid")
    net_pnl_quote = _quote_net_pnl(cfg, position.get("Entry Premium (Quote)"), exit_quote, position["Lots"])

    trade_record = {
        "Symbol": position["Symbol"],
        "Option Type": option_type,
        "Entry Time": position["Entry Time"],
        "Entry Premium": position["Entry Premium"],
        "Entry Premium (Quote)": position.get("Entry Premium (Quote)"),
        "Entry Spot": position["Entry Spot"],
        "Exit Time": data_point["timestamp"],
        "Exit Premium": current_premium,
        "Exit Premium (Quote)": exit_quote,
        "Exit Spot": data_point["spot"],
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
        "Net PnL (Quote)": round(net_pnl_quote, 2) if net_pnl_quote is not None else None,
    }

    return f"CLOSED ({reason}) net {round(net_pnl, 2)}", None, trade_record


def make_oi_footprint_event_cfg(index, lot_size, initial_capital=100000,
                                 hybrid_sl_cap_pct=None, spread_pct=None,
                                 daily_loss_lock=False, max_consecutive_losses=2):
    """
    cfg builder for oi_footprint_decide_fn. hybrid_sl_cap_pct defaults
    to None (the original fixed Rs 1,500 Stop-Loss) - pass 2.0 to use
    the hybrid cap today's cloud-session backtest found slightly better
    for this book (see this module's header comment).

    daily_loss_lock/max_consecutive_losses - added 24-Aug-2026, same
    fields/defaults as make_st2_threshold_event_cfg's own (21-Aug-2026)
    - see oi_footprint_decide_fn's matching note for the real incident.
    Default False keeps every existing book's behavior unchanged.
    """

    return {
        "index": index,
        "lot_size": lot_size,
        "initial_capital": initial_capital,
        "target_rupees": 1500,
        "stop_loss_rupees": 1500,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "spread_pct": spread_pct,
        "daily_loss_lock": daily_loss_lock,
        "max_consecutive_losses": max_consecutive_losses,
    }
