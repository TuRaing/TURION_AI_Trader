import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import verify_connection
from strategy.fyers_daily_tasks import run_options_snapshot, run_depth_snapshot, run_swing_and_intraday

# Added 05-Aug-2026, split further same day - runs every 5 min through
# market hours (via an external cron-job.org trigger -> .github/
# workflows/fyers_scheduled_check.yml), reusing the FYERS_ACCESS_TOKEN
# repo secret that fyers_trigger_run.py shared after the user's one
# morning login - NO fresh login here. Deliberately does NOT include
# the options position check anymore - that moved to its own 1-min
# trigger (fyers_options_watch_run.py) since real option premium can
# move several % within a single minute (leverage), while Swing/
# Intraday don't benefit from checking faster than their own underlying
# timeframes. If the token is missing/expired, verify_connection()
# fails and this exits cleanly rather than running against a dead
# token and generating confusing downstream errors.
#
# run_depth_snapshot() added 17-Aug-2026, same 5-min cadence, same
# "doesn't need to be as frequent as position checks" reasoning as
# run_options_snapshot() - see strategy/fyers_daily_tasks.py's comment
# for the real Fyers rate-limit math (adds ~450 calls/day, under 0.5%
# of the 1,00,000/day quota).


def main():

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"No valid Fyers session (token missing/expired) - skipping this run: {profile}")
        sys.exit(0)

    run_options_snapshot()
    run_depth_snapshot()
    run_swing_and_intraday()


if __name__ == "__main__":
    main()
