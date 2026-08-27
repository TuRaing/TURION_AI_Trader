# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260827-001

--------------------------------------------------

Date

27-Aug-2026

--------------------------------------------------

REAL LIVE INCIDENT #4 - ALL 3 VPS SERVICES HIT SYSTEMD'S RESTART
LIMIT ON A STALE TOKEN, FIXED AT THE ROOT (not just restarted again).
At 03:00 UTC (08:30 IST), all 3 services (turion-event-driven,
turion-tick-collector, turion-depth-collector) hit `build_runners()`'s
initial `pick_atm_symbols()` call with a PRESENT-but-STALE Fyers
token (yesterday's, still sitting in Firebase since today's login
hadn't happened yet) - `RuntimeError: ... {'message': 'Please provide
valid token', 'code': -15, ...}`. This is a DIFFERENT failure mode
from the already-handled "no token at all" case (`if not access_token:
sys.exit(0)`) - a token being PRESENT but REJECTED by Fyers was never
caught, so it crashed the whole process. All 3 services burned through
systemd's entire `Restart=on-failure` budget (`StartLimitBurst=5`
within `StartLimitIntervalSec=300`) in under a minute, hit `Start
request repeated too quickly`, and sat fully "failed" (dead, no more
auto-retry) until the user noticed a "connection lost" push
notification, confirmed they'd just logged in, and asked for a check.
Verified the fresh token was genuinely valid (a real Fyers `/profile`
API call, not just "Firebase returned something"), confirmed ownership
was clean (0 root-owned files - today's `fix_ownership.sh` cron had
nothing to do), and manually restarted all 3 (`systemctl restart`
clears the "failed" state even without `reset-failed`, which `turion`
doesn't have sudo for).

User's own question, live: "पण असं का होत आहे" (why does this keep
happening) - explained the real mechanism (daily token expiry timing
varies with when the previous day's login happened; the 08:00 IST
auto-restart only helps if login has ALREADY happened by then; a login
landing after both the token's own expiry AND the 5-attempt/50-second
systemd retry budget being exhausted needs a manual restart every
time). User's own follow-up, the real fix direction: "pan crash
honya peksha fakta msg send karel asa karu na crash ka hote" (instead
of crashing, can't it just send a message - why does it crash at all).

FIX (commit 4e5b67ea8, "Retry startup on a stale token instead of
crashing") - strategy/fyers_options_engine.py's new `is_invalid_
token_error(error)` (pure, 3 new tests) detects Fyers' code -15
response specifically, distinct from any other RuntimeError (rate-
limiting, a real bug, etc.) which still crashes normally through the
existing `OnFailure=turion-alert@%N.service` path. All 3 entrypoints
(`run_event_driven_engine.py`, `run_tick_collector.py`, `run_depth_
collector.py`) now catch this ONE specific error at startup and retry
every 120s, INDEFINITELY (no retry cap - the whole point is "wait
however long the user's login actually takes", not just widen a
different timeout), re-fetching a fresh token from Firebase each
attempt, with exactly ONE push notification on the first failure (not
one per retry) so the user still knows to log in without being
spammed. `run_tick_collector.py`/`run_depth_collector.py`'s `main()`
(previously one large function doing everything inline) were split
into a thin retry wrapper + a new `_run_collector(access_token)`
helper to make this possible without restructuring their whole body -
`run_event_driven_engine.py` already delegated to `strategy/event_
driven_runner.py`'s own `main()`, so it only needed the wrapper added
around that existing call.

Deployed as `turion` (not root), verified live: all 3 services active,
0 root-owned files, clean startup with the (already-valid-by-then)
token - the actual stale-token retry PATH itself wasn't exercised live
this session (the token was already fixed by the time of the deploy),
only verified via the 3 new unit tests plus a clean import/syntax
check of all 3 entrypoints. This is now the FOURTH real live incident
across 3 days (25-Aug: ownership; 26-Aug: OOM-kill + WebSocket-
abandonment + 2 GitHub Actions bugs + ownership again; 27-Aug: this
one) that got a real, root-cause code fix rather than just being
restarted and left for next time.

==================================================

Status

🟢 Stable

Current Version

v0.0.65

Next Version

v0.0.66

--------------------------------------------------

Next Session

1. Watch whether the new stale-token retry path actually fires and
   recovers correctly the NEXT time a real token-expiry gap happens
   (likely tomorrow morning again, given the daily cycle) - this
   session only verified it via unit tests + a clean deploy, not a
   real live trigger, since the token was already valid by deploy
   time.

2. Carried over from 26-Aug: watch both GitHub Actions concurrency
   fixes and the data-staleness watchdog over a few more real trading
   days: none of the 4 incidents this week have repeated in exactly
   the same form yet, but each new day surfaces a genuinely different
   failure mode (ownership -> OOM -> WebSocket-abandonment -> GitHub
   Actions -> stale-token-crash) - worth staying alert rather than
   assuming "the VPS is now fully hardened" after any single fix.

3. Still open: the quote-fix vs plain-LTP slippage gap checkpoint is
   Friday 28-Aug-2026 (user's own explicit decision, 26-Aug) - don't
   act on it before then. oi_footprint_quote books still thin on data.
   turion-tick-collector's own auto-retry cron lines (separate from
   today's fix - this was about IN-PROCESS retry, not the VPS-level
   cron safety net turion-event-driven alone has), sync_ticks_from_
   vps.py exercise, and end-Sep-2026 statistical-tools checkpoint all
   still open from 24-Aug.

==================================================
