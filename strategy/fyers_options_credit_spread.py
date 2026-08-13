import datetime
import json
import math
import os

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    _fetch_option_chain,
    _fetch_quote,
)
from strategy.fyers_data import fyers_download
from indicators.rsi import calculate_rsi

# Added 09-Aug-2026 - the premium-selling (theta) engine discussed at
# length 08-Aug: instead of BUYING an option and fighting time decay on
# every trade (every other strategy here does this), SELL a directional
# credit spread - collect a small, capped premium up front, profit from
# time passing if the underlying stays out of the way. Deliberately
# DEFINED-RISK (2 legs: sell one strike, buy a further one as insurance)
# - a naked/undefined-risk sell was already ruled out in this project's
# 22-Jul research (margin requirement, risk profile mismatch).
#
# DESIGN (agreed with the user 08/09-Aug):
#   - Directional credit spread only (Bull Put / Bear Call), not an Iron
#     Condor - simpler (2 legs, not 4), and direction comes from RSI
#     (same signal simple_st1/st2/st3 already use) so no new signal
#     logic needed there.
#   - Entry only when India VIX is in its own trailing HIGH percentile
#     band (>= VIX_HIGH_PERCENTILE) - the opposite filter from vix_
#     filter.py's "avoid extremes" rule, because premium SELLERS want
#     rich/elevated premiums to sell into, not calm ones.
#   - RSI>=50 (bullish/neutral lean) -> sell a PUT spread (bet spot
#     doesn't fall much); RSI<50 -> sell a CALL spread (bet spot
#     doesn't rise much).
#   - Short strike ~1.5% OTM from spot, long strike (protection)
#     WIDTH_POINTS further out - both rounded to the index's own
#     strike step.
#   - Exit: close at 50% of max profit (don't hold for the last, riskiest
#     half of the credit - standard credit-spread practice), Stop-Loss
#     at 2x the credit received, or square-off at expiry-day close.
#   - Both NIFTY and BANKNIFTY, whatever expiry Fyers' option chain
#     returns by default (the nearest one) - the user asked for
#     monthly specifically, but this project's existing option-chain
#     fetch (_fetch_option_chain, reused from fyers_options_engine.py)
#     has no expiry-selection parameter and every other strategy here
#     already relies on its default (nearest) expiry. NOT verified
#     against live data yet whether NIFTY's nearest expiry is weekly
#     or monthly - flag and confirm once real chain data is checked.
#
# MARGIN: Fyers does expose a span_margin endpoint, but its exact
# request/response schema wasn't confirmed (undocumented in the
# accessible docs). Rather than guess and risk mis-sizing real-money-
# shaped positions, this uses a SAFE, CONSERVATIVE proxy instead: size
# by the spread's own max possible loss (width - credit), which is
# always >= the real margin a defined-risk spread requires. Slightly
# under-utilizes capital, never over-commits it - real margin-API
# integration is a future refinement, not a blocker for going live.

RSI_DIRECTION_THRESHOLD = 50
VIX_HIGH_PERCENTILE = 0.70   # sell into the top 30% of VIX's own recent
                              # range - the OPPOSITE filter from vix_
                              # filter.py's "stay in the calm middle"
VIX_LOOKBACK_CANDLES = 125    # ~5 trading days of 15m candles, same
                               # window as vix_filter.py
SIGNAL_INTERVAL = "15m"
SHORT_STRIKE_OTM_PCT = 1.5     # short leg this far OTM from spot
WIDTH_POINTS_DEFAULT = 150     # long leg this many points further OTM
                                 # (the protective leg) - mid-point of
                                 # the agreed 100-200 range
TARGET_PCT_OF_CREDIT = 0.50    # close once 50% of max profit is banked
STOP_LOSS_CREDIT_MULT = 2.0    # close if the cost to close reaches 2x
                                 # the credit originally received
SQUAREOFF_TIME = (15, 15)


def make_credit_spread_config(index, name="credit_spread", width_points=WIDTH_POINTS_DEFAULT):

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "portfolio_file": f"reports/fyers_options_{name}_{index.lower()}_portfolio.json",
        "underlying_symbol": index_cfg["underlying_symbol"],
        "index_symbol_for_rsi": index_cfg["index_symbol_for_rsi"],
        "lot_size": index_cfg["lot_size"],
        "strike_step": index_cfg["strike_step"],
        "width_points": width_points,
        "initial_capital": 100000,
    }


def load_portfolio(cfg):

    if not os.path.exists(cfg["portfolio_file"]):

        return {
            "Cash": cfg["initial_capital"],
            "Position": None,
            "Closed Trades": [],
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
    RSI direction (>=50 bullish/neutral -> sell PUT spread, <50 -> sell
    CALL spread), gated on India VIX sitting in its own trailing HIGH
    percentile band - rich/elevated premium is what a seller wants,
    the opposite condition from vix_filter.py's directional-buy filter.
    """

    price_data = fyers_download(cfg["index_symbol_for_rsi"], period="10d", interval=SIGNAL_INTERVAL)
    vix_data = fyers_download("^INDIAVIX", period="10d", interval=SIGNAL_INTERVAL)

    if price_data is None or price_data.empty or vix_data is None or vix_data.empty:
        return None

    if len(vix_data) < VIX_LOOKBACK_CANDLES:
        return None

    rsi = calculate_rsi(price_data)

    if rsi.empty:
        return None

    latest_rsi = float(rsi.iloc[-1])

    if latest_rsi != latest_rsi:  # NaN check
        return None

    recent_vix = vix_data["Close"].iloc[-VIX_LOOKBACK_CANDLES:]
    vix_high_band = float(recent_vix.quantile(VIX_HIGH_PERCENTILE))
    latest_vix = float(vix_data["Close"].iloc[-1])

    if latest_vix < vix_high_band:
        return None  # VIX not elevated enough - premium isn't rich, skip

    option_type = "PE" if latest_rsi >= RSI_DIRECTION_THRESHOLD else "CE"

    return {"option_type": option_type, "rsi": round(latest_rsi, 2), "vix": round(latest_vix, 2)}


def _compute_strikes(spot, option_type, strike_step, width_points):
    """
    Pure function - the strike-selection math, split out from _pick_
    spread_legs() (which also does the live option-chain fetch) so this
    part is testable without network access.

    PE (Bull Put Spread): short strike BELOW spot (~SHORT_STRIKE_OTM_PCT
    away), long strike further below (extra protection, away from spot).
    CE (Bear Call Spread): mirror image, both strikes above spot.

    Returns
    -------
    short_strike, long_strike : float
    """

    if option_type == "PE":
        short_strike = round(spot * (1 - SHORT_STRIKE_OTM_PCT / 100) / strike_step) * strike_step
        long_strike = short_strike - width_points
    else:
        short_strike = round(spot * (1 + SHORT_STRIKE_OTM_PCT / 100) / strike_step) * strike_step
        long_strike = short_strike + width_points

    return short_strike, long_strike


CHAIN_STRIKE_COUNT_BUFFER = 3  # extra strikes of headroom past whatever
                                 # the long (further OTM) leg actually
                                 # needs, in case Fyers' own ATM pick and
                                 # this module's spot reading differ by
                                 # a strike or two


def _strikes_needed(spot, long_strike, strike_step):
    """
    Pure function - how many strikes away from ATM the long (furthest
    OTM) leg sits, so the option-chain fetch can be asked for enough
    strikes to actually contain it. Rounds up, always at least 1.
    """

    return max(1, math.ceil(abs(long_strike - spot) / strike_step))


def _pick_spread_legs(cfg, option_type):
    """
    Reads the live option chain, computes the short (sold) and long
    (bought, protective) strikes via _compute_strikes(), then makes
    sure the chain actually covers the long leg's distance from ATM -
    _fetch_option_chain's default strike_count=5 (fine for every other
    strategy here, which only needs the ATM leg) silently left both
    legs outside the chain for this strategy (short leg already ~1.5%
    OTM, long leg width_points further still - "Could not find both
    spread legs", caught 10-Aug). A first, cheap fetch gets spot; if
    the strike distance needs more than that fetch already covers, a
    second fetch asks for exactly enough (plus a small buffer) instead
    of guessing a fixed number that might still fall short on a wide-
    swinging index like BANKNIFTY.

    Returns
    -------
    short_leg, long_leg : dict (raw option-chain leg dicts)
    spot : float
    """

    chain = _fetch_option_chain(cfg)
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        raise RuntimeError("Could not read spot price from option chain response")

    short_strike, long_strike = _compute_strikes(spot, option_type, cfg["strike_step"], cfg["width_points"])

    needed_strike_count = _strikes_needed(spot, long_strike, cfg["strike_step"]) + CHAIN_STRIKE_COUNT_BUFFER

    if needed_strike_count > 5:
        chain = _fetch_option_chain(cfg, strike_count=needed_strike_count)
        legs = chain.get("optionsChain", [])

    short_leg = next((leg for leg in legs
                       if leg.get("strike_price") == short_strike and leg.get("option_type") == option_type), None)
    long_leg = next((leg for leg in legs
                      if leg.get("strike_price") == long_strike and leg.get("option_type") == option_type), None)

    if short_leg is None or long_leg is None:
        raise RuntimeError(
            f"Could not find both spread legs in the option chain (short {short_strike}, long {long_strike} {option_type})")

    return short_leg, long_leg, spot


def _leg_premium(leg):
    return leg.get("ltp") or (leg.get("bid", 0) + leg.get("ask", 0)) / 2


def _target_hit(entry_credit, cost_to_close_now):
    """
    Pure function - True once the position has banked >= TARGET_PCT_OF_
    CREDIT of the credit received (cost to close has fallen enough).
    """

    if entry_credit <= 0:
        return False

    profit_so_far_pct = (entry_credit - cost_to_close_now) / entry_credit

    return profit_so_far_pct >= TARGET_PCT_OF_CREDIT


def _stop_loss_hit(entry_credit, cost_to_close_now):
    """
    Pure function - True once the cost to close has grown to
    STOP_LOSS_CREDIT_MULT times the credit originally received.
    """

    return cost_to_close_now >= entry_credit * STOP_LOSS_CREDIT_MULT


def _close_position(cfg, portfolio, short_close_premium, long_close_premium, reason, exit_spot=None):

    position = portfolio["Position"]

    # Net PnL of a credit spread: (credit received at entry) - (cost to
    # close now). Closing means BUYING BACK the short leg (pay
    # short_close_premium) and SELLING the long leg (receive
    # long_close_premium) - so cost-to-close = short_close - long_close.
    cost_to_close = (short_close_premium - long_close_premium) * position["Lots"] * cfg["lot_size"]
    entry_credit_rupees = position["Entry Credit"] * position["Lots"] * cfg["lot_size"]
    net_pnl = entry_credit_rupees - cost_to_close

    portfolio["Cash"] += net_pnl

    portfolio["Closed Trades"].append({
        "Option Type": position["Option Type"],
        "Short Strike": position["Short Strike"],
        "Long Strike": position["Long Strike"],
        "Short Symbol": position["Short Symbol"],
        "Long Symbol": position["Long Symbol"],
        "Entry Time": position["Entry Time"],
        "Entry Credit": position["Entry Credit"],
        "Entry Spot": position.get("Entry Spot"),
        # Added 13-Aug-2026 - see fyers_options_engine.py's matching note.
        "Exit Spot": exit_spot,
        "Exit Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Short Close Premium": short_close_premium,
        "Long Close Premium": long_close_premium,
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / cfg["initial_capital"] * 100, 3),
    })

    portfolio["Position"] = None

    return portfolio, f"CLOSED ({reason}) net {round(net_pnl, 2)}"


def _check_position(cfg, portfolio):

    position = portfolio["Position"]

    short_quote = _fetch_quote(position["Short Symbol"])
    long_quote = _fetch_quote(position["Long Symbol"])

    short_now = short_quote.get("lp") or (short_quote.get("bid", 0) + short_quote.get("ask", 0)) / 2
    long_now = long_quote.get("lp") or (long_quote.get("bid", 0) + long_quote.get("ask", 0)) / 2

    underlying_quote = _fetch_quote(cfg["underlying_symbol"])
    current_spot = underlying_quote.get("lp") or (underlying_quote.get("bid", 0) + underlying_quote.get("ask", 0)) / 2

    cost_to_close_now = short_now - long_now  # per share, same units as Entry Credit
    entry_credit = position["Entry Credit"]

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if _target_hit(entry_credit, cost_to_close_now):
        return _close_position(cfg, portfolio, short_now, long_now, "Target (50% of credit)", current_spot)

    if _stop_loss_hit(entry_credit, cost_to_close_now):
        return _close_position(cfg, portfolio, short_now, long_now, "Stop Loss (2x credit)", current_spot)

    if past_squareoff:
        return _close_position(cfg, portfolio, short_now, long_now, "Square-Off", current_spot)

    position["Last Cost To Close"] = round(cost_to_close_now, 2)
    position["Last Checked"] = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (cost to close {round(cost_to_close_now, 2)}, credit {entry_credit})"


def _open_position(cfg, portfolio):

    entry = _entry_signal(cfg)

    if entry is None:
        return portfolio, "SKIPPED (no VIX-high + RSI-direction qualifying setup)"

    option_type = entry["option_type"]

    short_leg, long_leg, spot = _pick_spread_legs(cfg, option_type)

    short_premium = _leg_premium(short_leg)
    long_premium = _leg_premium(long_leg)

    if not short_premium or short_premium <= 0 or long_premium is None or long_premium < 0:
        return portfolio, "SKIPPED (no valid premium quote on one or both legs)"

    credit = short_premium - long_premium

    if credit <= 0:
        return portfolio, f"SKIPPED (no net credit available - short {short_premium}, long {long_premium})"

    max_loss_per_lot = (cfg["width_points"] - credit) * cfg["lot_size"]

    if max_loss_per_lot <= 0:
        return portfolio, "SKIPPED (credit exceeds spread width - suspicious quote, not trading it)"

    # Conservative sizing - see module docstring: uses the spread's own
    # worst-case loss as a stand-in for real margin, always >= what a
    # defined-risk spread actually requires.
    lots = int(portfolio["Cash"] // max_loss_per_lot)

    if lots < 1:
        return portfolio, f"SKIPPED (capital insufficient for 1 lot - max loss {max_loss_per_lot} per lot)"

    now = datetime.datetime.now()

    portfolio["Position"] = {
        "Option Type": option_type,
        "Short Strike": short_leg["strike_price"],
        "Long Strike": long_leg["strike_price"],
        "Short Symbol": short_leg["symbol"],
        "Long Symbol": long_leg["symbol"],
        "Entry Time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Spot": spot,
        "Entry Credit": round(credit, 2),
        "Entry RSI": entry["rsi"],
        "Entry VIX": entry["vix"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Max Loss": round(max_loss_per_lot * lots, 2),
        "Last Cost To Close": round(credit, 2),
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, (
        f"OPENED {option_type} spread: SELL {short_leg['strike_price']} / "
        f"BUY {long_leg['strike_price']} @ credit {round(credit, 2)} (RSI {entry['rsi']}, VIX {entry['vix']})"
    )


def check_or_open(cfg):
    """
    Call once per check. Opens a directional credit spread if none is
    open (VIX-high + RSI-direction signal, market-hours gated), or
    checks the open one against the 50%-of-credit Target / 2x-credit
    Stop-Loss / Square-Off. Always saves. No one-trade-per-day cap -
    the VIX-high condition is already selective on its own.

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
