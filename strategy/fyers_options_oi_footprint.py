import datetime
import json
import os

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    _fetch_option_chain,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
)

# Added 08-Aug-2026 - user's own idea, reframed against this project's
# "why do things fail" review: retail can never see WHICH institution
# traded WHAT in real time (that data simply isn't published), but a
# big position being built DOES leave a footprint in Open Interest -
# visible live via the option chain, which this project already
# collects (strategy/fyers_options_collector.py). This strategy reads
# that footprint directly instead of trying to infer direction from
# price shape alone (RSI/EMA/ORB - the category that has now failed
# 11/11 times, see doc/PROJECT_STATUS.md's 08-Aug entries).
#
# SIGNAL: the classic OI+Price "buildup" framework (normally applied
# to FUTURES open interest; adapted here to the ATM strike's combined
# CE+PE OI, since Fyers' option chain doesn't expose futures OI
# directly - a real adaptation, not the textbook-exact version):
#
#   Price up   + OI up   -> Long Buildup    -> bullish (BUY CE)
#   Price down + OI up   -> Short Buildup   -> bearish (BUY PE)
#   Price up   + OI down -> Short Covering  -> bullish, weaker (BUY CE)
#   Price down + OI down -> Long Unwinding  -> bearish, weaker (BUY PE)
#
# Only fires when the OI change is large enough to be a real signal,
# not noise (MIN_OI_CHANGE_PCT) - matches this project's own "no
# reliable edge from a single flimsy reading" lesson.
#
# EXIT: fixed, small, quick - the user's own explicit design choice
# ("1k to 2k profit, get out"), not a big directional bet. Rupee-
# based (not percentage) Target/Stop-Loss, unlike simple_st1/st2/st3.

MIN_OI_CHANGE_PCT = 5.0    # minimum combined ATM CE+PE OI change (vs the
                            # previous check) to count as a real signal
TARGET_RUPEES = 1500       # user's explicit ask: Rs 1,000-2,000, small
                            # and quick, not a big move
STOP_LOSS_RUPEES = 1500    # symmetric - keeps the "in and out, don't
                            # overstay" philosophy simple and disciplined
SQUAREOFF_TIME = (15, 15)


def make_oi_footprint_config(index, name="oi_footprint"):

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "portfolio_file": f"reports/fyers_options_{name}_{index.lower()}_portfolio.json",
        "underlying_symbol": index_cfg["underlying_symbol"],
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
            "Last OI Snapshot": None,
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


def _read_atm_oi_snapshot(cfg):
    """
    Live snapshot of spot + the ATM strike's CE/PE Open Interest - the
    "institutional footprint" proxy this strategy watches. Returns None
    if the option chain fetch fails or the ATM legs aren't found.
    """

    chain = _fetch_option_chain(cfg)
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        return None

    atm_strike = round(spot / cfg["strike_step"]) * cfg["strike_step"]

    ce_oi = next((leg.get("oi") for leg in legs
                  if leg.get("strike_price") == atm_strike and leg.get("option_type") == "CE"), None)
    pe_oi = next((leg.get("oi") for leg in legs
                  if leg.get("strike_price") == atm_strike and leg.get("option_type") == "PE"), None)

    if ce_oi is None or pe_oi is None:
        return None

    return {"spot": spot, "strike": atm_strike, "ce_oi": ce_oi, "pe_oi": pe_oi}


def _classify_buildup(previous, current):
    """
    Pure function - the OI+Price buildup classification described in
    the module docstring. Needs a previous snapshot AT THE SAME ATM
    strike (a strike change between checks means no valid comparison -
    the spot moved enough to shift ATM, treat as no signal this check).

    Returns "CE", "PE", or None (no previous snapshot, strike changed,
    or the OI change was too small to trust).
    """

    if previous is None or previous.get("strike") != current["strike"]:
        return None

    previous_total_oi = previous["ce_oi"] + previous["pe_oi"]

    if previous_total_oi == 0:
        return None

    price_change = current["spot"] - previous["spot"]
    oi_change = (current["ce_oi"] + current["pe_oi"]) - previous_total_oi
    oi_change_pct = abs(oi_change) / previous_total_oi * 100

    if oi_change_pct < MIN_OI_CHANGE_PCT:
        return None

    if price_change > 0 and oi_change > 0:
        return "CE"   # Long Buildup

    if price_change < 0 and oi_change > 0:
        return "PE"   # Short Buildup

    if price_change > 0 and oi_change < 0:
        return "CE"   # Short Covering

    if price_change < 0 and oi_change < 0:
        return "PE"   # Long Unwinding

    return None


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

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if net_pnl >= TARGET_RUPEES:
        return _close_position(cfg, portfolio, current_premium, "Target", current_spot)

    if net_pnl <= -STOP_LOSS_RUPEES:
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

    # Always refresh the baseline for next check, whether or not this
    # one produced a trade - a stale multi-check-old baseline would
    # make the NEXT comparison meaningless too.
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
    Call once per check. Opens a position if none is open (OI-buildup
    signal, market-hours gated), or checks the open one against the
    fixed Rs 1,500 Target/Stop-Loss/Square-Off. Always saves. No one-
    trade-per-day cap - "quick in and out" naturally means several
    short trades a day are expected, gated only by the MIN_OI_CHANGE_PCT
    noise filter, not a daily count.

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

        if now_hm < MARKET_OPEN_TIME:
            action = "SKIPPED (before market open, pre-open session quotes not tradeable)"
        elif now_hm >= SQUAREOFF_TIME:
            action = "SKIPPED (past square-off time, market closed or about to close)"
        else:
            portfolio, action = _open_position(cfg, portfolio)

    save_portfolio(cfg, portfolio)

    return portfolio, action
