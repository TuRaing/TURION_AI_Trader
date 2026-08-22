import datetime
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
# FIXED 21-Aug-2026 - real bug caught live: under systemd, stdout isn't
# a TTY, so Python defaults to full block buffering (~8KB) instead of
# line buffering - every print() in this whole process (including
# every strategy/*.py module it imports) could sit unflushed for a
# long time rather than reaching `journalctl` promptly. Confirmed live
# with strategy/event_driven_runner.py's new OI-refresh confirmation
# log: the code was running correctly (verified independently via
# portfolio file mtimes ticking every second), but its print() never
# showed up after 6+ minutes - only stderr tracebacks (Python's
# default unhandled-exception handler, which isn't subject to this
# buffering) were ever visible, creating a false impression that real,
# working code had silently stopped running. line_buffering=True
# flushes on every newline, matching what anyone tailing `journalctl
# -u turion-event-driven -f` actually expects.

from report.firebase_realtime_sync import fetch_access_token
from strategy.event_driven_runner import main as run_event_driven_engine
from strategy.execution_backend import resolve_execution_backend

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
#
# TURION_EXECUTION_MODE - added 18-Aug-2026, at the user's request:
# resolved HERE (this is the "top-level script resolves real config"
# half of the split described above), so going from paper to real
# (live) trading later needs only this one env var changed on the VPS
# - no code in strategy/event_driven_runner.py, event_driven_engine.py,
# or live_tick_harness.py ever needs to change. Defaults to "paper" if
# unset. See strategy/execution_backend.py's module docstring - "live"
# deliberately isn't built yet and raises a clear error rather than
# silently running as paper or crashing unexplained.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def main():

    # Added 22-Aug-2026 - real bug caught live: a Saturday systemd
    # restart (deploying new strategy code, market genuinely closed -
    # no reason today's Fyers login has run) reached build_runners()'s
    # unguarded pick_atm_symbols() -> _fetch_option_chain() call, which
    # raised on the stale/absent token and crashed the whole process -
    # then kept crash-looping (Restart=on-failure, RestartSec=10) until
    # systemd's StartLimitBurst=5/StartLimitIntervalSec=300 gave up.
    # Harmless (market was closed, no trade was ever at risk of being
    # missed) but pure noise - checked FIRST, before even fetching a
    # token, same "skip cleanly, don't crash" rule the token check right
    # below already uses. Weekends only (NSE holidays - Diwali, Republic
    # Day, etc. - aren't covered; would need a maintained holiday
    # calendar, a separate, larger feature).
    now_ist = datetime.datetime.now(IST)
    if now_ist.weekday() >= 5:  # Saturday=5, Sunday=6
        print(f"{now_ist.strftime('%A')} - NSE is closed on weekends, skipping this start attempt.")
        sys.exit(0)

    execution_backend = resolve_execution_backend(os.environ.get("TURION_EXECUTION_MODE", "paper"))

    access_token = fetch_access_token()

    if not access_token:
        print("No access_token available via Firebase yet (today's login hasn't run, or "
              "Firebase isn't configured) - skipping this start attempt.")
        sys.exit(0)

    print("Got today's access_token via Firebase - starting the event-driven engine...")

    # FIXED 21-Aug-2026 - real bug hit live: build_runners() calls
    # pick_atm_symbols() -> fyers_options_engine.py's _fetch_option_
    # chain()/_headers(), which ALWAYS calls strategy/fyers_auth.py's
    # get_access_token() (reads the LOCAL .env's FYERS_ACCESS_TOKEN) -
    # never wired to accept the Firebase-sourced token above. The VPS's
    # .env has no FYERS_ACCESS_TOKEN key at all (only FYERS_APP_ID +
    # the Firebase keys), so this crashed every time with "No FYERS_
    # ACCESS_TOKEN found". Same underlying issue would also hit
    # _seed_candles()/_previous_close() (strategy/fyers_data.py's own
    # _headers(), identical pattern). FIX: set the env var directly
    # rather than touching fyers_options_engine.py/fyers_data.py (both
    # "never modify a working module" - used by 60+ live polling
    # books) - get_access_token()'s own load_dotenv(..., override=True)
    # only overrides keys THAT EXIST in .env, and the VPS's .env has no
    # FYERS_ACCESS_TOKEN key to conflict with this, so every downstream
    # caller picks up the correct token with zero changes to any of
    # those shared modules.
    os.environ["FYERS_ACCESS_TOKEN"] = access_token

    run_event_driven_engine(access_token, execution_backend)


if __name__ == "__main__":
    main()
