import datetime
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token
from strategy.fyers_data import fyers_download
from strategy.options_transaction_costs import calculate_options_round_trip_cost
from indicators.rsi import calculate_rsi

# Added 04-Aug-2026 - options paper trading using REAL Fyers premium
# data (bid/ask/LTP from live quotes), not the Black-Scholes ESTIMATE
# strategy/nifty_options_backtest.py used (03-Aug research - no real
# historical option data exists, so that file could only ever estimate).
# This is the live, forward-only counterpart: every entry/exit price
# recorded here is a real quoted price at the moment it was checked.
#
# Rules (same money-management idea researched 03-Aug, now run for
# real): deploy available capital into ONE ATM option/day, direction
# from RSI momentum (>=50 -> CE, else PE - always has a side, so a
# trade is never skipped for lack of signal strength), exit at a fixed
# NET % profit target or NET % Stop-Loss (both on capital, after real
# strategy/options_transaction_costs.py costs), or forced square-off
# before market close. One position at a time, MANUAL run (call
# check_or_open() once per check - no continuous loop, no automation
# wired up yet, matching strategy/fyers_options_collector.py's
# manual-first approach).
#
# Options logic kept fully separate from equity/index paper trading,
# per this repo's rule - own file, own portfolio, touches nothing else.

DATA_BASE_URL = "https://api-t1.fyers.in/data"
PORTFOLIO_FILE = "reports/fyers_options_portfolio.json"

INITIAL_CAPITAL = 100000
LOT_SIZE = 75          # NIFTY
STRIKE_STEP = 50       # NIFTY
UNDERLYING_SYMBOL = "NSE:NIFTY50-INDEX"
INDEX_SYMBOL_FOR_RSI = "^NSEI"  # yfinance-style symbol strategy/fyers_data.py expects

TARGET_NET_PCT = 2.0
STOP_LOSS_PCT = 5.0
SQUAREOFF_TIME = (15, 15)
MARKET_OPEN_TIME = (9, 15)  # NSE regular trading start - before this is
                             # only the pre-open auction session, where
                             # quotes are indicative/illiquid, not real
                             # tradeable continuous-market prices.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _headers():
    return {"Authorization": f"{_app_id()}:{get_access_token()}"}


def load_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):

        return {
            "Cash": INITIAL_CAPITAL,
            "Position": None,
            "Closed Trades": [],
            "Data Source": "Fyers (real premium)",
        }

    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio(portfolio):

    os.makedirs("reports", exist_ok=True)

    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def _fetch_option_chain(symbol=UNDERLYING_SYMBOL, strike_count=5):

    response = requests.get(
        f"{DATA_BASE_URL}/options-chain-v3",
        headers=_headers(),
        params={"symbol": symbol, "strikecount": strike_count, "timestamp": ""},
        timeout=15,
    )

    data = response.json()

    if data.get("s") != "ok":
        raise RuntimeError(f"Fyers option chain fetch failed: {data}")

    return data["data"]


def _fetch_quote(fyers_symbol):
    """
    Real, current bid/ask/LTP for one exact option contract - used to
    track an already-open position's own strike precisely (the option
    chain's ATM window can drift past it if spot has moved since entry).
    """

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


def _get_direction():
    """
    RSI momentum bias on the underlying's 5m candles - >=50 -> CE,
    else PE. Always has a side (see strategy/nifty_options_backtest.py's
    same rule, researched 03-Aug) so a trade is never skipped for lack
    of a strong-enough signal.
    """

    frame = fyers_download(INDEX_SYMBOL_FOR_RSI, period="60d", interval="5m")

    if frame is None or frame.empty:
        raise RuntimeError("No underlying data available to compute RSI direction")

    rsi = calculate_rsi(frame)
    latest_rsi = float(rsi.iloc[-1])

    return "CE" if latest_rsi >= 50 else "PE", latest_rsi


def _pick_atm_leg(option_type):
    """
    Real spot + nearest-expiry ATM strike's live premium, from the
    option chain (same source strategy/fyers_options_collector.py
    snapshots).
    """

    chain = _fetch_option_chain()
    legs = chain.get("optionsChain", [])

    spot = next((leg["ltp"] for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        raise RuntimeError("Could not read spot price from option chain response")

    atm_strike = round(spot / STRIKE_STEP) * STRIKE_STEP

    for leg in legs:

        if leg.get("strike_price") == atm_strike and leg.get("option_type") == option_type:
            return leg, spot

    raise RuntimeError(f"ATM strike {atm_strike} {option_type} not found in option chain response")


def _net_pnl(entry_premium, current_premium, lots):

    quantity = lots * LOT_SIZE
    gross_pnl = (current_premium - entry_premium) * quantity
    cost = calculate_options_round_trip_cost(entry_premium, current_premium, LOT_SIZE, lots)

    return gross_pnl - cost


def _open_position(portfolio):

    option_type, rsi_value = _get_direction()
    leg, spot = _pick_atm_leg(option_type)

    entry_premium = leg.get("ltp") or (leg.get("bid", 0) + leg.get("ask", 0)) / 2

    if not entry_premium or entry_premium <= 0:
        return portfolio, "SKIPPED (no valid premium quote)"

    lots = int(portfolio["Cash"] // (entry_premium * LOT_SIZE))

    if lots < 1:
        return portfolio, f"SKIPPED (capital insufficient for 1 lot at premium {entry_premium})"

    portfolio["Position"] = {
        "Symbol": leg["symbol"],
        "Strike": leg["strike_price"],
        "Option Type": option_type,
        "Entry Time": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "Entry Spot": spot,
        "Entry Premium": entry_premium,
        "Entry RSI": round(rsi_value, 2),
        "Lots": lots,
        "Quantity": lots * LOT_SIZE,
        "Capital Deployed": round(entry_premium * lots * LOT_SIZE, 2),
        "Last Premium": entry_premium,
        "Last Checked": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
    }

    return portfolio, f"OPENED {option_type} {leg['strike_price']} @ {entry_premium}"


def _close_position(portfolio, exit_premium, reason):

    position = portfolio["Position"]
    net_pnl = _net_pnl(position["Entry Premium"], exit_premium, position["Lots"])

    portfolio["Cash"] += net_pnl

    portfolio["Closed Trades"].append({
        "Symbol": position["Symbol"],
        "Strike": position["Strike"],
        "Option Type": position["Option Type"],
        "Entry Time": position["Entry Time"],
        "Entry Premium": position["Entry Premium"],
        "Exit Time": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "Exit Premium": exit_premium,
        "Lots": position["Lots"],
        "Exit Reason": reason,
        "Net PnL": round(net_pnl, 2),
        "Net PnL %": round(net_pnl / INITIAL_CAPITAL * 100, 3),
    })

    portfolio["Position"] = None

    return portfolio, f"CLOSED ({reason}) net {round(net_pnl, 2)}"


def _check_position(portfolio):

    position = portfolio["Position"]
    quote = _fetch_quote(position["Symbol"])
    current_premium = quote.get("lp") or (quote.get("bid", 0) + quote.get("ask", 0)) / 2

    net_pnl = _net_pnl(position["Entry Premium"], current_premium, position["Lots"])
    net_pnl_pct = net_pnl / INITIAL_CAPITAL * 100

    now_ist = datetime.datetime.now(IST)
    past_squareoff = (now_ist.hour, now_ist.minute) >= SQUAREOFF_TIME

    if net_pnl_pct >= TARGET_NET_PCT:
        return _close_position(portfolio, current_premium, "Target")

    if net_pnl_pct <= -STOP_LOSS_PCT:
        return _close_position(portfolio, current_premium, "Stop Loss")

    if past_squareoff:
        return _close_position(portfolio, current_premium, "Square-Off")

    position["Last Premium"] = current_premium
    position["Last Checked"] = now_ist.strftime("%Y-%m-%d %H:%M:%S")

    return portfolio, f"HOLD (net {round(net_pnl, 2)} / {round(net_pnl_pct, 3)}%)"


def check_or_open():
    """
    Call once per manual check. Opens today's position if none is open
    (RSI-direction ATM CE/PE), or checks the open one against Target/
    Stop-Loss/Square-Off using a fresh real quote. Always saves.

    Returns
    -------
    portfolio : dict
    action : str
    """

    portfolio = load_portfolio()

    if portfolio["Position"] is not None:
        portfolio, action = _check_position(portfolio)
    else:
        now_ist = datetime.datetime.now(IST)
        if (now_ist.hour, now_ist.minute) < MARKET_OPEN_TIME:
            action = "SKIPPED (before market open, pre-open session quotes not tradeable)"
        else:
            portfolio, action = _open_position(portfolio)

    save_portfolio(portfolio)

    return portfolio, action


if __name__ == "__main__":

    portfolio, action = check_or_open()
    print(action)
    print(f"Cash: {portfolio['Cash']}")
