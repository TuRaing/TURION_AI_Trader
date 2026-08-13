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

# Added 09-Aug-2026 - "our own" indicator, co-designed with the user
# after RSI/RSI+ADX/RSI-Divergence all failed (see doc/PROJECT_STATUS.
# md's 09-Aug entries) - a deliberate move AWAY from price-pattern
# signals (crowded, arbitraged away) toward a mechanism-based one,
# same philosophy as oi_footprint.py: a real institutional position
# being built leaves a footprint in Open Interest, visible live via
# the option chain.
#
# THIS strategy widens that footprint from oi_footprint's single ATM
# strike to the WHOLE chain, and adds a volume-confirmation filter -
# the combo the user picked as the most complementary first pairing
# out of 4 candidate ideas discussed:
#   - Chain-Wide PCR Momentum: track the RATE OF CHANGE of Put-Call
#     Ratio (total Put OI / total Call OI, summed across the whole
#     collected chain, not just ATM) between checks - rising PCR ==
#     put-writing increasing faster than call-writing == put writers
#     confident a floor holds == bullish; falling PCR == the mirror,
#     bearish.
#   - Volume-Weighted confirmation: only trust a PCR move if it comes
#     with a meaningfully elevated total chain volume vs the last
#     check - filters out PCR drift from thin/stale quotes, keeps only
#     moves backed by real, fresh trading activity.
#
# NOT BACKTESTED (same limitation as oi_footprint.py and every other
# OI-based signal here): no historical option-chain OI/Volume archive
# exists anywhere (not NSE, not Fyers) to backtest against - the
# collected reports/options_premium_history.jsonl archive is still
# too sparse (see 08-Aug's finding) for a meaningful backtest. Built
# and unit-tested (pure logic fully covered) instead, same path
# oi_footprint took to going live.
#
# DEPLOYED 13-Aug-2026 - built 09-Aug and initially held back from
# ALL_STRATEGIES pending the 14-Aug review, but the user asked to go
# live now instead of waiting: this is paper trading (zero real-money
# risk) and its own separate book, so it doesn't contaminate any of
# the other 25 books' ongoing comparison - no reason to wait on the
# calendar when waiting costs nothing. Needs its own cron-job.org
# trigger (STRATEGY_NAME="pcr_momentum") to actually start firing.

MIN_PCR_CHANGE_PCT = 5.0    # minimum Put-Call OI ratio change (vs the
                              # last check) to treat as a real signal,
                              # not noise - same threshold convention
                              # as oi_footprint.py's MIN_OI_CHANGE_PCT
MIN_VOLUME_RATIO = 1.2       # current total chain volume must be at
                              # least this many times the last check's
                              # volume - confirms the PCR move has real,
                              # fresh activity behind it, not just a
                              # drift in thinly-traded quotes
TARGET_RUPEES = 1500         # small, quick - same "get in, get out"
                              # philosophy as oi_footprint.py
STOP_LOSS_RUPEES = 1500
SQUAREOFF_TIME = (15, 15)


def make_pcr_momentum_config(index, name="pcr_momentum"):

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
            "Last Chain Snapshot": None,
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


def _read_chain_snapshot(cfg):
    """
    Live snapshot of spot + chain-wide Put-Call OI ratio + total chain
    volume - the data this strategy's signal is built from. Returns
    None if the chain fetch fails or has no usable OI/Volume data.
    """

    chain = _fetch_option_chain(cfg)
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        return None

    total_put_oi = sum(leg.get("oi") or 0 for leg in legs if leg.get("option_type") == "PE")
    total_call_oi = sum(leg.get("oi") or 0 for leg in legs if leg.get("option_type") == "CE")
    total_volume = sum(leg.get("volume") or 0 for leg in legs if leg.get("option_type") in ("PE", "CE"))

    if total_call_oi == 0:
        return None

    pcr = total_put_oi / total_call_oi

    return {"spot": spot, "pcr": pcr, "total_volume": total_volume}


def _classify_pcr_momentum(previous, current):
    """
    Pure function - the PCR-momentum + volume-confirmation signal
    described in the module docstring.

    Returns "CE" (bullish), "PE" (bearish), or None (no previous
    snapshot, too little volume backing the move, or the PCR change
    was too small to trust).
    """

    if previous is None:
        return None

    if not previous.get("pcr") or not previous.get("total_volume"):
        return None

    pcr_change_pct = (current["pcr"] - previous["pcr"]) / previous["pcr"] * 100
    volume_ratio = current["total_volume"] / previous["total_volume"]

    if volume_ratio < MIN_VOLUME_RATIO:
        return None

    if pcr_change_pct >= MIN_PCR_CHANGE_PCT:
        return "CE"

    if pcr_change_pct <= -MIN_PCR_CHANGE_PCT:
        return "PE"

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
        "Entry PCR": position.get("Entry PCR"),
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

    current = _read_chain_snapshot(cfg)

    if current is None:
        return portfolio, "SKIPPED (could not read option chain OI/Volume)"

    previous = portfolio.get("Last Chain Snapshot")
    option_type = _classify_pcr_momentum(previous, current)

    # Always refresh the baseline for next check, whether or not this
    # one produced a trade - same reasoning as oi_footprint.py.
    portfolio["Last Chain Snapshot"] = current

    if option_type is None:
        return portfolio, f"SKIPPED (no meaningful PCR-momentum signal - spot {current['spot']}, PCR {round(current['pcr'], 3)})"

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
        "Entry PCR": round(current["pcr"], 4),
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (PCR-momentum + volume signal)"


def check_or_open(cfg):
    """
    Call once per check. Opens a position if none is open (PCR-
    momentum + volume signal, market-hours gated), or checks the open
    one against the fixed Rs 1,500 Target/Stop-Loss/Square-Off.
    Always saves.

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
