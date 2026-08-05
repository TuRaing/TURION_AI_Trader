import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import verify_connection
from strategy.fyers_daily_tasks import run_options_check

# Added 05-Aug-2026 - the FAST, every-1-minute half of the automation:
# only the options position check (open/monitor/close against a real
# live quote), nothing else. Real option premium can move several %
# within a single minute (leverage - see 04-Aug's research finding
# that a routine 0.1% NIFTY move can swing an ATM option's value ~8%),
# so this checks far more often than Swing/Intraday need
# (fyers_scheduled_run.py, every 5 min) - deliberately kept minimal so
# a 1-min cadence doesn't cause overlapping/queued runs the way running
# the full task list that often would. Reuses the FYERS_ACCESS_TOKEN
# repo secret from the morning login - no fresh login here.


def main():

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"No valid Fyers session (token missing/expired) - skipping this run: {profile}")
        sys.exit(0)

    run_options_check()


if __name__ == "__main__":
    main()
