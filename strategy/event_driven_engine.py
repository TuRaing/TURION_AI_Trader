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


# Added 30-Aug-2026, for the opt-in trailing_min_pct check below -
# same 30% peak-giveback already used and analyzed for strategy/fyers_
# options_engine.py's own trailing variant (that module's TRAIL_PCT) -
# reused here rather than inventing a second, untested value.
TRAILING_GIVEBACK_PCT = 0.30


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
    # cost_fn - added 29-Aug-2026, opt-in (cfg.get, default None ->
    # unchanged NIFTY/BankNifty cost model) so a currency-specific cost
    # function (e.g. crypto_transaction_costs.py's Deribit USD model)
    # can be swapped in per book without touching this shared function
    # or any existing book's cfg - see crypto_transaction_costs.py's
    # own docstring for the real bug this exists to let crypto opt out
    # of (the NIFTY cost model's Rs-denominated flat brokerage being
    # subtracted as USD dollars).
    cost_fn = cfg.get("cost_fn") or calculate_options_round_trip_cost
    cost = cost_fn(
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

        if cfg.get("stop_at_zero_capital") and data_point.get("current_cash", cfg["initial_capital"]) <= 0:
            # Added 01-Sep-2026, at the user's own explicit request -
            # "balance minus मध्ये जातायत, zero झालं की stop व्हायला
            # हवं". Lot sizing (below) always uses the FIXED cfg[
            # "initial_capital"], never the live, shrinking Cash - a
            # deliberate "paper bookkeeping, not a real spending
            # constraint" choice elsewhere in this project (see
            # _maybe_top_up_capital()'s own reasoning) - so without this
            # gate a book keeps opening full-size positions forever even
            # once its own realized Cash has gone deeply negative. Only
            # blocks NEW entries - an already-open position still runs
            # to its own Target/Stop-Loss, same as every other lock
            # above. Opt-in (cfg.get, default falsy) - every existing
            # book's behavior is unchanged unless a caller explicitly
            # sets this.
            return "SKIPPED (capital depleted - book stopped)", None, None

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

        # rsi_ce_threshold/rsi_pe_threshold - added 31-Aug-2026, at the
        # user's own request after a real finding: a plain RSI>=50
        # midpoint split fires on every marginal RSI wobble around 50
        # on a choppy day, which a real 31-Aug crypto trading day
        # showed disproportionately hurts PE (down-direction) entries -
        # BTC profit-lock book: PE -$3,991 net vs CE -$130 net, same
        # day. Widening the gap (e.g. CE only >=60, PE only <=40)
        # requires genuine conviction before entering either side,
        # instead of any RSI reading on the wrong side of an exact
        # midpoint. Both default to 50 (cfg.get, not required) so
        # every existing book's behavior is BYTE-IDENTICAL to before
        # this was added - a >=50/<50 split with no neutral zone.
        rsi = data_point["rsi"]
        ce_threshold = cfg.get("rsi_ce_threshold", 50)
        pe_threshold = cfg.get("rsi_pe_threshold", 50)

        if rsi >= ce_threshold:
            option_type = "CE"
        elif rsi <= pe_threshold:
            option_type = "PE"
        else:
            return f"SKIPPED (RSI {round(rsi, 1)} in neutral zone)", None, None

        # require_trend_confirmation - added 01-Sep-2026, at the user's
        # own request after a real whipsaw: a real 4-Sep BTC session
        # showed 9 consecutive PE entries (RSI<=30, genuine conviction
        # by the threshold gate above) all immediately Stop-Lossed
        # because spot kept RISING throughout - RSI was oversold on a
        # short 5-min view while the underlying was still in an
        # uptrend on a slower view ("RSI divergence"). Requires a
        # slower-moving trend read (data_point["spot_ema"], a longer-
        # period EMA of spot - see crypto_options_backtest.py's own
        # note for how the backtest computes this) to agree with the
        # RSI-driven direction before entering: CE only if spot is
        # ABOVE its own EMA (confirmed uptrend), PE only if BELOW
        # (confirmed downtrend). Missing spot_ema (EMA not warmed up
        # yet) -> SKIPPED, never silently ignored. Opt-in (cfg.get,
        # default falsy) - every existing book's behavior is
        # unchanged.
        if cfg.get("require_trend_confirmation"):
            spot_ema = data_point.get("spot_ema")
            if spot_ema is None:
                return "SKIPPED (trend EMA not ready yet)", None, None
            if option_type == "CE" and data_point["spot"] <= spot_ema:
                return "SKIPPED (CE blocked - spot below trend EMA)", None, None
            if option_type == "PE" and data_point["spot"] >= spot_ema:
                return "SKIPPED (PE blocked - spot above trend EMA)", None, None

        symbol = data_point[f"{option_type.lower()}_symbol"]
        entry_premium = data_point.get(f"{option_type.lower()}_{entry_field}")

        if not entry_premium or entry_premium <= 0:
            return "SKIPPED (no valid premium quote)", None, None

        lots = int(cfg["initial_capital"] // (entry_premium * cfg["lot_size"]))

        if lots < 1:
            return f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})", None, None

        # max_lots - added 05-Sep-2026, real bug caught live: a
        # near-expiry Deribit contract's premium collapses toward zero
        # as real expiry nears (documented, unfixed "KNOWN LIMITATION"
        # that ATM is picked ONCE at startup, never re-derived) - since
        # lots is inversely proportional to premium, a crashing premium
        # made BTC's own lot count balloon to 1238 (normal range:
        # 5-20), producing a single "Target" trade worth +$1,968,854.76
        # against a $10,000 book - a real number, correctly summed into
        # Cash, but meaningless (confirmed live, 04-Sep-2026, required
        # a manual Cash reset - see doc/CRYPTO_PROJECT_STATUS.md).
        # Clamping lots at a hard ceiling regardless of how cheap
        # premium gets prevents this blowup outright, independent of
        # (and simpler than) actually re-deriving ATM near expiry.
        # Opt-in (cfg.get, default None = no cap) - every existing
        # NIFTY/BankNifty book's behavior is unchanged; crypto sets
        # this explicitly (see run_crypto_options_engine.py). Only
        # added to _rsi_momentum_decide (what crypto actually uses) -
        # oi_footprint_decide_fn's own identical-looking lot sizing
        # below is untouched, since no crypto book uses it.
        max_lots = cfg.get("max_lots")
        if max_lots is not None:
            lots = min(lots, max_lots)

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

    # trailing_min_pct - added 30-Aug-2026, at the user's own request,
    # ported from strategy/fyers_options_engine.py's own trailing
    # variant (that module's make_strategy() docstring gives the full
    # reasoning). REPLACES the plain target_net_pct check entirely when
    # set: no fixed upper target, the position runs until its peak Net
    # PnL %% first reaches trailing_min_pct, then a trailing stop
    # (TRAILING_GIVEBACK_PCT giveback from the peak) takes over. Unlike
    # fyers_options_engine.py's own version (which could NOT be
    # backtested - that module's historical records are Entry/Exit-only,
    # no intraday peak) this DOES work in crypto_options_backtest.py's
    # backtest too, since rsi_momentum_decide_fn already runs against
    # every intermediate 5-min data point, not just entry/exit, so the
    # real intraday peak is visible here. Peak is tracked by mutating
    # `position` in place (same pattern fyers_options_engine.py already
    # uses) - safe because backtest_live_engine.py's _step() stores
    # back the exact same object it's given as the new position.
    if cfg.get("trailing_min_pct") is not None:
        peak_pnl_pct = max(position.get("Peak PnL %", net_pnl_pct), net_pnl_pct)
        position["Peak PnL %"] = peak_pnl_pct

        if peak_pnl_pct >= cfg["trailing_min_pct"]:
            trail_floor_pct = peak_pnl_pct * (1 - (cfg.get("trailing_giveback_pct") or TRAILING_GIVEBACK_PCT))
            if net_pnl_pct <= trail_floor_pct:
                reason = "Trailing Stop"
    elif net_pnl_pct >= cfg["target_net_pct"]:
        reason = "Target"

    if reason is None:
        if cfg.get("hybrid_sl_cap_pct") is not None:
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
                                  daily_loss_lock=False, max_consecutive_losses=2,
                                  cost_fn=None, trailing_min_pct=None, trailing_giveback_pct=None,
                                  rsi_ce_threshold=50, rsi_pe_threshold=50,
                                  stop_at_zero_capital=False, require_trend_confirmation=False,
                                  max_lots=None):
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

    cost_fn - added 29-Aug-2026 for the crypto sub-project (see _net_
    pnl()'s own matching note) - None (default) keeps every existing
    NIFTY/BankNifty book's cost model byte-identical; pass strategy/
    crypto_transaction_costs.py's calculate_crypto_options_round_trip_
    cost for a Deribit book so its USD premiums aren't run through the
    NIFTY model's Rs-denominated flat brokerage.

    trailing_min_pct/trailing_giveback_pct - added 30-Aug-2026, ported
    from strategy/fyers_options_engine.py's own trailing variant (see
    _rsi_momentum_decide()'s own matching note for exactly how this
    replaces target_net_pct once set). None (default) keeps every
    existing book's plain fixed-target behavior unchanged.
    trailing_giveback_pct defaults to None here too, meaning "use
    TRAILING_GIVEBACK_PCT (30%)" - only pass a number to override that
    shared default for one specific book.

    rsi_ce_threshold/rsi_pe_threshold - added 31-Aug-2026, see _rsi_
    momentum_decide()'s own matching note for the real finding behind
    this. Both default to 50 - a plain >=50 CE / <50 PE split with no
    neutral zone, BYTE-IDENTICAL to this function's behavior before
    this was added, for every existing call site.

    stop_at_zero_capital - added 01-Sep-2026, see _rsi_momentum_
    decide()'s own matching note. False (default) keeps every existing
    book's behavior unchanged - a book keeps opening full-size new
    positions off its own fixed initial_capital regardless of how
    negative its real Cash has gone, same as always.

    require_trend_confirmation - added 01-Sep-2026, see _rsi_momentum_
    decide()'s own matching note. False (default) keeps every existing
    book's behavior unchanged - RSI alone decides direction, no slower
    trend check.

    max_lots - added 05-Sep-2026, see _rsi_momentum_decide()'s own
    matching note for the real near-expiry blowup this fixes. None
    (default) keeps every existing book's behavior unchanged - lots is
    only ever capital-derived, never capped.
    """

    return {
        "index": index,
        "lot_size": lot_size,
        "initial_capital": initial_capital,
        "target_net_pct": 5.0,
        "stop_loss_pct": 2.0,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "spread_pct": spread_pct,
        "cost_fn": cost_fn,
        "trailing_min_pct": trailing_min_pct,
        "trailing_giveback_pct": trailing_giveback_pct,
        "rsi_ce_threshold": rsi_ce_threshold,
        "rsi_pe_threshold": rsi_pe_threshold,
        "stop_at_zero_capital": stop_at_zero_capital,
        "require_trend_confirmation": require_trend_confirmation,
        "max_lots": max_lots,
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


def _oi_footprint_decide(cfg, position, data_point, entry_field, exit_field):
    """
    Shared core behind oi_footprint_decide_fn (entry_field=exit_field=
    "ltp") and oi_footprint_quote_decide_fn (entry_field="ask",
    exit_field="bid") below - added 24-Aug-2026, same refactor as
    _rsi_momentum_decide's own 21-Aug-2026 split (see that function's
    matching note) after the real-depth slippage analysis run today
    against 55 real oi_footprint_nifty trades confirmed this book has
    the SAME LTP-vs-real-depth gap the RSI-momentum lock books had
    before their own quote-fix (recorded PnL even flips sign vs the
    walk-the-book realistic PnL on many individual trades) - this book
    never got that fix, only the reporting-only "(Quote)" fields did.

    data_point adds `oi_signal` ("CE"/"PE"/None, precomputed upstream)
    to the same ce/pe_symbol/ce/pe_ltp/ce/pe_ask/ce/pe_bid/spot/
    timestamp/past_squareoff shape rsi_momentum_decide_fn's data_point
    already uses.

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
            # See _rsi_momentum_decide's matching 21-Aug-2026 note -
            # reporting-only, skipped for oi_footprint_quote_decide_fn
            # (entry_field="ask") where Entry Premium above already IS
            # the quote.
            new_position["Entry Premium (Quote)"] = data_point.get(f"{option_type.lower()}_ask")

        return f"OPENED {option_type} @ {entry_premium} (OI buildup signal)", new_position, None

    option_type = position["Option Type"]
    current_premium = data_point.get(f"{option_type.lower()}_{exit_field}")

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
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
    }

    if entry_field == "ltp":
        # See new_position's own note above - carried through
        # unchanged from open, reporting only, skipped for
        # oi_footprint_quote_decide_fn.
        exit_quote = data_point.get(f"{option_type.lower()}_bid")
        net_pnl_quote = _quote_net_pnl(cfg, position.get("Entry Premium (Quote)"), exit_quote, position["Lots"])
        trade_record["Entry Premium (Quote)"] = position.get("Entry Premium (Quote)")
        trade_record["Exit Premium (Quote)"] = exit_quote
        trade_record["Net PnL (Quote)"] = round(net_pnl_quote, 2) if net_pnl_quote is not None else None

    return f"CLOSED ({reason}) net {round(net_pnl, 2)}", None, trade_record


def oi_footprint_decide_fn(cfg, position, data_point):
    """
    Faithful event-driven port of oi_footprint's real rules. See this
    module's own header comment above for the OI-signal-precomputed-
    upstream design note. Pure function, per the Shared Backtest-Live
    Engine contract - no I/O, no clock, no network.

    Thin wrapper around _oi_footprint_decide() (added 24-Aug-2026,
    alongside oi_footprint_quote_decide_fn below, for the refactor's
    own reasoning) - Target/Stop-Loss trigger off LTP, same as always.
    Byte-identical to this function's pre-24-Aug-2026 behavior.

    Returns
    -------
    (action, new_position, trade_record)
    """

    return _oi_footprint_decide(cfg, position, data_point, "ltp", "ltp")


def oi_footprint_quote_decide_fn(cfg, position, data_point):
    """
    Added 24-Aug-2026, same reasoning as rsi_momentum_quote_decide_fn's
    own 21-Aug-2026 note - real depth-slippage analysis today found
    oi_footprint_nifty's LTP-based recorded PnL overstates realistic
    (walk-the-book) PnL badly enough that individual trades' sign even
    flips (recorded profit, realistic loss) - the same class of problem
    the RSI-momentum lock books had before their own quote-fix, just
    never ported here. Same OI-signal/lock/circuit-band/squareoff rules
    as oi_footprint_decide_fn (shared via _oi_footprint_decide) - the
    ONLY difference is which data_point field Target/Stop-Loss actually
    trigger off: the real ASK (buying) at entry, the real BID (selling)
    at exit, instead of LTP. Missing/zero ask at entry -> SKIPPED
    (never silently falls back to LTP); missing bid while holding ->
    HELD (waits for the next tick with a real quote).

    Returns
    -------
    (action, new_position, trade_record)
    """

    return _oi_footprint_decide(cfg, position, data_point, "ask", "bid")


def make_oi_footprint_event_cfg(index, lot_size, initial_capital=100000,
                                 hybrid_sl_cap_pct=None, spread_pct=None,
                                 daily_loss_lock=False, max_consecutive_losses=2):
    """
    cfg builder for oi_footprint_decide_fn/oi_footprint_quote_decide_fn.
    hybrid_sl_cap_pct defaults to None (the original fixed Rs 1,500
    Stop-Loss) - pass 2.0 to use the hybrid cap today's cloud-session
    backtest found slightly better for this book (see this module's
    header comment).

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
