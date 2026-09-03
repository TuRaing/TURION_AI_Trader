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

    28 2 * * 1-5 sudo systemctl restart turion-event-driven
    28 2 * * 1-5 sudo systemctl restart turion-tick-collector
    28 2 * * 1-5 sudo systemctl restart turion-depth-collector

(02:28 UTC = 07:58 IST - 2 min before `deploy.sh`'s own 02:30 UTC run,
deliberately not the same minute to avoid both racing to restart the
same services at once. CHANGED same session from an initial 07:30 IST
pick to 07:58 IST, user's own explicit ask - login usually lands
07:00-07:30 IST, so 07:58 IST leaves real margin instead of assuming
login always beats a 07:30 restart.) Already covered by the existing
NOPASSWD sudoers scope (restart was already permitted per-service) -
no sudoers change needed. THREE separate crontab lines, not one
combined `systemctl restart a b c` command - sudoers only permits the
exact single-service command strings already granted, a combined
multi-service invocation would not match any of them and would
silently fail under cron (caught before installing, not after). This
is strictly additive to the existing fixes, not a replacement: if
login hasn't happened yet by 07:58 IST, the 27-Aug retry-on-stale-
token wrapper still takes over exactly as before.

Documented in all 3 `deploy/*.service` files (mirroring the existing
`turion-event-driven.service`/`turion-tick-collector.service`/
`turion-depth-collector.service` convention for VPS crontab entries)
so a future VPS reinstall reproduces this, not just the live crontab
having it. Installed live on the VPS crontab the same session (first
at 07:30 IST, then corrected to 07:58 IST minutes later at the user's
own request) - takes effect from tomorrow (04-Sep) morning, since
today's pre-market window had already passed by the time this was
built.

==================================================

TODAY'S RESULT - REAL VOLATILITY, NOT A DATA-QUALITY BUG, AND A REAL
DISTINCTION WORTH KEEPING IN MIND. Combined total across all 14 books:
-Rs 38,436, a reversal from 02-Sep's +Rs 61,003. 6 books (all the
"_lock_quoteX%" variants) show an IDENTICAL -Rs 5,586.22 - checked
rather than assumed it was another stale-print incident (`st2_
threshold_lock_quote0pt5pct`'s real trade JSON):

- 09:15:02 CE @ Rs 183.80, spot 24017.35 -> 09:15:03 exit @ Rs 177.25,
  spot 24006.4 (Stop Loss, -3.66%)
- 09:15:03 CE @ Rs 179.00, spot 24006.4 -> 09:15:04 exit @ Rs 175.75,
  spot 23989.5 (Stop Loss, -1.93%)

Genuinely different root cause from every prior incident this week:
spot ACTUALLY moved (~28 points down in 2 real seconds) - not a stale/
frozen print with zero spot movement like 31-Aug/01-Sep. RSI picked CE
(bullish) right as spot was genuinely falling fast at the open -
classic whipsaw, the exact failure mode the N=2 breaker was originally
built for (21-Aug), not the stale-print bug the debounce targets.

Real, useful clarification of what the debounce actually protects
against: it only requires 10 REAL ticks before trusting a price - on a
fast, genuinely volatile open, 10 real ticks can arrive within 1-2
seconds, so the debounce did its job (waited for real data) and still
couldn't prevent this, because the data was never bad to begin with.
Debounce = protection from BAD data; the N=2 breaker = protection from
GOOD but volatile data moving against the strategy. Two different,
complementary jobs - today's incident isn't evidence the debounce
failed, it's evidence of the OTHER, older, already-accepted risk this
project has lived with since 21-Aug. The breaker worked exactly as
designed both times today, capping each affected book at 2 losses
rather than letting it compound further.

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

1. Verify tomorrow (04-Sep) morning that the new unconditional 07:58
   IST restart actually fires and picks up the day's token cleanly
   (assuming login has happened by then) - the real first live test of
   today's fix, same as every other fix this week has needed its own
   live confirmation before being trusted.

2. If login typically happens AFTER 07:58 IST some mornings, this fix
   alone won't fully close the gap (the 07:58 restart would just repeat
   yesterday's pattern of "started but token still stale," relying on
   the existing 120s retry-on-stale-token wrapper to eventually pick up
   a later login). Worth watching whether that's common enough to need
   a second, later unconditional restart too, or whether the existing
   retry wrapper genuinely covers the gap fine once one fresh-enough
   restart has happened.

3. Carried over from 02-Sep: `oi_footprint`'s own same-direction-after-
   loss whipsaw is still unsolved (2 ideas falsified) - needs a
   genuinely different approach or more real OI data before trying
   again.

==================================================
