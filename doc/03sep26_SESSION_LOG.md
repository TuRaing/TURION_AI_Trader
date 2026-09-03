# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260903-001

--------------------------------------------------

Date

03-Sep-2026

--------------------------------------------------

THIRD MORNING IN A ROW OF THE SAME STALE-TOKEN-ACROSS-A-DAY-BOUNDARY
GAP - FIXED FOR REAL THIS TIME, NOT JUST MANUALLY WORKED AROUND AGAIN.
Same pattern as 01-Sep and 02-Sep: services had been running unbroken
since the previous day (02-Sep 06:27:49 UTC / 11:57 IST), spanning
midnight, stale token this morning despite the user's ~07:58 IST login
already landing in Firebase. 01-Sep's `token_watchdog_loop` still
hasn't had a chance to prove itself, for the same reason each time -
it deliberately only acts DURING market hours (09:15-15:30 IST) by
design, and the stale state exists BEFORE that window every single
morning so far. Manually restarted again (verified no open positions
first) - clean reconnect confirmed.

User's own direct question this time, the right one: can this be made
to just happen automatically after login, instead of Claude manually
restarting every single morning? Real fix, not another manual step:
added an UNCONDITIONAL daily restart to `crontab -u turion` for all 3
services, independent of `deploy.sh`'s commit-gating (which only
restarts when there's a NEW commit to pull - the actual root cause of
why the daily 08:00 IST deploy never covered this):

    0 2 * * 1-5 sudo systemctl restart turion-event-driven
    0 2 * * 1-5 sudo systemctl restart turion-tick-collector
    0 2 * * 1-5 sudo systemctl restart turion-depth-collector

(02:00 UTC = 07:30 IST, 30 min before `deploy.sh`'s own 02:30 UTC run,
Mon-Fri only.) Already covered by the existing NOPASSWD sudoers scope
(restart was already permitted per-service) - no sudoers change
needed. THREE separate crontab lines, not one combined `systemctl
restart a b c` command - sudoers only permits the exact single-service
command strings already granted, a combined multi-service invocation
would not match any of them and would silently fail under cron (caught
before installing, not after). This is strictly additive to the
existing fixes, not a replacement: if login hasn't happened yet by
07:30 IST, the 27-Aug retry-on-stale-token wrapper still takes over
exactly as before.

Documented in all 3 `deploy/*.service` files (mirroring the existing
`turion-event-driven.service`/`turion-tick-collector.service`/
`turion-depth-collector.service` convention for VPS crontab entries)
so a future VPS reinstall reproduces this, not just the live crontab
having it. Installed live on the VPS crontab the same session - takes
effect from tomorrow (04-Sep) morning, since today's 07:30 IST window
had already passed by the time this was built.

==================================================

Status

🟢 Stable

Current Version

v0.0.71

Next Version

v0.0.71 (crontab-only fix - VPS-side change plus doc comments, no
Python/Dart code shipped)

--------------------------------------------------

Next Session

1. Verify tomorrow (04-Sep) morning that the new unconditional 07:30
   IST restart actually fires and picks up the day's token cleanly
   (assuming login has happened by then) - the real first live test of
   today's fix, same as every other fix this week has needed its own
   live confirmation before being trusted.

2. If login typically happens AFTER 07:30 IST some mornings, this fix
   alone won't fully close the gap (the 07:30 restart would just repeat
   yesterday's pattern of "started but token still stale," relying on
   the existing 120s retry-on-stale-token wrapper to eventually pick up
   a later login). Worth watching whether that's common enough to need
   a second, later unconditional restart too (e.g. a 08:45 IST one),
   or whether the existing retry wrapper genuinely covers the gap fine
   once one fresh-enough restart has happened.

3. Carried over from 02-Sep: `oi_footprint`'s own same-direction-after-
   loss whipsaw is still unsolved (2 ideas falsified) - needs a
   genuinely different approach or more real OI data before trying
   again.

==================================================
