import datetime
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token

# Added 04-Aug-2026 - manual-run collector that snapshots the REAL live
# NIFTY/BANKNIFTY option chain (bid/ask/LTP/OI/volume) from Fyers and
# appends it to a JSONL archive. Exists because Fyers (like every broker
# checked) purges EXPIRED option contracts from its symbol list, so
# there is no way to backfill historical option premium data - the only
# path to a real (non-estimated) options dataset is collecting it
# ourselves, going forward, one snapshot at a time. Analysis/data-
# gathering only - does not open any position, does not touch the
# yfinance-based paper trading engines, per this repo's engine-
# separation rule.

DATA_BASE_URL = "https://api-t1.fyers.in/data"
ARCHIVE_PATH = os.path.join("reports", "options_premium_history.jsonl")


def _headers():
    return {"Authorization": f"{_app_id()}:{get_access_token()}"}


def fetch_option_chain(symbol="NSE:NIFTY50-INDEX", strike_count=5):
    """
    One live snapshot of the option chain around ATM, for the nearest
    expiry. Returns the raw Fyers response dict.
    """

    response = requests.get(
        f"{DATA_BASE_URL}/options-chain-v3",
        headers=_headers(),
        params={"symbol": symbol, "strikecount": strike_count, "timestamp": ""},
        timeout=15,
    )

    return response.json()


def snapshot(symbols=("NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX"), strike_count=5):
    """
    Takes one snapshot per symbol, appends each option leg as its own
    JSON line to ARCHIVE_PATH (creating it if needed). Safe to call
    repeatedly - every call just appends, never overwrites.

    Returns
    -------
    int - number of option-leg records written this call.
    """

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    written = 0

    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)

    with open(ARCHIVE_PATH, "a", encoding="utf-8") as archive_file:

        for symbol in symbols:

            data = fetch_option_chain(symbol, strike_count)

            if data.get("s") != "ok":
                print(f"[skip] {symbol}: {data.get('message', data)}")
                continue

            chain = data.get("data", {})
            spot = None

            for leg in chain.get("optionsChain", []):

                if leg.get("strike_price") == -1:
                    spot = leg.get("ltp")
                    continue

                if not leg.get("option_type"):
                    continue

                record = {
                    "Snapshot Time (UTC)": timestamp,
                    "Underlying": symbol,
                    "Spot": spot,
                    "Symbol": leg.get("symbol"),
                    "Strike": leg.get("strike_price"),
                    "Option Type": leg.get("option_type"),
                    "Bid": leg.get("bid"),
                    "Ask": leg.get("ask"),
                    "LTP": leg.get("ltp"),
                    "OI": leg.get("oi"),
                    "Volume": leg.get("volume"),
                }

                archive_file.write(json.dumps(record) + "\n")
                written += 1

    return written


if __name__ == "__main__":

    count = snapshot()
    print(f"Wrote {count} option-leg records to {ARCHIVE_PATH}")
