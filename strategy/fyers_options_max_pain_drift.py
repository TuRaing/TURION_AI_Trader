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
from strategy.fyers_data import parse_option_expiry

# Added 13-Aug-2026 - the 4th and last of the novel-indicator ideas
# discussed 09-Aug alongside PCR Momentum + Volume-Weighted OI (see
# fyers_options_pcr_momentum.py's module docstring for the full
# background) - deliberately kept SEPARATE from that combo rather than
# folded in, per the user's own explicit sequencing at the time.
#
# MAX PAIN: the strike at which option WRITERS (mostly institutions)
# owe the least aggregate payout at expiry - i.e. where the maximum
# combined CE+PE open interest would expire worthless. The (debated,
# not universally accepted) theory is that as expiry nears, large
# option sellers' own hedging activity tends to "pin" the underlying
# toward this strike.
#
# THIS strategy does NOT trade toward the current Max Pain level
# (a static read, less defensible) - it tracks how the Max Pain
# strike itself DRIFTS between checks, same "watch the change, not the
# snapshot" philosophy that already worked for oi_footprint (OI
# buildup direction) and pcr_momentum (PCR rate of change): Max Pain
# drifting UP -> more call-writing pressure -> bullish (CE); drifting
# DOWN -> bearish (PE).
#
# EXPIRY-PROXIMITY GATE (the user's own refinement, 13-Aug): the "pull
# toward Max Pain" effect, if real at all, is strongest as expiry
# nears (settlement is imminent, sellers' hedging is most urgent) and
# weakest far from expiry. Rather than trust the drift signal every
# day, this only acts within MAX_DAYS_TO_EXPIRY of the option's own
# expiry - using the expiry parser + time-to-expiry helper built the
# same day (strategy/fyers_data.py's parse_option_expiry()/
# time_to_expiry_years()) specifically to make this possible.
#
# NOT BACKTESTED (same permanent limitation as every OI-based signal
# here - no historical option-chain OI dataset exists anywhere) -
# built and unit-tested as pure logic only, same path oi_footprint and
# pcr_momentum took.
#
# DEPLOYED 13-Aug-2026 - built the same day, and immediately deployed
# on the user's direct request (same reasoning as pcr_momentum.py's
# matching note: paper trading, zero real-money risk, its own separate
# book, no reason to wait on the calendar). Needs its own cron-job.org
# trigger (STRATEGY_NAME="max_pain_drift") to actually start firing.

CHAIN_STRIKE_COUNT = 15      # wide enough to see meaningful OI across
                              # the visible chain for a reasonable Max
                              # Pain estimate - unlike credit_spread's
                              # exact-far-strike problem, Max Pain just
                              # needs broad coverage, not one precise
                              # distant strike, so a fixed generous
                              # count (no dynamic re-fetch) is enough
MIN_DRIFT_STRIKES = 1        # Max Pain must have moved at least this
                              # many strike-steps since the last check
                              # to count as a real drift, not noise
MAX_DAYS_TO_EXPIRY = 2       # only trust the drift signal within this
                              # many days of the option's own expiry -
                              # the user's own explicit refinement
TARGET_RUPEES = 1500         # same small, quick "get in, get out"
                              # philosophy as oi_footprint.py
STOP_LOSS_RUPEES = 1500
SQUAREOFF_TIME = (15, 15)


def make_max_pain_drift_config(index, name="max_pain_drift"):

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
            "Last Max Pain": None,
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


def _compute_max_pain(legs, strike_step):
    """
    Pure function - the classic Max Pain calculation: for each
    candidate settlement strike, sum what option WRITERS would owe
    across every other strike's CE+PE open interest if the underlying
    settled there, then return the strike that minimizes that payout.

    legs : list of option-chain leg dicts (strike_price, option_type,
           oi) - the spot leg (strike_price == -1) is ignored.

    Returns
    -------
    float (the Max Pain strike), or None if there's no usable OI data.
    """

    oi_map = {}
    strikes = set()

    for leg in legs:

        strike = leg.get("strike_price")

        if strike is None or strike == -1:
            continue

        strikes.add(strike)
        oi_map[(strike, leg.get("option_type"))] = leg.get("oi") or 0

    if not strikes:
        return None

    best_strike, best_payout = None, None

    for candidate in strikes:

        payout = 0.0

        for strike in strikes:

            if candidate > strike:
                payout += (candidate - strike) * oi_map.get((strike, "CE"), 0)

            if candidate < strike:
                payout += (strike - candidate) * oi_map.get((strike, "PE"), 0)

        if best_payout is None or payout < best_payout:
            best_payout, best_strike = payout, candidate

    return best_strike


def _classify_max_pain_drift(previous_max_pain, current_max_pain, strike_step,
                              min_drift_strikes=MIN_DRIFT_STRIKES):
    """
    Pure function - "CE" if Max Pain drifted up enough strikes since
    the last check, "PE" if down, None if no previous snapshot or the
    drift is too small to trust (noise filter, same spirit as oi_
    footprint's MIN_OI_CHANGE_PCT).
    """

    if previous_max_pain is None or current_max_pain is None:
        return None

    drift = current_max_pain - previous_max_pain

    if abs(drift) < min_drift_strikes * strike_step:
        return None

    return "CE" if drift > 0 else "PE"


def _within_expiry_window(expiry_date, now, max_days=MAX_DAYS_TO_EXPIRY):
    """
    Pure function - True only if expiry_date is today or within the
    next max_days calendar days (never past expiry, never further out
    than the window). None expiry_date (unparseable symbol) -> False,
    fail closed rather than trade on an unverified assumption.
    """

    if expiry_date is None:
        return False

    days_left = (expiry_date - now.date()).days

    return 0 <= days_left <= max_days


def _read_chain_snapshot(cfg):
    """
    Live snapshot of spot + Max Pain strike + the expiry date parsed
    off any real leg's own symbol. Returns None if the chain fetch
    fails, has no usable spot, or no leg's symbol parses to a real
    expiry (fail closed - never guess).
    """

    chain = _fetch_option_chain(cfg, strike_count=CHAIN_STRIKE_COUNT)
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        return None

    max_pain = _compute_max_pain(legs, cfg["strike_step"])

    if max_pain is None:
        return None

    expiry_date = None

    for leg in legs:

        symbol = leg.get("symbol")

        if not symbol:
            continue

        expiry_date = parse_option_expiry(symbol)

        if expiry_date is not None:
            break

    if expiry_date is None:
        return None

    return {"spot": spot, "max_pain": max_pain, "expiry_date": expiry_date}


def _close_position(cfg, portfolio, exit_premium, reason):

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
        "Entry Max Pain": position.get("Entry Max Pain"),
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

    net_pnl = _net_pnl(cfg, position["Entry Premium"], current_premium, position["Lots"])

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if net_pnl >= TARGET_RUPEES:
        return _close_position(cfg, portfolio, current_premium, "Target")

    if net_pnl <= -STOP_LOSS_RUPEES:
        return _close_position(cfg, portfolio, current_premium, "Stop Loss")

    if past_squareoff:
        return _close_position(cfg, portfolio, current_premium, "Square-Off")

    position["Last Premium"] = current_premium
    position["Last Checked"] = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (net {round(net_pnl, 2)})"


def _open_position(cfg, portfolio):

    current = _read_chain_snapshot(cfg)

    if current is None:
        return portfolio, "SKIPPED (could not read option chain / Max Pain / expiry)"

    now_ist = datetime.datetime.now(IST)

    if not _within_expiry_window(current["expiry_date"], now_ist):
        # Still refresh the baseline outside the window, so the FIRST
        # check once we do enter the window has a real previous
        # snapshot to compare against, not a stale/missing one.
        portfolio["Last Max Pain"] = current["max_pain"]
        return portfolio, (
            f"SKIPPED (outside expiry window - expiry {current['expiry_date']}, "
            f"today {now_ist.date()})"
        )

    previous_max_pain = portfolio.get("Last Max Pain")
    option_type = _classify_max_pain_drift(previous_max_pain, current["max_pain"], cfg["strike_step"])

    portfolio["Last Max Pain"] = current["max_pain"]

    if option_type is None:
        return portfolio, f"SKIPPED (no meaningful Max Pain drift - spot {current['spot']}, Max Pain {current['max_pain']})"

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
        "Entry Max Pain": current["max_pain"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (Max Pain drift to {current['max_pain']})"


def check_or_open(cfg):
    """
    Call once per check. Opens a position if none is open (Max Pain
    drift signal, gated to near-expiry days only, market-hours gated),
    or checks the open one against the fixed Rs 1,500 Target/Stop-
    Loss/Square-Off. Always saves.

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
