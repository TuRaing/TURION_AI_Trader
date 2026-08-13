import datetime
import json
import os

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
)
from strategy.fyers_options_pcr_momentum import _read_chain_snapshot, _classify_pcr_momentum
from strategy.fyers_data import fyers_download

# Added 13-Aug-2026 - the 4th of the 09-Aug novel-indicator ideas
# (see fyers_options_pcr_momentum.py's module docstring for the shared
# background), built now on the user's own reasoning: paper trading
# carries zero real-money risk, and there's no benefit to waiting for
# pcr_momentum's own review before also collecting real data on this
# combo in parallel - worst case it's another negative result (a real,
# useful finding on its own, same as every rejected signal this
# project has tested), best case it's positive and time was saved by
# not sequencing.
#
# DESIGN: reuses pcr_momentum.py's chain-reading and PCR-momentum-
# drift classification UNCHANGED (imported, not duplicated - per this
# repo's own DEVELOPMENT RULES) and adds ONE more condition on top:
# only trust the PCR-momentum signal when India VIX sits inside its
# own trailing [30th,70th] percentile band (not the deadest or most
# panicked conditions) - the exact same VIX-band reasoning already
# validated for RSI-momentum in fyers_options_vix_filter.py, applied
# here to an OI-based signal instead. The idea: a real institutional
# positioning shift (what PCR momentum tries to detect) is more
# trustworthy as a signal when the broader market isn't already in an
# extreme, unstable volatility regime.
#
# NOT BACKTESTED (same permanent limitation as every OI-based signal
# here) - built and unit-tested as pure logic only. DEPLOYED same day
# as built (not held back) - same reasoning as pcr_momentum.py and
# max_pain_drift.py's own 13-Aug deployment notes.

VIX_SYMBOL = "^INDIAVIX"
VIX_PERCENTILE_LOW = 0.30
VIX_PERCENTILE_HIGH = 0.70
VIX_LOOKBACK_CANDLES = 125   # ~5 trading days of 15m candles, matching
                              # vix_filter.py's own validated window
SIGNAL_INTERVAL = "15m"
TARGET_RUPEES = 1500         # same small, quick "get in, get out"
                              # philosophy as oi_footprint.py/pcr_
                              # momentum.py
STOP_LOSS_RUPEES = 1500
SQUAREOFF_TIME = (15, 15)


def make_pcr_vix_combo_config(index, name="pcr_vix_combo"):

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


def _vix_in_calm_band():
    """
    True if India VIX's latest close sits inside its own trailing
    [30th,70th] percentile band over the last VIX_LOOKBACK_CANDLES 15m
    candles - the same validated condition fyers_options_vix_filter.py
    uses, reimplemented here (not imported) since vix_filter.py's own
    version is entangled with its RSI/ATR logic, not a standalone
    reusable helper.

    Returns
    -------
    bool
    """

    vix_data = fyers_download(VIX_SYMBOL, period="10d", interval=SIGNAL_INTERVAL)

    if vix_data is None or vix_data.empty or len(vix_data) < VIX_LOOKBACK_CANDLES:
        return False

    recent_vix = vix_data["Close"].iloc[-VIX_LOOKBACK_CANDLES:]
    low_band = float(recent_vix.quantile(VIX_PERCENTILE_LOW))
    high_band = float(recent_vix.quantile(VIX_PERCENTILE_HIGH))
    latest_vix = float(vix_data["Close"].iloc[-1])

    if latest_vix != latest_vix:  # NaN check
        return False

    return low_band <= latest_vix <= high_band


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
        return portfolio, "SKIPPED (could not read option chain OI/Volume)"

    previous = portfolio.get("Last Chain Snapshot")
    option_type = _classify_pcr_momentum(previous, current)

    # Always refresh the baseline for next check, whether or not this
    # one produced a trade - same reasoning as pcr_momentum.py.
    portfolio["Last Chain Snapshot"] = current

    if option_type is None:
        return portfolio, f"SKIPPED (no meaningful PCR-momentum signal - spot {current['spot']}, PCR {round(current['pcr'], 3)})"

    if not _vix_in_calm_band():
        return portfolio, f"SKIPPED (PCR-momentum signal present but VIX outside calm band - spot {current['spot']}, PCR {round(current['pcr'], 3)})"

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

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (PCR-momentum + VIX-calm-band signal)"


def check_or_open(cfg):
    """
    Call once per check. Opens a position if none is open (PCR-
    momentum + VIX-calm-band signal, market-hours gated), or checks
    the open one against the fixed Rs 1,500 Target/Stop-Loss/Square-
    Off. Always saves.

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
