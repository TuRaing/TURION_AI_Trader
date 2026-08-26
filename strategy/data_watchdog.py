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

    if now.weekday() >= 5:
        return False

    now_hm = (now.hour, now.minute)

    if not (market_open_time <= now_hm <= market_close_time):
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
