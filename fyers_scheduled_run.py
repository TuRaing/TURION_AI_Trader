import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import verify_connection
from strategy.fyers_daily_tasks import run_all_tasks

# Added 05-Aug-2026 - runs every few minutes through market hours (via
# an external cron-job.org trigger -> .github/workflows/
# fyers_scheduled_check.yml, same pattern as the existing yfinance
# Watchlist/Best Trade workflows), reusing the FYERS_ACCESS_TOKEN repo
# secret that fyers_trigger_run.py shared after the user's one morning
# login - NO fresh login here. If that secret is missing, empty, or the
# day has rolled over (Fyers tokens are daily), verify_connection()
# fails and this exits cleanly rather than running against a dead
# token and generating confusing downstream errors.


def main():

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"No valid Fyers session (token missing/expired) - skipping this run: {profile}")
        sys.exit(0)

    run_all_tasks()


if __name__ == "__main__":
    main()
