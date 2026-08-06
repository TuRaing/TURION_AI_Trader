import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import verify_connection
from strategy.options_strategies import ALL_STRATEGIES

# Added 06-Aug-2026 - runs every named strategy's check_or_open() once
# each, for every configured index. Same reuse-the-morning-login
# pattern as fyers_options_watch_run.py (no fresh login here). A
# failure in one strategy/index must not stop the rest from being
# checked.
#
# UPDATED 06-Aug-2026 (same day) - the user wants each strategy
# independently pausable/resumable from cron-job.org's dashboard
# (e.g. turn off st2 without touching the other 3), which isn't
# possible if one cron-job.org job always runs all 8 configs -
# pausing that one job pauses everything. STRATEGY_NAME (env var, or
# argv[1]) filters ALL_STRATEGIES down to just that name's configs
# (both indices) - "all"/unset runs everything, unchanged from
# before, so this stays backward compatible with a single combined
# trigger too if ever wanted again.

STRATEGY_NAME = os.environ.get("STRATEGY_NAME") or (sys.argv[1] if len(sys.argv) > 1 else "all")


def main():

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"No valid Fyers session (token missing/expired) - skipping this run: {profile}")
        sys.exit(0)

    strategies = ALL_STRATEGIES if STRATEGY_NAME == "all" else [
        (check_fn, cfg) for check_fn, cfg in ALL_STRATEGIES if cfg["name"] == STRATEGY_NAME
    ]

    if not strategies:
        print(f"No strategy named '{STRATEGY_NAME}' found - nothing to check.")
        return

    for check_fn, cfg in strategies:

        try:
            _, action = check_fn(cfg)
            print(f"[{cfg['name']} / {cfg['index']}] {action}")
        except Exception as error:
            print(f"[{cfg['name']} / {cfg['index']}] FAILED (continuing): {error}")


if __name__ == "__main__":
    main()
