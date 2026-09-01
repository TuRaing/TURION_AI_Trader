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

DEBOUNCE EXPANDED TO ALL 10 RSI-MOMENTUM BOOKS - REAL LIVE EVIDENCE
THE SAME MORNING, THEN A REAL DEPLOYMENT-TIMING LESSON THE SAME
AFTERNOON. Around mid-morning, `simple_st1_threshold` (debounce not
yet applied to it) hit the exact same stale-print-through-Stop-Loss
pattern the gate targets: 2 same-second 09:15:00 trades, spot barely
moved, Stop Loss fired but at -14.585%/-14.25% (far past the book's
own configured 3%) - the underlying tick itself was bad/stale, the SL
just exited at whatever price it could once threshold was crossed.
Meanwhile `st2_threshold` (debounce live since 31-Aug evening) lost
~74% less on the same morning (-Rs 7,617 vs -Rs 28,834). User's own
explicit choice, offered narrower alternatives: roll the debounce out
to all 9 remaining RSI-momentum books at once, not incrementally.

Implementation mirrors 31-Aug's exactly - `make_simple_st1_threshold_
event_cfg()` gained the same `stale_print_debounce_ticks` parameter
`make_st2_threshold_event_cfg()` already had, and `stale_print_
debounce_ticks: 10` was added to all 9 remaining books' cfg_overrides
in `event_driven_runner.py`. 1 new test (cfg pass-through), full suite
629/629 passing.

Deployed the SAME morning, ~09:56 IST - market was already open
(09:15). Verified no open positions first, but user's own real-time
correction arrived mid-deploy: "VPS ला धोका होईल असं काही करू नकोस -
संध्याकाळी किंवा सगळे trades stop झाल्यावर करूया" (don't do anything
that risks the VPS - let's do this in the evening or after all trades
stop). The deploy itself had already completed by the time this
landed (no way to un-restart) - verified clean afterward (0 open
positions at restart time, clean logs, correct commit) - but this is
now a firm rule going forward: no more VPS restarts/deploys during
market hours without asking first, regardless of how safe a given one
turns out to be in hindsight.

Checked today's real result after market close and found a genuine
deployment-TIMING lesson, not a gate-design problem: `simple_st1_
threshold`/`st2_threshold_lock` still show -Rs 28,834 today (identical
to what `simple_st1_threshold` alone showed BEFORE the expansion) -
because the market-open whipsaw at 09:15 IST already happened and
already locked those books via the N=2 breaker a full 40 minutes
BEFORE the 09:56 IST deploy landed. The debounce genuinely cannot
protect a trade that already happened before its own code was live.
Only `st2_threshold` (debounce since the previous evening) actually
benefited today. User asked whether the market-open buffer (tested and
rejected 31-Aug when combined with debounce - cancels debounce's own
benefit entirely) might help instead - re-explained why not: today's
loss was a deployment-timing fluke, not a gap the buffer would ever
have addressed, and stacking it back in would only weaken the debounce
again. Tomorrow (02-Sep) is the real first full-day test - debounce
is already live on all 10 books before the normal 08:00 IST pre-market
restart, so it will be active from market open for the first time.

==================================================

PERMANENT RULE ADDED TODAY, user's own explicit words: no VPS restart/
deploy during market hours (09:15-15:30 IST) without asking first,
full stop - not even when a real check (open positions, etc.) says
it's safe. The 09:56 IST mid-day deploy above turned out harmless in
hindsight, but that was verified AFTER the fact, and the user's own
correction landed WHILE it was happening - the rule going forward is
ask first, not "check first and proceed."

==================================================

STRUCTURAL FIX BUILT FOR THIS MORNING'S TOKEN-STALENESS GAP - A NEW,
SEPARATE TOKEN WATCHDOG. Built the real fix for the "Next Session" item
1 flagged this morning: `strategy/data_watchdog.py` gained `should_
restart_for_stale_token()` and `token_watchdog_loop()` - same
`os._exit(1)`-on-trigger philosophy as the existing 26-Aug feed
watchdog (let systemd's already-proven Restart=on-failure path recover
it), but watching a DIFFERENT signal: time since the last genuinely
successful (non-token-error) REST call, not WebSocket message
silence - deliberate, since a stale token doesn't necessarily stop an
already-established WebSocket session from delivering ticks, so the
feed watchdog alone wasn't guaranteed to catch this specific failure
mode. 10-minute default timeout (2 missed 5-min OI-refresh cycles,
deliberately less trigger-happy than the feed watchdog's 5 minutes - a
single failed poll is expected/harmless).

Refactored the shared weekday/market-hours gate into one `_is_market_
hours()` helper used by both watchdogs (this project's own "one place,
not two copies" rule) - but deliberately did NOT touch the existing,
already-proven `watchdog_loop()` function itself, or generalize it to
take a `should_restart_fn`, even though the loop shape is nearly
identical. Added a separate `token_watchdog_loop()` instead - "never
modify a working module" outweighs a small amount of duplicated loop
mechanics here, since `watchdog_loop()` is live production
infrastructure protecting all 3 VPS services right now.

Wired into `event_driven_runner.py`: a new `_last_valid_token_at`
tracker (seeded to "now" at successful `build_runners()`, same pattern
as the existing `_last_message_at`), updated by `oi_refresh_loop()`
only on a genuinely successful refresh (not on the except branch, so a
run of pure token-error failures correctly leaves it stale), and a new
`token_watchdog_loop()` thread running alongside the existing feed
watchdog thread - complementary, not a replacement.

5 new tests for `should_restart_for_stale_token()` (mirrors the
existing feed-watchdog test shape, plus one direct replay of this
morning's real incident - a token last valid at 31-Aug 21:27 IST,
correctly flagged as stale by the time market hours arrive the next
day). Full suite: 634/634 passing. NOT yet deployed to the VPS - per
today's own new rule, deploy is deferred to after asking, even though
market is now closed (16:24 IST) for the day.

==================================================

Status

🟢 Stable

Current Version

v0.0.71

Next Version

v0.0.71 (debounce expanded to all 10 RSI-momentum books, deployed
mid-morning - see the permanent no-market-hours-deploys rule above for
why that specific timing won't repeat; today's own result shows the
fix simply came too late in the day to help most books, not a design
problem)

--------------------------------------------------

Next Session

1. Build a structural fix for the stale-token-across-a-day-boundary
   gap found this morning (see above) - a long-running process
   currently has NO way to recover from a token going stale mid-
   session across a day boundary, only from being stale at its own
   startup. High priority - today's near-miss would have meant a full
   trading day with zero real trades if not caught manually before
   09:15 IST. Still open, not built today.

2. Tomorrow (02-Sep) is the real first full-day test of the debounce
   on all 10 books, deployed BEFORE the normal 08:00 IST pre-market
   restart this time (not mid-day) - check the real result once market
   closes.

3. Carried over from 31-Aug: the debounce backtest sample is still
   only 5 days - keep collecting real trading days (now including
   01-Sep's own tick/OI/depth archives) toward a larger, more reliable
   validation set.

==================================================
