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
from strategy.fyers_data import fyers_download
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr

# Added 08-Aug-2026 - ports the ONE validated-but-unused finding from
# this project's own 22-Jul research (strategy/momentum_vix_backtest.py):
# Momentum(RSI) + India VIX percentile-band filter was found consistently
# profitable on BANKNIFTY's directional accuracy (38/42 parameter combos
# positive, 90%) - the best combo (VIX 30-70 percentile band, RSI>60/
# RSI<40, 1.5x SL/4.0x Target ATR on the underlying) gave +3,775.53
# underlying points over 60d. NIFTY was REJECTED under the same filter
# (only 9/42 combos positive) - so this strategy is BANKNIFTY ONLY,
# unlike every other options strategy here which runs both indices.
#
# That 22-Jul finding measured DIRECTIONAL ACCURACY on the underlying
# only (no real premium cost model existed then, per its own caveat).
# This wires the exact same validated rule into real Fyers premiums for
# the first time, same as every other strategy here already does for
# its own signal - SL/Target are tracked on the underlying's spot (ATR-
# based), same reasoning as st4/gapfill: no reliable per-contract
# premium candle history exists to compute levels in premium terms
# directly.
#
# Deliberately built as a NEW, separate strategy/portfolio rather than
# modifying simple_st1/st2/st3's existing BANKNIFTY books - those 3
# already have real trade history accumulating toward the already-
# agreed 1-week review; changing their live signal mid-week would
# contaminate that comparison. Per this repo's own DEVELOPMENT RULES:
# never modify a working module, add new functionality as a separate
# engine.

RSI_BULLISH = 60
RSI_BEARISH = 40
VIX_SYMBOL = "^INDIAVIX"
VIX_PERCENTILE_LOW = 0.30
VIX_PERCENTILE_HIGH = 0.70
VIX_LOOKBACK_CANDLES = 125  # ~5 trading days of 15m candles, matching
                             # the validated backtest's window
SIGNAL_INTERVAL = "15m"
ATR_SL_MULT = 1.5
ATR_TARGET_MULT = 4.0
SQUAREOFF_TIME = (15, 15)


def make_vix_filter_config(name="vix_filter"):
    """
    BANKNIFTY only - see module docstring. No `index` parameter, unlike
    every other make_*_config() here, since a NIFTY variant of this
    exact combo was already tested and rejected.
    """

    index_cfg = INDEX_CONFIG["BANKNIFTY"]

    return {
        "name": name,
        "index": "BANKNIFTY",
        "portfolio_file": f"reports/fyers_options_{name}_banknifty_portfolio.json",
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
    RSI>60 -> CE, RSI<40 -> PE, only when India VIX sits inside its own
    trailing [30th,70th] percentile band (not the deadest or the most
    panicked conditions) - the exact validated 22-Jul combo.
    """

    price_data = fyers_download(cfg["index_symbol_for_rsi"], period="10d", interval=SIGNAL_INTERVAL)
    vix_data = fyers_download(VIX_SYMBOL, period="10d", interval=SIGNAL_INTERVAL)

    if price_data is None or price_data.empty or vix_data is None or vix_data.empty:
        return None

    if len(vix_data) < VIX_LOOKBACK_CANDLES:
        return None

    rsi = calculate_rsi(price_data)
    atr = calculate_atr(price_data)

    if rsi.empty or atr.empty:
        return None

    latest_rsi = float(rsi.iloc[-1])
    latest_atr = float(atr.iloc[-1])

    if latest_rsi != latest_rsi or latest_atr != latest_atr:  # NaN check
        return None

    recent_vix = vix_data["Close"].iloc[-VIX_LOOKBACK_CANDLES:]
    vix_low_band = float(recent_vix.quantile(VIX_PERCENTILE_LOW))
    vix_high_band = float(recent_vix.quantile(VIX_PERCENTILE_HIGH))
    latest_vix = float(vix_data["Close"].iloc[-1])

    if not (vix_low_band <= latest_vix <= vix_high_band):
        return None

    if latest_rsi > RSI_BULLISH:
        option_type = "CE"
    elif latest_rsi < RSI_BEARISH:
        option_type = "PE"
    else:
        return None

    spot = float(price_data["Close"].iloc[-1])

    if option_type == "CE":
        stop_loss_spot = spot - latest_atr * ATR_SL_MULT
        target_spot = spot + latest_atr * ATR_TARGET_MULT
    else:
        stop_loss_spot = spot + latest_atr * ATR_SL_MULT
        target_spot = spot - latest_atr * ATR_TARGET_MULT

    return {
        "option_type": option_type,
        "rsi": round(latest_rsi, 2),
        "vix": round(latest_vix, 2),
        "target_spot": target_spot,
        "stop_loss_spot": stop_loss_spot,
    }


def _target_hit(option_type, current_spot, target_spot):

    if option_type == "CE":
        return current_spot >= target_spot

    return current_spot <= target_spot


def _stop_loss_hit(option_type, current_spot, stop_loss_spot):

    if option_type == "CE":
        return current_spot <= stop_loss_spot

    return current_spot >= stop_loss_spot


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
        "Entry RSI": position.get("Entry RSI"),
        "Entry VIX": position.get("Entry VIX"),
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
        return portfolio, "SKIPPED (no RSI+VIX-band qualifying setup)"

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
        "Entry RSI": entry["rsi"],
        "Entry VIX": entry["vix"],
        "Target Spot": entry["target_spot"],
        "Stop Loss Spot": entry["stop_loss_spot"],
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Spot": spot,
        "Last Checked": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium} (RSI {entry['rsi']}, VIX {entry['vix']})"


def check_or_open(cfg):
    """
    Call once per check. Opens a new position if none is open (RSI+VIX-
    band signal, market-hours gated), or checks the open one against
    the spot-based Target/Stop-Loss/Square-Off. Always saves. Unlike
    st4/gapfill, this has NO one-trade-per-day cap - the validated
    backtest didn't use one either, and the RSI+VIX-band filter is
    already selective (both conditions must align).

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
