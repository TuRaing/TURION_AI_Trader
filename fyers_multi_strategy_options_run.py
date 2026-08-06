import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import verify_connection
from strategy.fyers_options_engine import check_or_open
from strategy.options_strategies import ALL_STRATEGIES

# Added 06-Aug-2026 - runs every named strategy's check_or_open() once
# each, for every configured index. Same reuse-the-morning-login
# pattern as fyers_options_watch_run.py (no fresh login here) - not
# yet wired into a GitHub Actions workflow (manual-first, matching how
# every other Fyers piece started - see strategy/fyers_options_
# collector.py). A failure in one strategy/index must not stop the
# rest from being checked.


def main():

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"No valid Fyers session (token missing/expired) - skipping this run: {profile}")
        sys.exit(0)

    for cfg in ALL_STRATEGIES:

        try:
            _, action = check_or_open(cfg)
            print(f"[{cfg['name']} / {cfg['index']}] {action}")
        except Exception as error:
            print(f"[{cfg['name']} / {cfg['index']}] FAILED (continuing): {error}")


if __name__ == "__main__":
    main()
