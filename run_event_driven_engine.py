import sys

sys.stdout.reconfigure(encoding="utf-8")

from report.firebase_realtime_sync import fetch_access_token
from strategy.event_driven_runner import main as run_event_driven_engine

# Added 18-Aug-2026 - the VPS entry point for tonight's WebSocket
# event-driven engine (strategy/event_driven_runner.py). Same "top-
# level script fetches real credentials, strategy/ module takes them
# as a plain parameter" split this project already uses for fyers_
# scheduled_run.py/fyers_trigger_run.py - keeps event_driven_runner.
# py's own main() testable/pure (just takes an access_token) rather
# than reaching into Firebase itself.
#
# Fetches today's access_token via Firebase Realtime Database (see
# report/firebase_realtime_sync.py's fetch_access_token() and fyers_
# trigger_run.py's matching sync_access_token() call, added the same
# day) - the VPS-specific delivery path, since a VPS is not a GitHub
# Actions runner and can never receive the FYERS_ACCESS_TOKEN repo
# secret the scheduled workflows use. If today's login hasn't happened
# yet (or Firebase itself isn't configured), exits cleanly rather than
# running against no token - same "skip cleanly, don't crash" rule
# fyers_scheduled_run.py's own verify_connection() check already uses.
#
# NOT LIVE-TESTED - this is the final piece of tonight's code-prep;
# actually running it needs a real VPS, fyers_apiv3 installed, a
# configured Firebase Realtime Database, and a real live connection
# attempt - none of which exist yet (see strategy/event_driven_
# runner.py and live_tick_harness.py's own matching caveats).


def main():

    access_token = fetch_access_token()

    if not access_token:
        print("No access_token available via Firebase yet (today's login hasn't run, or "
              "Firebase isn't configured) - skipping this start attempt.")
        sys.exit(0)

    print("Got today's access_token via Firebase - starting the event-driven engine...")
    run_event_driven_engine(access_token)


if __name__ == "__main__":
    main()
