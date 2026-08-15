import datetime

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
    _hybrid_stop_loss_cap,
)
from strategy.fyers_options_oi_footprint import (
    TARGET_RUPEES,
    SQUAREOFF_TIME,
    _read_atm_oi_snapshot,
    _classify_buildup,
    load_portfolio,
    save_portfolio,
)
from strategy.fyers_data import fyers_download
from indicators.rsi import calculate_rsi

# Added 14-Aug-2026 - 6 oi_footprint variants requested after the
# profit-booking-filter research (doc/PROJECT_STATUS.md's "oi_footprint
# EXIT-MECHANISM DEEP DIVE" + "CIRCUIT-BREAKER..." entries) found the
# hybrid Stop-Loss cap has strong, full-sample retrospective evidence,
# but Trailing-Stop / Breakeven / Laddered / ATR-scaling / Indicator-
# based exits could NOT be properly backtested - oi_footprint's real
# trades are too short (0.6-8.9 min) for the available historical
# price-snapshot data (5-min resolution) to reconstruct a trade's
# internal path. Built here as LIVE paper-trading variants instead,
# since that limitation is a HISTORICAL-DATA problem, not a live-
# checking one - going forward, each variant's own real checks will
# see real prices as they happen, giving a genuine (not retrospective)
# test of each idea. strategy/fyers_options_oi_footprint.py itself is
# COMPLETELY UNTOUCHED - reuses its entry signal (_read_atm_oi_
# snapshot/_classify_buildup) unchanged, per this repo's "never modify
# a working module" rule.
#
# All 6 variants share the SAME entry signal and the SAME hybrid Stop-
# Loss cap (see fyers_options_engine.py's _hybrid_stop_loss_cap - the
# same one built for the RSI-family _slcap books). Only ONE additional
# exit idea is layered on top of each, per the user's own list - never
# combined with each other, to keep each variant a clean, isolated test
# of exactly one idea:
#
#   io_hybrid_sl              - hybrid SL cap only, otherwise identical
#                                to the original (Target still lets
#                                profit run, per the "MAJOR CORRECTION"
#                                finding that overshoot-on-the-profit-
#                                side has been net-beneficial).
#   io_hybrid_sl_trailing     - + once Target is first reached, don't
#                                close immediately - trail a stop at
#                                TRAIL_PCT below the peak profit seen,
#                                instead of exiting at the very first
#                                crossing.
#   io_hybrid_sl_atr          - + the hybrid cap itself is scaled by
#                                today's real ATR14 vs. a rolling
#                                average (same method as the
#                                retrospective ATR test, just live).
#   io_hybrid_sl_breakeven    - + once profit ever reaches BREAKEVEN_
#                                TRIGGER_RUPEES, the position can never
#                                be allowed to close at a net loss again
#                                (closes at breakeven instead).
#   io_hybrid_sl_laddered     - + books HALF the position once profit
#                                reaches LADDER_HALF_AT_PCT of Target,
#                                letting the other half continue toward
#                                the full Target/hybrid-SL on its own.
#   io_hybrid_sl_indicator    - + exits early if the underlying's RSI
#                                crosses back through 50 against the
#                                position's direction, even before
#                                Target/Stop-Loss is hit.

HYBRID_SL_CAP_PCT = 2.0
TRAIL_PCT = 0.30                 # once Target is first reached, give back at most 30% of the peak before exiting
BREAKEVEN_TRIGGER_RUPEES = 750   # half of TARGET_RUPEES - once profit reaches this, never let the trade turn negative
LADDER_HALF_AT_PCT = 0.5         # book half the position once profit reaches 50% of TARGET_RUPEES
RSI_NEUTRAL = 50


def make_oi_footprint_variant_config(index, name, extra_exit=None):
    """
    `extra_exit` - one of None, "trailing", "atr", "breakeven",
    "laddered", "indicator" - see the module docstring above. None
    means hybrid-SL-cap-only (io_hybrid_sl).
    """

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "extra_exit": extra_exit,
        "hybrid_sl_cap_pct": HYBRID_SL_CAP_PCT,
        "portfolio_file": f"reports/fyers_options_{name}_{index.lower()}_portfolio.json",
        "underlying_symbol": index_cfg["underlying_symbol"],
        "index_symbol_for_rsi": index_cfg["index_symbol_for_rsi"],
        "lot_size": index_cfg["lot_size"],
        "strike_step": index_cfg["strike_step"],
        "initial_capital": 100000,
    }


def _atr_scale(cfg):
    """
    Today's real ATR14 for the underlying vs. a rolling ~1-month
    average - same method as the retrospective ATR test in PROJECT_
    STATUS.md. Returns 1.0 (no scaling) if data isn't available, so a
    network hiccup degrades to the plain hybrid cap instead of crashing.
    """

    frame = fyers_download(cfg["index_symbol_for_rsi"], period="1mo", interval="1d")

    if frame is None or len(frame) < 15:
        return 1.0

    high_low = frame["High"] - frame["Low"]
    high_prev_close = (frame["High"] - frame["Close"].shift(1)).abs()
    low_prev_close = (frame["Low"] - frame["Close"].shift(1)).abs()
    true_range = high_low.combine(high_prev_close, max).combine(low_prev_close, max)
    atr14 = true_range.rolling(14).mean()

    latest_atr = atr14.iloc[-1]
    average_atr = atr14.dropna().mean()

    if not average_atr or average_atr <= 0 or latest_atr != latest_atr:  # NaN check
        return 1.0

    return float(latest_atr / average_atr)


def _current_rsi(cfg):

    frame = fyers_download(cfg["index_symbol_for_rsi"], period="60d", interval="5m")

    if frame is None or frame.empty:
        return None

    rsi = calculate_rsi(frame)

    return float(rsi.iloc[-1])


def _partial_close(cfg, portfolio, exit_premium, exit_spot, lots_to_close):

    position = portfolio["Position"]
    partial_pnl = _net_pnl(cfg, position["Entry Premium"], exit_premium, lots_to_close)

    portfolio["Cash"] += partial_pnl

    portfolio["Closed Trades"].append({
        "Symbol": position["Symbol"],
        "Strike": position["Strike"],
        "Option Type": position["Option Type"],
        "Entry Time": position["Entry Time"],
        "Entry Premium": position["Entry Premium"],
        "Entry Spot": position.get("Entry Spot"),
        "Exit Spot": exit_spot,
        "Entry CE OI": position.get("Entry CE OI"),
        "Entry PE OI": position.get("Entry PE OI"),
        "Exit Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Premium": exit_premium,
        "Lots": lots_to_close,
        "Exit Reason": "Partial Target",
        "Net PnL": round(partial_pnl, 2),
        "Net PnL %": round(partial_pnl / cfg["initial_capital"] * 100, 3),
    })

    position["Lots"] -= lots_to_close
    position["Quantity"] = position["Lots"] * cfg["lot_size"]
    position["Partial Booked"] = True

    return portfolio


def _close_position(cfg, portfolio, exit_premium, reason, exit_spot=None):

    position = portfolio["Position"]
    net_pnl = _net_pnl(cfg, position["Entry Premium"], exit_premium, position["Lots"])

    portfolio["Cash"] += net_pnl

    portfolio["Closed Trades"].append({
        "Symbol": position["Symbol"],
        "Strike": position["Strike"],
        "Option Type": position["Option Type"],
        "Entry Time": position["Entry Time"],
        "Entry Premium": position["Entry Premium"],
        "Entry Spot": position.get("Entry Spot"),
        "Exit Spot": exit_spot,
        "Entry CE OI": position.get("Entry CE OI"),
        "Entry PE OI": position.get("Entry PE OI"),
        "Exit Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Premium": exit_premium,
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
    })

    portfolio["Position"] = None

    return portfolio, f"CLOSED ({reason}) net {round(net_pnl, 2)}"


def _check_position(cfg, portfolio):

    position = portfolio["Position"]

    quote = _fetch_quote(position["Symbol"])
    current_premium = quote.get("lp") or (quote.get("bid", 0) + quote.get("ask", 0)) / 2

    underlying_quote = _fetch_quote(cfg["underlying_symbol"])
    current_spot = underlying_quote.get("lp") or (underlying_quote.get("bid", 0) + underlying_quote.get("ask", 0)) / 2

    net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])

    peak_pnl = max(position.get("Peak PnL", net_pnl), net_pnl)
    position["Peak PnL"] = peak_pnl

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    extra_exit = cfg.get("extra_exit")

    # --- laddered: book half at half-target, exactly once ---
    if extra_exit == "laddered" and not position.get("Partial Booked") \
            and net_pnl >= TARGET_RUPEES * LADDER_HALF_AT_PCT:
        lots_to_close = position["Lots"] // 2
        if lots_to_close >= 1:
            portfolio = _partial_close(cfg, portfolio, current_premium, current_spot, lots_to_close)
            position = portfolio["Position"]
            net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])

    # --- indicator-based: exit early on an RSI reversal against the position ---
    if extra_exit == "indicator":
        rsi = _current_rsi(cfg)
        if rsi is not None:
            reversed_against_ce = position["Option Type"] == "CE" and rsi < RSI_NEUTRAL
            reversed_against_pe = position["Option Type"] == "PE" and rsi > RSI_NEUTRAL
            if reversed_against_ce or reversed_against_pe:
                return _close_position(cfg, portfolio, current_premium, "Indicator Exit", current_spot)

    # --- breakeven: once ever profitable enough, never allow a net loss ---
    if extra_exit == "breakeven" and peak_pnl >= BREAKEVEN_TRIGGER_RUPEES and net_pnl <= 0:
        return _close_position(cfg, portfolio, current_premium, "Stop Loss (Breakeven)", current_spot)

    # --- trailing: once Target is first reached, trail instead of exiting immediately ---
    if extra_exit == "trailing" and peak_pnl >= TARGET_RUPEES:
        trail_floor = peak_pnl * (1 - TRAIL_PCT)
        if net_pnl <= trail_floor:
            return _close_position(cfg, portfolio, current_premium, "Trailing Stop", current_spot)
    elif net_pnl >= TARGET_RUPEES:
        return _close_position(cfg, portfolio, current_premium, "Target", current_spot)

    # --- hybrid Stop-Loss cap (every variant), optionally ATR-scaled ---
    stop_loss_cap = _hybrid_stop_loss_cap(cfg, position["Capital Deployed"])
    if extra_exit == "atr":
        stop_loss_cap *= _atr_scale(cfg)

    if net_pnl <= -stop_loss_cap:
        return _close_position(cfg, portfolio, current_premium, "Stop Loss", current_spot)

    if past_squareoff:
        return _close_position(cfg, portfolio, current_premium, "Square-Off", current_spot)

    position["Last Premium"] = current_premium
    position["Last Checked"] = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (net {round(net_pnl, 2)})"


def _open_position(cfg, portfolio):

    current = _read_atm_oi_snapshot(cfg)

    if current is None:
        return portfolio, "SKIPPED (could not read option chain OI)"

    previous = portfolio.get("Last OI Snapshot")
    option_type = _classify_buildup(previous, current)

    portfolio["Last OI Snapshot"] = current

    if option_type is None:
        return portfolio, f"SKIPPED (no meaningful OI buildup - spot {current['spot']}, strike {current['strike']})"

    leg, spot = _pick_atm_leg(cfg, option_type)
    entry_premium = leg.get("ltp") or (leg.get("bid", 0) + leg.get("ask", 0)) / 2

    if not entry_premium or entry_premium <= 0:
        return portfolio, "SKIPPED (no valid premium quote)"

    lots = int(portfolio["Cash"] // (entry_premium * cfg["lot_size"]))

    if lots < 1:
        return portfolio, f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})"

    now = datetime.datetime.now()

    portfolio["Position"] = {
        "Symbol": leg["symbol"],
        "Strike": leg["strike_price"],
        "Option Type": option_type,
        "Entry Time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Spot": spot,
        "Entry Premium": entry_premium,
        "Entry CE OI": current["ce_oi"],
        "Entry PE OI": current["pe_oi"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (OI buildup signal)"


def check_or_open(cfg):
    """
    Same call contract as fyers_options_oi_footprint.py's check_or_open
    - see this module's docstring for what differs.
    """

    portfolio = load_portfolio(cfg)

    if portfolio["Position"] is not None:
        portfolio, action = _check_position(cfg, portfolio)
    else:

        now_ist = datetime.datetime.now(IST)
        now_hm = (now_ist.hour, now_ist.minute)

        if now_hm < MARKET_OPEN_TIME:
            action = "SKIPPED (before market open, pre-open session quotes not tradeable)"
        elif now_hm >= SQUAREOFF_TIME:
            action = "SKIPPED (past square-off time, market closed or about to close)"
        else:
            portfolio, action = _open_position(cfg, portfolio)

    save_portfolio(cfg, portfolio)

    return portfolio, action
