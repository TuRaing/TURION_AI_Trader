import datetime

from strategy.backtest_live_engine import run_backtest, run_live_check
from strategy.options_transaction_costs import calculate_options_round_trip_cost

# Added 17-Aug-2026 - CODE-PREP for Stage 2 (VPS + Fyers WebSocket),
# per the plan already on record (PROJECT_STATUS.md's "LIVE-DATA
# ARCHITECTURE" entry, 06/07-Aug): this rewrite was always going to be
# needed before Stage 2's event-driven checking, so it is built THROUGH
# strategy/backtest_live_engine.py's decide_fn shape (added 15-Aug,
# unused until now) - one function, reused for both backtest replay and
# live event-driven checking, so there is no second hand-written copy
# to drift out of sync (the exact problem that framework exists to
# prevent). Deliberately starts with ONE strategy (st2_threshold - the
# strongest of the 4 real-data-verified profitable books, see 17-Aug's
# fresh profitability check) as a working, tested prototype rather than
# porting all 4 at once - prove the pattern first.
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
#   }
#
# POSITION SHAPE (what this decide_fn stores as portfolio["Position"]):
#   {"Option Type": "CE"/"PE", "Symbol": str, "Entry Premium": float,
#    "Entry Spot": float, "Entry Time": str, "Lots": int,
#    "Capital Deployed": float}
#
# cfg fields used: lot_size, strike_step (unused here, ATM already
# picked upstream - kept for interface parity), initial_capital,
# target_net_pct, hybrid_sl_cap_pct, spread_pct (opt-in, None = same
# behavior as every live book today - see options_transaction_costs.py).


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


def st2_threshold_decide_fn(cfg, position, data_point):
    """
    Faithful event-driven port of st2_threshold's real rules (RSI>=50 ->
    CE else PE, ATM, Target 5%, hybrid Stop-Loss cap, Square-Off at
    squareoff_time) - see strategy/fyers_options_engine.py's
    make_strategy()/_check_position()/_open_position() for the original
    polling version this must match. Pure function, per the Shared
    Backtest-Live Engine contract - no I/O, no clock, no network.

    Returns
    -------
    (action, new_position, trade_record)
    """

    if position is None:

        if data_point.get("rsi") is None:
            return "SKIPPED (RSI not ready yet)", None, None

        if data_point.get("past_squareoff"):
            return "SKIPPED (past square-off time)", None, None

        option_type = "CE" if data_point["rsi"] >= 50 else "PE"
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
            "Entry Spot": data_point["spot"],
            "Entry Time": data_point["timestamp"],
            "Lots": lots,
            "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        }

        return f"OPENED {option_type} @ {entry_premium}", new_position, None

    option_type = position["Option Type"]
    current_premium = data_point[f"{option_type.lower()}_ltp"]

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

    return f"CLOSED ({reason}) net {round(net_pnl, 2)}", None, trade_record


def make_st2_threshold_event_cfg(index, lot_size, initial_capital=100000,
                                  hybrid_sl_cap_pct=2.0, spread_pct=None):
    """
    cfg builder for st2_threshold_decide_fn - mirrors fyers_options_
    engine.py's make_strategy() field names where they overlap, so a
    real Fyers response can be mapped into a data_point without a
    second translation layer to keep in sync later.
    """

    return {
        "index": index,
        "lot_size": lot_size,
        "initial_capital": initial_capital,
        "target_net_pct": 5.0,
        "stop_loss_pct": 2.0,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "spread_pct": spread_pct,
    }
