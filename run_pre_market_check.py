import datetime
import glob
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token
from report.market_checks import format_pre_market_checklist, market_check_log_filename

# Added 19-Aug-2026 - the first of the user's 3 daily checks (pre-market,
# running-market [run_market_check.py], after-market). Live wiring for
# report/market_checks.py's format_pre_market_checklist(), same pattern
# as run_market_check.py: one command, scheduled via cron before 09:15
# IST market open. DEPLOYED TO THE VPS 20-Aug - see run_market_check.
# py's matching comment for why _resolve_access_token() tries Firebase
# first, local .env second.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DATA_BASE_URL = "https://api-t1.fyers.in/data"
LOG_DIR = os.path.join("logs", "market_checks")


def _resolve_access_token():
    from report.firebase_realtime_sync import fetch_access_token

    token = fetch_access_token()

    return token if token else get_access_token()


def _headers():
    return {"Authorization": f"{_app_id()}:{_resolve_access_token()}"}


def _token_is_ready():
    try:
        response = requests.get(
            f"{DATA_BASE_URL}/quotes",
            headers=_headers(),
            params={"symbols": "NSE:NIFTY50-INDEX"},
            timeout=15,
        )
        data = response.json()
        return data.get("s") == "ok" and bool(data.get("d"))
    except Exception:
        return False


def _open_positions():
    open_positions = []

    for path in sorted(glob.glob(os.path.join("reports", "*_portfolio.json"))):
        name = os.path.splitext(os.path.basename(path))[0]

        try:
            with open(path, encoding="utf-8") as fh:
                portfolio = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue

        position = portfolio.get("Position")
        if position:
            open_positions.append((name, position))

    return open_positions


def run_check():
    now = datetime.datetime.now(IST)

    token_ready = _token_is_ready()
    open_positions = _open_positions()

    report = format_pre_market_checklist(now, token_ready, open_positions)

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "pre_market_" + market_check_log_filename(now))
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"\nWritten to {log_path}")

    return log_path


if __name__ == "__main__":
    run_check()
