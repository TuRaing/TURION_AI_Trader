import datetime
import json
import os

import pandas as pd

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    DAILY_PROFIT_LOCK_RS,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
    _today_realized_pnl,
    _hybrid_stop_loss_cap,
)
from strategy.fyers_data import fyers_download
from strategy.fyers_multi_timeframe_engine import get_multi_timeframe_signal
from indicators.adx import calculate_adx

# Added 06-Aug-2026 - st4, the fourth of the user's requested options
# strategies: only ONE trade per day, waiting for a genuinely high-
# confidence setup instead of trading every check. Needs materially
# different entry/exit logic from strategy/fyers_options_engine.py's
# generic RSI-momentum core (simple_st1/st2/st3), so it's its own
# module - reuses that engine's option-chain/quote/cost helpers
# rather than duplicating them.
#
# Design (agreed with the user 06-Aug, after discussing the
# tradeoffs): reuse this project's own two most-validated filters
# instead of inventing an untested one -
#   - Entry: 15m/5m/1m multi-timeframe alignment (strategy/fyers_
#     multi_timeframe_engine.py) AND 15m ADX > 25 - ADX>25 was "the
#     clearest single improvement found" in this project's 25-Jul
#     research (78% less negative, win rate 45%->83%). Both together
#     is deliberately selective - most checks are expected to fire
#     nothing, by design (one good trade, not a trade every check).
#   - Once net profit crosses TRAIL_TRIGGER_RUPEES, switch from a
#     fixed initial Stop-Loss to a trailing stop on the UNDERLYING's
#     spot price (not the option premium - Fyers has no reliable
#     historical/intraday candle series for an individual option
#     contract to compute its own ATR from, but the underlying's ATR
#     is already reliably available). Trail distance is 1.0x the
#     entry-time 5m ATR - 24-Jul's own tuning found this the best
#     trailing distance for this style of trend-continuation trade.
#   - Before the trigger, a fixed INITIAL_STOP_LOSS_PCT protects
#     against an early adverse move.
#   - Exactly one trade per calendar day (Last Trade Date field) -
#     once closed (any reason), no new entry until tomorrow.

ADX_THRESHOLD = 25
INITIAL_STOP_LOSS_PCT = 3.0
TRAIL_TRIGGER_RUPEES = 1000
TRAIL_ATR_MULT = 1.0
SQUAREOFF_TIME = (15, 15)


def make_st4_config(index, name="st4", daily_profit_lock=False, group=None, hybrid_sl_cap_pct=None):
    """
    `hybrid_sl_cap_pct` (added 14-Aug-2026) - when set, replaces the
    plain INITIAL_STOP_LOSS_PCT check (before the trailing stop
    activates) with min(flat, %-of-deployed) - see fyers_options_
    engine.py's _hybrid_stop_loss_cap() and PROJECT_STATUS.md's
    "HYBRID SL CAP" entry. Does NOT change the trailing-stop phase
    (that's already spot-based, a different mechanism entirely) -
    only the initial protective Stop-Loss before TRAIL_TRIGGER_RUPEES
    is reached. Default None keeps the original behavior unchanged.
    """

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "group": group,
        "daily_profit_lock": daily_profit_lock,
        "hybrid_sl_cap_pct": hybrid_sl_cap_pct,
        "portfolio_file": f"reports/fyers_options_{name}_{index.lower()}_portfolio.json",
        "underlying_symbol": index_cfg["underlying_symbol"],
        "index_symbol_for_rsi": index_cfg["index_symbol_for_rsi"],
        "lot_size": index_cfg["lot_size"],
        "strike_step": index_cfg["strike_step"],
        "initial_capital": 100000,
    }


def load_portfolio(cfg):

    if not os.path.exists(cfg["portfolio_file"]):

        return {
            "Cash": cfg["initial_capital"],
            "Position": None,
            "Closed Trades": [],
            "Last Trade Date": None,
            "Data Source": "Fyers (real premium)",
            "Strategy": cfg["name"],
            "Index": cfg["index"],
        }

    with open(cfg["portfolio_file"], "r") as f:
        return json.load(f)


def save_portfolio(cfg, portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(cfg["portfolio_file"], "w") as f:
        json.dump(portfolio, f, indent=2)


def _entry_signal(cfg):

    signal = get_multi_timeframe_signal(cfg["index"], cfg["index_symbol_for_rsi"])

    if not signal.get("Aligned") or signal.get("Decision") not in ("BUY", "SELL"):
        return None

    frame_15m = fyers_download(cfg["index_symbol_for_rsi"], period="60d", interval="15m")

    if frame_15m is None or frame_15m.empty:
        return None

    adx = calculate_adx(frame_15m)

    if adx.empty or pd.isna(adx.iloc[-1]) or float(adx.iloc[-1]) <= ADX_THRESHOLD:
        return None

    return {
        "option_type": "CE" if signal["Decision"] == "BUY" else "PE",
        "spot_atr": signal["ATR"],
        "adx": round(float(adx.iloc[-1]), 2),
    }


def _trailing_stop_hit(option_type, current_spot, peak_spot, trail_distance):
    """
    Pure logic, kept separate for testability. CE trails below the
    best (highest) spot seen since entry; PE trails above the best
    (lowest) spot seen.
    """

    if option_type == "CE":
        return current_spot <= (peak_spot - trail_distance)

    return current_spot >= (peak_spot + trail_distance)


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
        # Added 06-Aug-2026 - so the app can show the underlying's spot
        # price as a chart reference line for closed trades too. Also
        # keep Peak Spot - the level the trailing stop was actually
        # trailing behind, useful chart context for st4 specifically.
        "Entry Spot": position.get("Entry Spot"),
        "Peak Spot": position.get("Peak Spot"),
        # Added 13-Aug-2026 - see fyers_options_engine.py's matching
        # note - needed to later split a premium move into its Delta
        # vs Theta component.
        "Exit Spot": exit_spot,
        # Stored as naive/local time (UTC on the GitHub Actions runner),
        # matching every other engine's convention - see the same-day
        # fix note in fyers_options_paper_trading.py.
        "Exit Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Premium": exit_premium,
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
    })

    portfolio["Position"] = None
    # Last Trade Date IS deliberately IST, unlike the timestamps above -
    # it's compared against IST wall-clock "today" for the one-trade-
    # per-day gate (check_or_open), never shown in the app.
    portfolio["Last Trade Date"] = datetime.datetime.now(IST).strftime("%Y-%m-%d")

    return portfolio, f"CLOSED ({reason}) net {round(net_pnl, 2)}"


def _check_position(cfg, portfolio):

    position = portfolio["Position"]
    option_type = position["Option Type"]

    quote = _fetch_quote(position["Symbol"])
    current_premium = quote.get("lp") or (quote.get("bid", 0) + quote.get("ask", 0)) / 2

    spot_quote = _fetch_quote(cfg["underlying_symbol"])
    current_spot = spot_quote.get("lp") or (spot_quote.get("bid", 0) + spot_quote.get("ask", 0)) / 2

    net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if option_type == "CE":
        position["Peak Spot"] = max(position.get("Peak Spot", position["Entry Spot"]), current_spot)
    else:
        position["Peak Spot"] = min(position.get("Peak Spot", position["Entry Spot"]), current_spot)

    if not position.get("Trailing Active") and net_pnl >= TRAIL_TRIGGER_RUPEES:
        position["Trailing Active"] = True

    if position.get("Trailing Active"):

        trail_distance = TRAIL_ATR_MULT * position["Entry ATR"]

        if _trailing_stop_hit(option_type, current_spot, position["Peak Spot"], trail_distance):
            return _close_position(cfg, portfolio, current_premium, "Trailing Stop", current_spot)

    elif cfg.get("hybrid_sl_cap_pct") is not None:

        stop_loss_cap = _hybrid_stop_loss_cap(cfg, position["Capital Deployed"])

        if net_pnl <= -stop_loss_cap:
            return _close_position(cfg, portfolio, current_premium, "Stop Loss", current_spot)

    else:

        net_pnl_pct = net_pnl / cfg["initial_capital"] * 100

        if net_pnl_pct <= -INITIAL_STOP_LOSS_PCT:
            return _close_position(cfg, portfolio, current_premium, "Stop Loss", current_spot)

    if past_squareoff:
        return _close_position(cfg, portfolio, current_premium, "Square-Off", current_spot)

    position["Last Premium"] = current_premium
    position["Last Spot"] = current_spot
    position["Last Checked"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    trailing = position.get("Trailing Active", False)
    return portfolio, f"HOLD (net {round(net_pnl, 2)}, trailing={trailing})"


def _open_position(cfg, portfolio):

    entry = _entry_signal(cfg)

    if entry is None:
        return portfolio, "SKIPPED (no aligned 15m/5m/1m + ADX>25 setup)"

    option_type = entry["option_type"]
    leg, spot = _pick_atm_leg(cfg, option_type)

    entry_premium = leg.get("ltp") or (leg.get("bid", 0) + leg.get("ask", 0)) / 2

    if not entry_premium or entry_premium <= 0:
        return portfolio, "SKIPPED (no valid premium quote)"

    lots = int(portfolio["Cash"] // (entry_premium * cfg["lot_size"]))

    if lots < 1:
        return portfolio, f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})"

    # Stored as naive/local time (UTC on the GitHub Actions runner),
    # matching every other engine's convention - see the same-day fix
    # note in fyers_options_paper_trading.py.
    now = datetime.datetime.now()

    portfolio["Position"] = {
        "Symbol": leg["symbol"],
        "Strike": leg["strike_price"],
        "Option Type": option_type,
        "Entry Time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Spot": spot,
        "Entry Premium": entry_premium,
        "Entry ATR": entry["spot_atr"],
        "Entry ADX": entry["adx"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Peak Spot": spot,
        "Trailing Active": False,
        "Last Premium": entry_premium,
        "Last Spot": spot,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (ADX {entry['adx']})"


def check_or_open(cfg):
    """
    Call once per check. Opens today's ONE trade if none is open yet
    today (multi-timeframe + ADX>25 alignment required, skipped
    outside market hours), or checks the open one against the fixed
    initial Stop-Loss / trailing stop / Square-Off. Always saves.

    Returns
    -------
    portfolio : dict
    action : str
    """

    portfolio = load_portfolio(cfg)

    if portfolio["Position"] is not None:
        portfolio, action = _check_position(cfg, portfolio)
    else:

        now_ist = datetime.datetime.now(IST)
        now_hm = (now_ist.hour, now_ist.minute)
        today_str = now_ist.strftime("%Y-%m-%d")

        if portfolio.get("Last Trade Date") == today_str:
            action = "SKIPPED (already took today's one trade)"
        elif now_hm < MARKET_OPEN_TIME:
            action = "SKIPPED (before market open, pre-open session quotes not tradeable)"
        elif now_hm >= SQUAREOFF_TIME:
            action = "SKIPPED (past square-off time, market closed or about to close)"
        elif cfg.get("daily_profit_lock") and _today_realized_pnl(portfolio) >= DAILY_PROFIT_LOCK_RS:
            action = f"SKIPPED (today's profit already Rs {DAILY_PROFIT_LOCK_RS}+, no more new trades today)"
        else:
            portfolio, action = _open_position(cfg, portfolio)

    save_portfolio(cfg, portfolio)

    return portfolio, action
