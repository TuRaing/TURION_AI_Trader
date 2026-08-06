import datetime
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token
from strategy.fyers_data import fyers_download
from strategy.options_transaction_costs import calculate_options_round_trip_cost
from indicators.rsi import calculate_rsi

# Added 06-Aug-2026 - generalized, parameterized core that multiple
# named options strategies run through (simple_st1, st2, st3, and
# later st4), each on both NIFTY and BANKNIFTY - 4 strategies x 2
# indices = 8 independent Rs 1,00,000 paper books, each with its own
# portfolio file, instead of 8 near-duplicate scripts. strategy/
# fyers_options_paper_trading.py (the original single live strategy)
# is left completely untouched - this is a new, separate engine, per
# this repo's "never modify a working module" rule.
#
# Every config shares the same RSI-momentum entry rule (CE if the
# underlying's RSI >= 50 else PE, ATM strike, one full-capital
# position at a time, real Fyers quotes) - only Target %, Stop-Loss
# %, and the index's own lot size/strike step differ. A strategy
# whose ENTRY LOGIC itself differs (st4 - multi-timeframe+ADX
# alignment, trailing stop after a rupee profit threshold) needs a
# materially different module and is not implemented here.

DATA_BASE_URL = "https://api-t1.fyers.in/data"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
MARKET_OPEN_TIME = (9, 15)  # NSE regular trading start - before this is
                             # only the pre-open auction session, where
                             # quotes are indicative/illiquid, not real
                             # tradeable continuous-market prices.

INDEX_CONFIG = {
    "NIFTY": {
        "underlying_symbol": "NSE:NIFTY50-INDEX",
        "index_symbol_for_rsi": "^NSEI",
        "lot_size": 75,
        "strike_step": 50,
    },
    "BANKNIFTY": {
        "underlying_symbol": "NSE:NIFTYBANK-INDEX",
        "index_symbol_for_rsi": "^NSEBANK",
        "lot_size": 30,
        "strike_step": 100,
    },
}


def make_strategy(name, index, target_net_pct, stop_loss_pct,
                   initial_capital=100000, squareoff_time=(15, 15)):
    """
    Build one named strategy's config for one index. `name` (e.g.
    "simple_st1") only affects the portfolio filename - reports/
    fyers_options_{name}_{index}_portfolio.json - keeping each of the
    4-strategies x 2-indices paper books fully independent.
    """

    index_cfg = INDEX_CONFIG[index]

    return {
        "name": name,
        "index": index,
        "portfolio_file": f"reports/fyers_options_{name}_{index.lower()}_portfolio.json",
        "underlying_symbol": index_cfg["underlying_symbol"],
        "index_symbol_for_rsi": index_cfg["index_symbol_for_rsi"],
        "lot_size": index_cfg["lot_size"],
        "strike_step": index_cfg["strike_step"],
        "target_net_pct": target_net_pct,
        "stop_loss_pct": stop_loss_pct,
        "initial_capital": initial_capital,
        "squareoff_time": squareoff_time,
    }


def _headers():
    return {"Authorization": f"{_app_id()}:{get_access_token()}"}


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


def _fetch_option_chain(cfg, strike_count=5):

    response = requests.get(
        f"{DATA_BASE_URL}/options-chain-v3",
        headers=_headers(),
        params={"symbol": cfg["underlying_symbol"], "strikecount": strike_count, "timestamp": ""},
        timeout=15,
    )

    data = response.json()

    if data.get("s") != "ok":
        raise RuntimeError(f"Fyers option chain fetch failed for {cfg['underlying_symbol']}: {data}")

    return data["data"]


def _fetch_quote(fyers_symbol):

    response = requests.get(
        f"{DATA_BASE_URL}/quotes",
        headers=_headers(),
        params={"symbols": fyers_symbol},
        timeout=15,
    )

    data = response.json()

    if data.get("s") != "ok" or not data.get("d"):
        raise RuntimeError(f"Fyers quote fetch failed for {fyers_symbol}: {data}")

    return data["d"][0]["v"]


def _get_direction(cfg):

    frame = fyers_download(cfg["index_symbol_for_rsi"], period="60d", interval="5m")

    if frame is None or frame.empty:
        raise RuntimeError(f"No underlying data available for {cfg['index_symbol_for_rsi']}")

    rsi = calculate_rsi(frame)
    latest_rsi = float(rsi.iloc[-1])

    return ("CE" if latest_rsi >= 50 else "PE"), latest_rsi


def _pick_atm_leg(cfg, option_type):

    chain = _fetch_option_chain(cfg)
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        raise RuntimeError("Could not read spot price from option chain response")

    atm_strike = round(spot / cfg["strike_step"]) * cfg["strike_step"]

    for leg in legs:

        if leg.get("strike_price") == atm_strike and leg.get("option_type") == option_type:
            return leg, spot

    raise RuntimeError(f"ATM strike {atm_strike} {option_type} not found in option chain response")


def _net_pnl(cfg, entry_premium, current_premium, lots):

    quantity = lots * cfg["lot_size"]
    gross_pnl = (current_premium - entry_premium) * quantity
    cost = calculate_options_round_trip_cost(entry_premium, current_premium, cfg["lot_size"], lots)

    return gross_pnl - cost


def _open_position(cfg, portfolio):

    option_type, rsi_value = _get_direction(cfg)
    leg, spot = _pick_atm_leg(cfg, option_type)

    entry_premium = leg.get("ltp") or (leg.get("bid", 0) + leg.get("ask", 0)) / 2

    if not entry_premium or entry_premium <= 0:
        return portfolio, "SKIPPED (no valid premium quote)"

    lots = int(portfolio["Cash"] // (entry_premium * cfg["lot_size"]))

    if lots < 1:
        return portfolio, f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})"

    portfolio["Position"] = {
        "Symbol": leg["symbol"],
        "Strike": leg["strike_price"],
        "Option Type": option_type,
        # Stored as naive/local time (UTC on the GitHub Actions runner),
        # matching every other engine's convention - see the same-day
        # fix note in fyers_options_paper_trading.py. IST is only used
        # for gating decisions, never for what gets persisted.
        "Entry Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Spot": spot,
        "Entry Premium": entry_premium,
        "Entry RSI": round(rsi_value, 2),
        "Lots": lots,
        "Quantity": lots * cfg["lot_size"],
        "Capital Deployed": round(entry_premium * lots * cfg["lot_size"], 2),
        "Last Premium": entry_premium,
        "Last Checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium}"


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
    net_pnl_pct = net_pnl / cfg["initial_capital"] * 100

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= cfg["squareoff_time"]

    if net_pnl_pct >= cfg["target_net_pct"]:
        return _close_position(cfg, portfolio, current_premium, "Target")

    if net_pnl_pct <= -cfg["stop_loss_pct"]:
        return _close_position(cfg, portfolio, current_premium, "Stop Loss")

    if past_squareoff:
        return _close_position(cfg, portfolio, current_premium, "Square-Off")

    position["Last Premium"] = current_premium
    position["Last Checked"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (net {round(net_pnl, 2)} / {round(net_pnl_pct, 3)}%)"


def check_or_open(cfg):
    """
    Call once per check for a given strategy config. Opens today's
    position if none is open (RSI-direction ATM CE/PE, skipped before
    MARKET_OPEN_TIME), or checks the open one against Target/Stop-
    Loss/Square-Off using a fresh real quote. Always saves.

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
        elif now_hm >= cfg["squareoff_time"]:
            action = "SKIPPED (past square-off time, market closed or about to close)"
        else:
            portfolio, action = _open_position(cfg, portfolio)

    save_portfolio(cfg, portfolio)

    return portfolio, action
