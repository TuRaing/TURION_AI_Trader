# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260901-001

--------------------------------------------------

Date

01-Sep-2026

--------------------------------------------------

MORNING CHECK - REAL GAP FOUND AND FIXED BEFORE MARKET OPEN: A LONG-
RUNNING PROCESS NEVER RE-FETCHES A FRESH TOKEN ON ITS OWN. Routine
pre-market VPS check (deployed commit `033024e36` from 31-Aug's
debounce deploy still active, all 3 services "active") found the
user's ~07:00 IST login had NOT reached the running processes even
after `run_pre_market_check.py` (a fresh, direct Firebase read)
confirmed the token WAS ready in Firebase.

Root-caused rather than assumed a transient blip: `systemctl status`
showed all 3 services' Main PID unchanged since 31-Aug 15:57:55 UTC
(21:27 IST) - 10+ hours, spanning the calendar-day boundary, with NO
restart since yesterday evening's debounce deploy. `run_event_driven_
engine.py`'s outer retry loop (the one that re-fetches from Firebase
every 120s - built 27-Aug for exactly the "stale token at startup"
case) only runs BEFORE `build_runners()` first succeeds; once
connected, the process moves into its main loop and never re-enters
that outer wrapper unless a NEW RuntimeError is raised. The periodic
INNER checks that run once connected (OI snapshot refresh every 5 min,
ATM re-check) just reuse whatever `FYERS_ACCESS_TOKEN` was set in
`os.environ` at that one-time startup - they catch and log a failure
("continuing on old signal"/"continuing on old strike") rather than
crashing, so the process never dies and never gets a chance to pick up
a fresh token, even though a perfectly valid one is sitting in Firebase
the whole time.

Practical consequence: a process that happens to stay up across a
midnight boundary (no crash, and no new commit for deploy.sh's daily
08:00 IST restart to act on) will NEVER pick up that day's login on
its own - neither the daily deploy restart (only fires on a new
commit) nor the existing crontab safety net (`systemctl start`, a
no-op on an already-active service) covers this case. Would have meant
ZERO real trades across all 14 event-driven books today if not caught
before 09:15 IST market open.

FIXED for today: verified no open positions (all closed positions were
from the older, unrelated GitHub-Actions-driven polling engine, not
this VPS), manually restarted all 3 services at 07:50 IST. Confirmed
clean: "Got today's access_token via Firebase..." and (31-Aug's own
new log line) "Successfully connected - build_runners() completed...
today's token is valid" for all 3. `data/ticks/ticks_010926.jsonl` and
`data/depth/depth_010926.jsonl` confirmed writing fresh.

NOT YET FIXED STRUCTURALLY - this is a real, previously-unknown gap in
the retry-on-stale-token design (27-Aug) that only covers STARTUP
staleness, not a token going stale WHILE the process is already
running across a day boundary. Worth a permanent fix next session -
options: (a) the periodic OI-refresh/ATM-recheck failure paths could
themselves re-fetch from Firebase and update `os.environ` on failure,
same pattern as the outer wrapper already does; (b) extend `strategy/
data_watchdog.py`'s existing stale-feed detection to also force an
`os._exit()` restart if a token-related error persists past some
threshold during market hours - letting the already-proven systemd
Restart=on-failure path recover it, same philosophy as the 28-Aug
watchdog. Not built today - flagging only, real trading risk avoided
this time only because it was caught manually before market open.

==================================================

Status

🟢 Stable (after this session's manual fix)

Current Version

v0.0.70

Next Version

v0.0.70 (no code shipped - pure operational fix + a real design gap
flagged for next session)

--------------------------------------------------

Next Session

1. Build a structural fix for today's real gap (see above) - a long-
   running process currently has NO way to recover from a token going
   stale mid-session across a day boundary, only from being stale at
   its own startup. High priority - today's near-miss would have meant
   a full trading day with zero real trades if not caught manually
   before 09:15 IST.

2. Watch how `st2_threshold`'s 10-tick debounce (deployed 31-Aug)
   performs on its first real trading day, now that the token issue
   above is fixed and the book can actually trade today.

3. Carried over from 31-Aug: the debounce backtest sample is still
   only 5 days - keep collecting real trading days (today's tick/OI/
   depth archives) toward a larger, more reliable validation set.

==================================================
