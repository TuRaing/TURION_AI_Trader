import datetime
import json
import math
import os

from strategy.fyers_options_engine import (
    IST,
    MARKET_OPEN_TIME,
    INDEX_CONFIG,
    _fetch_quote,
    _pick_atm_leg,
    _net_pnl,
)
from strategy.fyers_options_oi_footprint import _read_atm_oi_snapshot, _classify_buildup
from strategy.fyers_data import fyers_download, parse_option_expiry, time_to_expiry_years
from indicators.black_scholes import implied_volatility

# Added 13-Aug-2026 - a retrospective backtest (see PROJECT_STATUS.md's
# "IV vs REALIZED VOLATILITY RETROSPECTIVELY TESTED" entry) found that
# skipping oi_footprint trades where the option's own implied
# volatility looked "expensive" relative to the underlying's actual
# recent realized volatility would have removed almost none of oi_
# footprint/NIFTY's real profit (Rs 730 of Rs 54,982) while cutting
# its weakest trades (40% win rate vs 63.6% for the rest) - close to a
# free lunch. That same filter, tested on the RSI-threshold family,
# ran BACKWARDS (removed their best trades instead) - so this is NOT
# folded into oi_footprint itself, but built as its own separate book,
# same "never modify a working module, add a new engine" rule this
# project has followed throughout.
#
# DESIGN: reuses oi_footprint.py's OI-buildup read/classify logic
# UNCHANGED (imported, not duplicated), and adds ONE more condition
# before opening: the candidate leg's own implied_volatility() (solved
# from its live premium) must not exceed MAX_IV_RV_RATIO times the
# underlying's own trailing realized volatility (computed live from
# real daily closes, same method as the retrospective backtest).
#
# NOT BACKTESTED IN THE FORWARD-TESTING SENSE (same permanent
# limitation as every OI-based signal here) - the retrospective check
# above used ALREADY-CLOSED oi_footprint trades' own stored data, not
# a true historical option-chain backtest. DEPLOYED same day as built,
# on the user's own "no benefit to waiting, paper trading is risk-
# free" reasoning already applied to pcr_momentum/max_pain_drift/
# pcr_vix_combo.

MAX_IV_RV_RATIO = 1.5        # the threshold the retrospective backtest
                              # found near-free for oi_footprint/NIFTY
REALIZED_VOL_LOOKBACK_DAYS = 10
TARGET_RUPEES = 1500         # same small, quick "get in, get out"
                              # philosophy as oi_footprint.py
STOP_LOSS_RUPEES = 1500
SQUAREOFF_TIME = (15, 15)


def make_oi_iv_combo_config(index, name="oi_iv_combo"):

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
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


def _realized_volatility(cfg, lookback_days=REALIZED_VOL_LOOKBACK_DAYS):
    """
    Trailing annualized realized volatility (%) of the underlying,
    from real daily closes - log returns' std dev x sqrt(252). The
    live counterpart of the retrospective backtest's realized-vol
    calculation. Returns None if there isn't enough daily history.
    """

    price_data = fyers_download(cfg["index_symbol_for_rsi"], period="30d", interval="1d")

    if price_data is None or price_data.empty or len(price_data) < lookback_days + 1:
        return None

    closes = price_data["Close"].iloc[-(lookback_days + 1):].tolist()
    log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]

    mean = sum(log_returns) / len(log_returns)
    var = sum((x - mean) ** 2 for x in log_returns) / (len(log_returns) - 1)
    std = math.sqrt(var)

    return std * math.sqrt(252) * 100


def _option_looks_cheap_enough(cfg, leg, spot, premium):
    """
    True if the candidate leg's own implied volatility (solved from
    its live premium) is within MAX_IV_RV_RATIO of the underlying's
    trailing realized volatility - i.e. not "expensive". False (skip
    the trade) if IV can't be solved, expiry can't be parsed, or the
    ratio is too high - fails closed, never guesses.
    """

    symbol = leg.get("symbol")
    expiry = parse_option_expiry(symbol) if symbol else None

    if expiry is None:
        return False

    entry_dt = datetime.datetime.now()
    t_years = time_to_expiry_years(entry_dt, expiry)

    if t_years <= 0:
        return False

    iv = implied_volatility(premium, spot, leg["strike_price"], t_years, leg["option_type"])

    if iv is None:
        return False

    rv_pct = _realized_volatility(cfg)

    if rv_pct is None or rv_pct <= 0:
        return False

    return (iv * 100) / rv_pct <= MAX_IV_RV_RATIO


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

    if not _option_looks_cheap_enough(cfg, leg, spot, entry_premium):
        return portfolio, (
            f"SKIPPED (OI-buildup signal present but option looks expensive vs realized vol - "
            f"spot {current['spot']}, strike {current['strike']})"
        )

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

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (OI buildup + cheap-IV signal)"


def check_or_open(cfg):
    """
    Call once per check. Opens a position if none is open (OI-buildup
    signal AND the option not looking "expensive" vs realized vol,
    market-hours gated), or checks the open one against the fixed
    Rs 1,500 Target/Stop-Loss/Square-Off. Always saves.

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
