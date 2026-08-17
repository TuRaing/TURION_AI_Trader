import datetime
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token
from strategy.fyers_options_collector import fetch_option_chain

# Added 17-Aug-2026 - separate collector, does NOT modify fyers_options_
# collector.py, per this repo's engine-separation rule. Follow-up to the
# 17-Aug spread-cost work (SPREAD_COST_PCT_NIFTY/BANKNIFTY in strategy/
# options_transaction_costs.py, measured from options_premium_history.
# jsonl's real Bid/Ask): that only covers the TOP-of-book spread. The
# remaining slippage gap is market-DEPTH/size-impact cost - if a real
# order's lot count exceeds what's resting at the best price, it would
# fill partly at worse levels. Fyers' /depth endpoint returns real
# 5-level order-book depth (price/volume/order-count per level, both
# sides) - this collector snapshots it for the ATM CE/PE leg of each
# index (same ATM convention as fyers_options_engine.py's _pick_atm_
# leg - round(spot/strike_step)*strike_step), going forward, the same
# "collect real data first, measure later" approach already used for
# the spread work - no real depth data existed before this.
#
# VERIFICATION CAVEAT: Fyers' own docs did not publish a complete, exact
# JSON response example for /depth at the time this was written (only
# the inner field names - bids/ask/totalbuyqty/totalsellqty/price/
# volume/ord - confirmed via community/SDK source, not a raw response
# sample). This assumes the SAME outer envelope this project's own
# _fetch_quote() already uses successfully for the sibling /quotes
# endpoint (`{"s":"ok","d":[{"n":symbol,"v":{...fields...}}]}`), since
# both are Fyers v3 market-data endpoints under the same base URL and
# both accept a symbol (or comma-separated symbol list) parameter.
# COULD NOT be live-tested before committing - the local session's
# Fyers token is expired AND Fyers' own daily API quota was exhausted
# today (see PROJECT_STATUS.md's 17-Aug entries) - both block a real
# call from anywhere right now. Parsing is defensive: an unexpected
# shape is printed and skipped, not crashed on, so the very first real
# run (once quota resets) either works or self-diagnoses cleanly
# instead of silently writing garbage.
#
# API-QUOTA CONSCIOUS BY DESIGN: only the ATM strike's CE+PE (not the
# full 5-strike chain fetch_option_chain() itself covers) gets a depth
# call - 2 depth calls/index = 4 total per snapshot() run, plus the 2
# option-chain calls already needed to find the ATM strike. Matches
# fyers_options_collector.py's own "manual-run, not continuous" nature
# - NOT wired into any GitHub Actions workflow/cron trigger here, given
# today's real API-limit-exhaustion finding.

DATA_BASE_URL = "https://api-t1.fyers.in/data"
ARCHIVE_PATH = os.path.join("reports", "options_depth_history.jsonl")

INDEX_STRIKE_STEP = {
    "NSE:NIFTY50-INDEX": 50,
    "NSE:NIFTYBANK-INDEX": 100,
}


def _headers():
    return {"Authorization": f"{_app_id()}:{get_access_token()}"}


def fetch_depth(fyers_symbol):
    """
    One live 5-level order-book depth snapshot for a single option
    symbol. Returns the raw Fyers response dict - caller checks
    response["s"] == "ok" before trusting the shape (see module
    docstring's verification caveat).
    """

    response = requests.get(
        f"{DATA_BASE_URL}/depth",
        headers=_headers(),
        params={"symbol": fyers_symbol, "ohlcv_flag": "1"},
        timeout=15,
    )

    return response.json()


def _atm_ce_pe_symbols(underlying_symbol, strike_count=5):
    """
    One option-chain snapshot (reuses fyers_options_collector.py's
    fetch_option_chain(), never duplicated) - returns (spot, atm_strike,
    ce_symbol, pe_symbol), any of which may be None if the chain
    response didn't have what was needed.
    """

    data = fetch_option_chain(underlying_symbol, strike_count)

    if data.get("s") != "ok":
        print(f"[skip] {underlying_symbol} option chain: {data.get('message', data)}")
        return None, None, None, None

    legs = data.get("data", {}).get("optionsChain", [])
    spot = next((leg.get("ltp") for leg in legs if leg.get("strike_price") == -1), None)

    if spot is None:
        print(f"[skip] {underlying_symbol}: could not read spot from option chain response")
        return None, None, None, None

    strike_step = INDEX_STRIKE_STEP[underlying_symbol]
    atm_strike = round(spot / strike_step) * strike_step

    ce_symbol = next((leg.get("symbol") for leg in legs
                       if leg.get("strike_price") == atm_strike and leg.get("option_type") == "CE"), None)
    pe_symbol = next((leg.get("symbol") for leg in legs
                       if leg.get("strike_price") == atm_strike and leg.get("option_type") == "PE"), None)

    return spot, atm_strike, ce_symbol, pe_symbol


def _parse_depth_response(data, fyers_symbol):
    """
    Pure function - extracts the depth fields dict from a raw /depth
    response, assuming the same `{"d":[{"n":symbol,"v":{...}}]}` shape
    _fetch_quote() already relies on for /quotes. Returns None (never
    raises) on any unexpected shape, so snapshot() can skip that one
    symbol instead of crashing the whole run - see module docstring's
    verification caveat.
    """

    if data.get("s") != "ok" or not data.get("d"):
        print(f"[skip] {fyers_symbol} depth: {data.get('message', data)}")
        return None

    for entry in data["d"]:
        if entry.get("n") == fyers_symbol and "v" in entry:
            return entry["v"]

    print(f"[skip] {fyers_symbol} depth: unexpected response shape - {data}")
    return None


def snapshot(underlying_symbols=("NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX")):
    """
    Takes one ATM CE + ATM PE depth snapshot per underlying, appends
    each as its own JSON line to ARCHIVE_PATH (creating it if needed).
    Safe to call repeatedly - every call just appends, never overwrites.

    Returns
    -------
    int - number of depth records written this call.
    """

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    written = 0

    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)

    with open(ARCHIVE_PATH, "a", encoding="utf-8") as archive_file:

        for underlying_symbol in underlying_symbols:

            spot, atm_strike, ce_symbol, pe_symbol = _atm_ce_pe_symbols(underlying_symbol)

            if spot is None:
                continue

            for option_type, leg_symbol in (("CE", ce_symbol), ("PE", pe_symbol)):

                if leg_symbol is None:
                    print(f"[skip] {underlying_symbol} ATM {option_type}: not found in option chain response")
                    continue

                raw = fetch_depth(leg_symbol)
                fields = _parse_depth_response(raw, leg_symbol)

                if fields is None:
                    continue

                record = {
                    "Snapshot Time (UTC)": timestamp,
                    "Underlying": underlying_symbol,
                    "Spot": spot,
                    "Symbol": leg_symbol,
                    "Strike": atm_strike,
                    "Option Type": option_type,
                    "Total Buy Qty": fields.get("totalbuyqty"),
                    "Total Sell Qty": fields.get("totalsellqty"),
                    "Bids": fields.get("bids"),
                    "Asks": fields.get("ask"),
                    "LTP": fields.get("ltp"),
                }

                archive_file.write(json.dumps(record) + "\n")
                written += 1

    return written


if __name__ == "__main__":

    count = snapshot()
    print(f"Wrote {count} depth records to {ARCHIVE_PATH}")
