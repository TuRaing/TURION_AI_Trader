import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import generate_access_token, verify_connection
from strategy.fyers_options_collector import snapshot as collect_options_snapshot
from strategy.fyers_options_paper_trading import check_or_open as check_options_position
from strategy.fyers_paper_trading import run_watchlist_paper_trading
from fyers_daily_best_trade import main as run_best_trade_check
from data.watchlist import NIFTY_50_SYMBOLS, INDICES

# Added 04-Aug-2026 - the single entry point the "Login to Fyers" in-app
# WebView button triggers (via a GitHub Actions workflow_dispatch, see
# .github/workflows/fyers_trigger.yml). Takes the one-time auth_code
# from the app, exchanges it for today's access_token, and immediately
# runs every Fyers data task in this SAME process - the token is never
# written anywhere that outlives this one run (see strategy/
# fyers_auth.py's 04-Aug update). If the exchange itself fails (auth_code
# expired, wrong credentials, etc.) this exits non-zero before touching
# anything else, so a bad login attempt can't silently commit partial/
# stale state.


def main():

    auth_code = os.environ.get("FYERS_AUTH_CODE")

    if not auth_code:
        print("FYERS_AUTH_CODE not set - nothing to do.")
        sys.exit(1)

    print("Exchanging auth_code for today's access token...")
    generate_access_token(auth_code)

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"Login verification failed - aborting before running anything: {profile}")
        sys.exit(1)

    name = profile.get("data", {}).get("name", "(name unavailable)")
    print(f"Connected as {name}. Running today's Fyers tasks...")

    print("\n--- Options premium snapshot ---")
    try:
        count = collect_options_snapshot()
        print(f"Wrote {count} option-leg records.")
    except Exception as error:
        print(f"Options snapshot failed (continuing): {error}")

    print("\n--- Options paper trading check ---")
    try:
        _, action = check_options_position()
        print(action)
    except Exception as error:
        print(f"Options paper trading check failed (continuing): {error}")

    print("\n--- Swing (Watchlist) paper trading ---")
    try:
        symbols = dict(INDICES)
        for ticker in NIFTY_50_SYMBOLS:
            symbols[ticker.replace(".NS", "")] = ticker
        _, events = run_watchlist_paper_trading(symbols, period="6mo", interval="1d")
        print(f"{len(events)} Swing event(s) this run.")
    except Exception as error:
        print(f"Swing paper trading failed (continuing): {error}")

    print("\n--- Intraday (Best Trade) check ---")
    try:
        run_best_trade_check()
    except Exception as error:
        print(f"Intraday check failed (continuing): {error}")

    print("\nDone.")


if __name__ == "__main__":
    main()
