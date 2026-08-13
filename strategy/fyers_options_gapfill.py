import datetime
import json
import os

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    DAILY_PROFIT_LOCK_RS,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
    _today_realized_pnl,
)
from strategy.fyers_data import fyers_download
from indicators.atr import calculate_atr

# Added 07/08-Aug-2026 - a genuinely different entry signal from
# simple_st1/st2/st3 (RSI-momentum) and st4 (multi-timeframe+ADX
# trend-continuation): Gap-Fill bets that a significant open-vs-
# previous-close gap REVERTS back toward the previous close during
# the day - the opposite thesis to "the gap continues". Reuses
# strategy/gap_fill_backtest.py's exact rule (25-Jul research - the
# ONE intraday candidate in this project's whole history that landed
# net-positive after real transaction costs on NIFTY, +Rs 413.45/60d,
# 45% win rate - CAVEAT: a split-window check found the edge
# concentrated in the earlier half, not stable across the whole
# window, so this is "promising", not "proven"). Built after 07-Aug's
# finding that simple_st1/st2/st3/st4's shared RSI-momentum entry
# lost broadly across all 8 books on their first real trading day -
# different Target/Stop-Loss ratios didn't help because the ENTRY
# signal itself was the problem, so this strategy deliberately uses a
# different entry mechanism instead of another ratio variant.
#
# Adapted from spot-price terms (the original backtest) to options:
# gap up -> bet on reversion DOWN -> BUY PE; gap down -> bet on
# reversion UP -> BUY CE. Target/Stop-Loss are tracked on the
# UNDERLYING's spot price (Target = previous close, Stop-Loss = ATR-
# based, on the side AWAY from target) - same reasoning as st4: no
# reliable per-contract premium candle history exists to compute
# levels in premium terms directly, and premium/spot are different
# scales anyway.

GAP_THRESHOLD_PCT = 0.3  # matches gap_fill_backtest.py's default
ATR_SL_MULT = 1.0
ATR_PERIOD = 14
SQUAREOFF_TIME = (15, 15)
ENTRY_CUTOFF_TIME = (10, 0)  # a gap-fill bet only makes sense taken
                              # early - by mid-morning the day's real
                              # intraday action has already moved past
                              # the at-open gap dynamics this counts on


def make_gapfill_config(index, name="gapfill", daily_profit_lock=False, group=None):

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "group": group,
        "daily_profit_lock": daily_profit_lock,
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
    """
    Compares today's real Open (the latest daily candle - stable once
    set at market open, doesn't change through the day) against
    yesterday's real Close. No look-ahead: ATR uses only the most
    recently fully-closed daily candle (yesterday's), never today's
    still-forming one.
    """

    daily = fyers_download(cfg["index_symbol_for_rsi"], period="10d", interval="1d")

    if daily is None or len(daily) < 2:
        return None

    today_open = float(daily["Open"].iloc[-1])
    prev_close = float(daily["Close"].iloc[-2])

    if prev_close == 0:
        return None

    atr_series = calculate_atr(daily, period=ATR_PERIOD)
    atr_yesterday = atr_series.iloc[-2]

    if atr_yesterday != atr_yesterday:  # NaN check without importing math
        return None

    gap_pct = (today_open - prev_close) / prev_close * 100

    if abs(gap_pct) < GAP_THRESHOLD_PCT:
        return None

    if gap_pct > 0:
        option_type = "PE"  # gap up -> bet on reversion down
        stop_loss_spot = today_open + float(atr_yesterday) * ATR_SL_MULT
    else:
        option_type = "CE"  # gap down -> bet on reversion up
        stop_loss_spot = today_open - float(atr_yesterday) * ATR_SL_MULT

    return {
        "option_type": option_type,
        "gap_pct": round(gap_pct, 3),
        "target_spot": prev_close,
        "stop_loss_spot": stop_loss_spot,
    }


def _target_hit(option_type, current_spot, target_spot):

    if option_type == "PE":
        return current_spot <= target_spot

    return current_spot >= target_spot


def _stop_loss_hit(option_type, current_spot, stop_loss_spot):

    if option_type == "PE":
        return current_spot >= stop_loss_spot

    return current_spot <= stop_loss_spot


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
        # Added 13-Aug-2026 - see fyers_options_engine.py's matching note.
        "Exit Spot": exit_spot,
        "Gap %": position.get("Gap %"),
        "Exit Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Premium": exit_premium,
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
    })

    portfolio["Position"] = None
    portfolio["Last Trade Date"] = datetime.datetime.now(IST).strftime("%Y-%m-%d")

    return portfolio, f"CLOSED ({reason}) net {round(net_pnl, 2)}"


def _check_position(cfg, portfolio):

    position = portfolio["Position"]
    option_type = position["Option Type"]

    quote = _fetch_quote(position["Symbol"])
    current_premium = quote.get("lp") or (quote.get("bid", 0) + quote.get("ask", 0)) / 2

    spot_quote = _fetch_quote(cfg["underlying_symbol"])
    current_spot = spot_quote.get("lp") or (spot_quote.get("bid", 0) + spot_quote.get("ask", 0)) / 2

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if _target_hit(option_type, current_spot, position["Target Spot"]):
        return _close_position(cfg, portfolio, current_premium, "Target", current_spot)

    if _stop_loss_hit(option_type, current_spot, position["Stop Loss Spot"]):
        return _close_position(cfg, portfolio, current_premium, "Stop Loss", current_spot)

    if past_squareoff:
        return _close_position(cfg, portfolio, current_premium, "Square-Off", current_spot)

    position["Last Premium"] = current_premium
    position["Last Spot"] = current_spot
    position["Last Checked"] = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (spot {current_spot}, target {position['Target Spot']}, sl {position['Stop Loss Spot']})"


def _open_position(cfg, portfolio):

    entry = _entry_signal(cfg)

    if entry is None:
        return portfolio, "SKIPPED (no qualifying gap today)"

    option_type = entry["option_type"]
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
        "Gap %": entry["gap_pct"],
        "Target Spot": entry["target_spot"],
        "Stop Loss Spot": entry["stop_loss_spot"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Spot": spot,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (gap {entry['gap_pct']}%)"


def check_or_open(cfg):
    """
    Call once per check. Opens today's ONE gap-fill trade if none is
    open yet today (only within the early-morning entry window, and
    only if a qualifying gap exists), or checks the open one against
    the spot-based Target/Stop-Loss/Square-Off. Always saves.

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
            action = "SKIPPED (already took today's one gap-fill trade)"
        elif now_hm < MARKET_OPEN_TIME:
            action = "SKIPPED (before market open, pre-open session quotes not tradeable)"
        elif now_hm >= ENTRY_CUTOFF_TIME:
            action = "SKIPPED (past the early-morning gap-fill entry window)"
        elif cfg.get("daily_profit_lock") and _today_realized_pnl(portfolio) >= DAILY_PROFIT_LOCK_RS:
            action = f"SKIPPED (today's profit already Rs {DAILY_PROFIT_LOCK_RS}+, no more new trades today)"
        else:
            portfolio, action = _open_position(cfg, portfolio)

    save_portfolio(cfg, portfolio)

    return portfolio, action
