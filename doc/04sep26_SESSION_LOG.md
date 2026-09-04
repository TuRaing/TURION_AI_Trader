# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260904-001

--------------------------------------------------

Date

04-Sep-2026

--------------------------------------------------

FIRST LIVE TEST OF YESTERDAY'S 07:58 IST UNCONDITIONAL RESTART - FOUND
BROKEN, ROOT-CAUSED, FIXED. User logged in this morning and asked for
a login check. VPS check found the running turion-event-driven process
still on a stale/expired token well after login had already landed a
fresh one in Firebase (websocket "Token is expired", OI snapshot fetch
failing with "Please provide valid token" every 5 min since 00:29 UTC/
05:59 IST). Scheduled a one-shot local check for 08:05 IST (~7 min
after the new cron's 07:58 IST fire time) to see whether yesterday's
fix actually worked, rather than manually restarting and losing the
chance to observe it.

RESULT: the new restart DID fire (confirmed via `grep CRON /var/log/
syslog` - all 3 `sudo systemctl restart ...` commands ran at 02:28:01
UTC / 07:58:01 IST) but had NO EFFECT - `journalctl -u turion-event-
driven` showed no Stop/Start activity at that timestamp, service kept
running on the old token uninterrupted. Root cause found and confirmed
by reproducing the exact cron command manually (`sudo -u turion bash
-c 'sudo systemctl restart turion-event-driven >> /var/log/turion-
daily-restart.log 2>&1'` -> exit code 1, "Permission denied"): `/var/
log/turion-daily-restart.log` (the new log file yesterday's crontab
lines redirect into) DID NOT EXIST, and the `turion` user cannot
CREATE new files directly in `/var/log/` (only append to files root
already created) - the shell's `>>` redirect setup fails before
`systemctl restart` ever runs. This is the EXACT SAME bug class first
found and fixed on 24-Aug for `turion-depth-verify.log`/`turion-tick-
compress.log` - that fix's lesson (pre-touch + chown any NEW log file
a turion cron job writes to) didn't get re-applied when yesterday's 3
new crontab lines were added.

Service was actually healthy at check time (08:05 IST) ONLY by
coincidence: `deploy.sh`'s own pre-existing 08:00 IST cron restart
(which redirects into `turion-deploy.log`, a log file that already
existed) found a new commit to pull - this session's own doc commits
from earlier - and restarted for THAT reason, picking up the fresh
token as a side effect. Had there been no new commit today (the normal
case most days), deploy.sh would not have restarted either, and the
stale-token gap from yesterday would have persisted uncaught straight
into market open, exactly like every day this week before yesterday's
fix.

FIX (user approved live, pre-market, no service restart needed since
already healthy): `touch /var/log/turion-daily-restart.log && chown
turion:turion /var/log/turion-daily-restart.log` on the VPS, matching
the exact ownership pattern of the 3 already-working turion log files
(`turion-depth-verify.log`, `turion-tick-compress.log`, `turion-
health-check.log`). Verified fixed by reproducing the append as
`turion` (`echo verify-append-works >> /var/log/turion-daily-restart.
log` -> exit code 0, line written) - did NOT re-run a live `systemctl
restart` to avoid an unnecessary extra restart of an already-healthy
process (the sudoers NOPASSWD path for that command is separately
already proven working, e.g. by deploy.sh's own restart today and by
every prior day's collector-start entries).

No code files changed - VPS-side file-permission fix only, same
category as 24-Aug's fix. Nothing to sync to `main` beyond this log.

==================================================

MARKET OPEN 09:15:03-09:15:42 - ALL 14 LIVE BOOKS LOCKED WITHIN 40
SECONDS, GENUINE FAST WHIPSAW (NOT A DATA BUG). NIFTY spot: 23,915 ->
23,948 in 8 seconds (open rally), then -> 23,939 in the next 7 seconds
(reversal) - real movement, same class as 03-Sep's incident, confirmed
via the real tick archive's SPOT records, not a stale/frozen print.
Every one of the 14 active books (st2_threshold/simple_st1_threshold/
oi_footprint families, prefixes ending "_eventdriven") entered PE at
09:15:03 right as spot was rallying against that direction, took an
immediate Stop-Loss, then re-entered PE again seconds later as RSI
stayed bearish - by 09:15:42 every book had independently hit either
its daily_loss_lock (2 consecutive losses) or daily_profit_lock,
computed live from each book's own reports/fyers_options_*_portfolio.
json (no persisted lock flag in the JSON - status was derived by
replaying each book's own real daily_loss_lock/daily_profit_lock
threshold logic against today's actual closed trades). Combined day
result across all 14: -Rs 14,622.61 (st2_threshold family net
positive - a big win before its lock landed offset the rest;
simple_st1_threshold family net negative - never got a winning trade
before locking).

User asked whether trailing stop-loss would help here - answered no:
the first losing trade (09:15:03->09:15:04, PnL -Rs 3,502) was stopped
out in 1 second, before ever moving into profit, so there was nothing
to trail. Trailing SL protects profit already made on a winning trade;
it does nothing for an immediate adverse move at entry, and nothing to
stop the RAPID RE-ENTRY into a new same-direction trade seconds after
a stop-out, which is the actual mechanism behind today's cascade. (A
`simple_st1_threshold_trailing2pct` book exists from the pre-event-
driven engine but was never migrated into the current 14-book roster -
confirmed orphaned, not a live option today.)

==================================================

COOLDOWN-AFTER-CLOSE BACKTEST FOR RSI-MOMENTUM (st2_threshold/
simple_st1_threshold) - SAME NEGATIVE CONCLUSION AS oi_footprint's
03-Sep TEST. Following directly from the trailing-SL answer above,
tested whether a cooldown-after-close gate (same idea already tried
for oi_footprint on 03-Sep, found weak there) helps the RSI-momentum
family's rapid re-entry problem instead. New script `scratch_rsi_
cooldown_backtest.py` (LiveTickRunner replay, real RSI seeding via
yfinance, N=2 daily_loss_lock ON, stale_print_debounce_ticks=10 ON -
matches every live RSI-momentum book exactly). Tested cooldowns of
15s/30s/60s/120s/300s against baseline (0s) across all 9 real tick-
archive days available at the time (21,24,25,26,27,28,31-Aug + 01,02-
Sep) plus today (04-Sep) = 11 days x 2 indices x 2 book families = 44
combinations.

Found and fixed a real bug in `_open_lines()` (inherited from
scratch_cooldown_backtest.py, 29-Aug) while running the sweep: a path
already ending in `.gz` was checked with `os.path.exists()` first,
which is True for the .gz file itself - so it opened the gzip file as
plain UTF-8 text instead of decompressing it, crashing 7 of the 11
days with UnicodeDecodeError. Fixed by checking the `.gz` suffix FIRST
before the exists() branch. Re-ran the affected 7 days after the fix.

RESULT (summed net PnL across all 44 combinations):

    300s cooldown     +Rs 13,682.26   (looks best - see caveat below)
    0s (baseline)     -Rs 33,784.60
    30s cooldown      -Rs 53,143.68
    60s cooldown      -Rs 62,254.76
    120s cooldown     -Rs 83,844.45
    15s cooldown     -Rs 115,003.60   (worst)

The apparent 300s win does NOT hold up: just 2 of the 44 combinations
(01-Sep BankNifty/simple_st1_threshold +Rs 45,941.85, 25-Aug BankNifty/
simple_st1_threshold +Rs 28,098.87) account for +Rs 74,040.72 - more
than the entire reported total. Removing just those 2 flips the 300s
total to -Rs 60,358.46, WORSE than baseline. 300s is also not more
often profitable than baseline (14/44 positive vs baseline's 15/44) -
it just occasionally hits a large win that dominates the sum, the
exact same fat-tail distortion already flagged for oi_footprint's
"consistent-signal" variant on 03-Sep. Every OTHER cooldown duration
(15s/30s/60s/120s) is unambiguously worse than baseline, several by a
large margin.

CONCLUSION: no cooldown duration is a reliable fix for RSI-momentum's
rapid-re-entry whipsaw - same finding as oi_footprint's 03-Sep test.
No code changes made to any live book. Both known whipsaw problems
(oi_footprint's same-direction-after-loss, RSI-momentum's rapid re-
entry after a fast-open stop-out) remain open, unsolved by every idea
tried so far this week.

==================================================

VPS DATA SYNC ATTEMPTED - LOCAL DISK FOUND COMPLETELY FULL (100%,
132KB free of 139GB). User asked to sync all VPS-side archived data
(ticks/OI/depth) to this machine. Synced cleanly: 2 missing tick days
(22-Aug, 29-Aug - both Saturdays, tiny/near-empty files) and today's
OI snapshot (`oi_040926.jsonl`). The depth (order-book) archive - see
this same log's earlier note that it had never been synced at all -
ran out of local disk space mid-transfer: 7 of 11 real trading days'
depth files copied successfully (~270MB), 1 arrived truncated (26-Aug,
~21MB of an expected ~53MB) and 3 arrived as 0-byte stubs (27,28,31-
Aug) before the disk filled. Removed the truncated/stub files (created
this session, safe to discard) rather than leave corrupt data next to
real archives. Did NOT attempt to free space or delete anything else -
this machine's disk usage is outside this project's scope and is the
user's call, not something to guess at. Remaining depth days (27,28,
31-Aug) still need syncing once space exists; nothing was deleted from
the VPS itself (that was separately proposed 04-Sep morning, sync-
first-then-clear-VPS, and remains un-actioned pending the local-disk
issue).

==================================================

Status

🟢 Stable

Current Version

v0.0.71 (unchanged - VPS-side permission fix only, no app code)

--------------------------------------------------

Next Session

1. Tomorrow (05-Sep) is the real clean test: verify the 07:58 IST
   restart now actually shows up as Stop/Start activity in `journalctl
   -u turion-event-driven` on its own, without needing deploy.sh's
   commit-gated restart to coincidentally cover for it.

2. Worth a quick sweep of any OTHER recently-added turion cron lines
   for the same "log file doesn't exist yet" trap before they get a
   chance to silently fail too - this is the second time this exact
   bug class has bitten a new log redirect (24-Aug, now 04-Sep).

3. Local disk (D:) is completely full (132KB free of 139GB) - blocks
   more than just this project's data sync (any new file write on this
   machine). User's own call on what to clear; needs resolving before
   the depth archive sync (3 days still missing: 27,28,31-Aug) or any
   other local data growth can continue.

4. Both whipsaw problems remain unsolved after this week's testing:
   oi_footprint's same-direction-after-loss (8 gate combinations tried,
   03-Sep) and RSI-momentum's rapid-re-entry-after-fast-open-stop-out
   (5 cooldown durations tried, 04-Sep). Neither cooldown, direction-
   flip, signal-consistency, nor trailing SL has produced a reliable
   fix - next idea needs to be genuinely different, not another
   variation on "wait before re-entering."

==================================================
