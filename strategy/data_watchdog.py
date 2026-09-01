import datetime

# Added 26-Aug-2026, real live incident: fyers_apiv3's own reconnect
# logic (data_ws.py, all 3 VPS services) gives up after 5 failed
# attempts - "Max reconnect attempts reached. Connection abandoned." -
# and does NOT crash the process or retry again afterward. The process
# stays alive (systemd's Restart=on-failure never triggers, since
# there's no exit code to react to) but the WebSocket feed is
# permanently dead until someone manually restarts the service. This
# happened live on ALL 3 services simultaneously right at market open
# (09:13-09:22 IST, 26-Aug-2026 - a Cloudflare 502 on Fyers' own
# WebSocket front end, confirmed via the real "cf-ray"/502 error in the
# journal) - 9+ minutes of dead trading data and zero decisions before
# a human noticed and manually restarted them.
#
# This module is the pure, testable decision behind the fix: each
# service tracks its own "last message received" timestamp (updated on
# EVERY WebSocket message, not just ones that trigger a trade decision)
# and a background thread periodically asks should_restart_for_stale_
# feed() whether enough silent time has passed DURING MARKET HOURS to
# justify a deliberate process exit - letting the already-proven
# systemd Restart=on-failure + OnFailure=turion-alert@%N.service
# machinery (same one every real crash this project has hit already
# goes through) pick the connection back up and notify the user,
# instead of building a second, parallel restart/alerting mechanism.


def _is_market_hours(now, market_open_time, market_close_time):
    """
    Shared by should_restart_for_stale_feed() and (added 01-Sep-2026)
    should_restart_for_stale_token() below - both need the exact same
    "is a deliberately-quiet/stale signal actually worth restarting
    over" gate (a weekday, within NSE's 09:15-15:30 IST session), and
    this project's own established rule is one place for a check like
    this, not two copies to keep in sync.
    """

    if now.weekday() >= 5:
        return False

    now_hm = (now.hour, now.minute)

    return market_open_time <= now_hm <= market_close_time


def should_restart_for_stale_feed(last_message_at, now, timeout_minutes=5,
                                   market_open_time=(9, 15), market_close_time=(15, 30)):
    """
    True only when ALL of: it's a weekday, `now` falls within
    [market_open_time, market_close_time] (inclusive - NSE's real
    09:15-15:30 IST session), and at least `timeout_minutes` have
    passed since `last_message_at` with no message at all.

    Deliberately False outside market hours - a quiet WebSocket before
    09:15 or after 15:30 is normal (no real tick flow to receive
    then), not a failure worth restarting over. `last_message_at`
    should be seeded to the connection's own start time by the caller
    (not None) so a service that never receives its first message
    still gets caught after `timeout_minutes`, not ignored forever.
    """

    if not _is_market_hours(now, market_open_time, market_close_time):
        return False

    return (now - last_message_at).total_seconds() >= timeout_minutes * 60


def watchdog_loop(get_last_message_at, timeout_minutes=5, check_interval_seconds=60,
                   ist=datetime.timezone(datetime.timedelta(hours=5, minutes=30))):
    """
    Blocking loop - run this in a daemon thread, one per service. Calls
    `get_last_message_at()` (a zero-arg callable, so the caller can
    hand in a live-updating closure/dict-getter rather than a snapshot)
    every `check_interval_seconds` and force-exits the WHOLE process
    (os._exit, not sys.exit - this runs in a background thread, where
    sys.exit()/SystemExit only kills that one thread, not the process)
    the moment should_restart_for_stale_feed() says so. A print right
    before exiting lands in the journal so a restart caused by this
    watchdog is distinguishable from any other exit reason.
    """

    import os
    import time

    while True:
        time.sleep(check_interval_seconds)
        now = datetime.datetime.now(ist)
        last = get_last_message_at()

        if should_restart_for_stale_feed(last, now, timeout_minutes=timeout_minutes):
            print(f"WATCHDOG: no WebSocket message in {timeout_minutes}+ min during market "
                  f"hours (last at {last}) - forcing a restart.")
            os._exit(1)


def should_restart_for_stale_token(last_valid_token_at, now, timeout_minutes=10,
                                    market_open_time=(9, 15), market_close_time=(15, 30)):
    """
    Added 01-Sep-2026, real live incident: a process that stays up
    across a calendar-day boundary (no crash, no new commit for
    deploy.sh's daily restart to act on) has NO way to pick up a fresh
    Fyers token on its own once it has already connected once -
    run_event_driven_engine.py's retry-on-stale-token wrapper (27-Aug)
    only runs BEFORE the FIRST successful build_runners() call; once
    past that, the process is in its main loop and never re-enters that
    wrapper. The periodic checks that keep running (OI snapshot refresh,
    ATM re-check) just kept reusing the SAME stale os.environ token
    forever - each one caught and logged its own failure
    ("continuing on the old signal"/"continuing on the old strike")
    rather than crashing, so the process never died and never got a
    chance to fetch a fresh token either. Caught manually 01-Sep before
    market open; this is the structural fix - same "let systemd's
    already-proven Restart=on-failure machinery recover it" philosophy
    as should_restart_for_stale_feed() above, just watching a DIFFERENT
    signal (successful REST calls, not WebSocket messages - a stale
    token doesn't necessarily stop ticks from arriving over an already-
    established WebSocket session, so the feed-staleness watchdog alone
    isn't guaranteed to catch this specific failure mode).

    True only when ALL of: it's a weekday, `now` falls within market
    hours, and at least `timeout_minutes` have passed since the last
    genuinely successful (non-token-error) REST call - meaning every
    periodic check in that whole window failed, not just one transient
    blip. Default 10 min (2 missed 5-min OI-refresh cycles) rather than
    5, deliberately less trigger-happy than the feed watchdog - a single
    failed poll is expected/harmless (see refresh_oi_snapshots()'s own
    "continuing on the old signal" comment), only a SUSTAINED run of
    failures indicates the token itself needs a fresh fetch.
    """

    if not _is_market_hours(now, market_open_time, market_close_time):
        return False

    return (now - last_valid_token_at).total_seconds() >= timeout_minutes * 60


def token_watchdog_loop(get_last_valid_token_at, timeout_minutes=10, check_interval_seconds=60,
                         ist=datetime.timezone(datetime.timedelta(hours=5, minutes=30))):
    """
    Added 01-Sep-2026 - see should_restart_for_stale_token()'s own
    docstring for the real incident. A separate loop/thread from
    watchdog_loop() above (not a shared/parameterized one) - DELIBERATE:
    that function is already live, proven, production infrastructure
    protecting all 3 VPS services' WebSocket feeds; this project's own
    "never modify a working module" rule (see fyers_options_engine.py's
    matching note elsewhere) applies here too - a small amount of
    duplicated loop shape is a better trade than any risk of a
    regression in the already-working watchdog.

    Same os._exit(1)-on-trigger mechanism, letting the same already-
    proven systemd Restart=on-failure path recover it. Run this
    ALONGSIDE watchdog_loop() (a service can have a stale feed, a stale
    token, or both - separate, complementary safety nets), each with
    its own get_last_*_at() closure/dict-getter.
    """

    import os
    import time

    while True:
        time.sleep(check_interval_seconds)
        now = datetime.datetime.now(ist)
        last = get_last_valid_token_at()

        if should_restart_for_stale_token(last, now, timeout_minutes=timeout_minutes):
            print(f"WATCHDOG: no successful Fyers REST call in {timeout_minutes}+ min during "
                  f"market hours (last valid token confirmation at {last}) - forcing a restart.")
            os._exit(1)
