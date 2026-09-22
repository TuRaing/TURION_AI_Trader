# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260922-001

--------------------------------------------------

Date

22-Sep-2026

--------------------------------------------------

FULL DAY-BY-DAY PNL AUDIT - FILLED IN EVERY PREVIOUSLY-UNCHECKED
TRADING DAY. User asked for a day-wise PnL history covering every
day not yet individually reported this session. Pulled per-book,
per-day totals straight from the VPS's own portfolio JSONs (the only
authoritative live-trading record - see 04-Sep's log on why GitHub
never gets this data). Filled in 21,24,25,26,27,28,31-Aug, 01,02,03,
21,22-Sep (12 days total):

    21-Aug   -Rs  90,022   (the original whipsaw incident - N=2
                            breaker + debounce fixes trace back to this)
    24-Aug   -Rs  38,767
    25-Aug   -Rs  59,972
    26-Aug   +Rs  24,560
    27-Aug   -Rs  61,413
    28-Aug   -Rs  16,898
    31-Aug   -Rs 270,005   (worst day found - 4 books lost Rs 54,748
                            each on a single pair of trades)
    01-Sep   -Rs 169,938
    02-Sep   +Rs  61,003
    03-Sep   -Rs  38,436
    21-Sep   +Rs  11,606
    22-Sep  -Rs 101,964

While filling this in, found FOUR trading-weekday gaps with ZERO
trades across all 14 books: 11,12,19,20-Sep. Investigated each:

- 12-Sep and 19-Sep are SATURDAYS, 20-Sep is a SUNDAY - no trading
  expected, not an issue (the weekday>=5 startup guard is working
  correctly).
- 11-Sep is the one real gap: a Friday with zero trades. `journalctl`
  showed 195 consecutive "stale/invalid token, retrying in 120s"
  messages across the ENTIRE session window (09:01 IST through end of
  day) - the retry-on-stale-token wrapper (27-Aug) never once
  succeeded that day. User confirmed directly: they simply forgot to
  log in that morning. Not a code bug - the retry wrapper did exactly
  what it's supposed to do (keep retrying, never crash-loop) for a
  login that genuinely never happened.

==================================================

REAL GAP FOUND AND FIXED: THE MISSING-LOGIN NOTIFICATION WAS ONE-SHOT,
NOT REPEATED. Investigating 11-Sep found `run_event_driven_engine.py`
(the top-level VPS entrypoint, 27-Aug) already sends a push
notification on the FIRST stale-token retry failure ("TURION Engine -
Waiting for today's login") - so the user likely WAS notified around
09:01 IST that day. But the `notified` flag suppressed every
subsequent reminder for the rest of the day/session, so a missed or
dismissed first ping was the whole safety net - nothing else ever
reminded the user again, and the missed day only surfaced 11 days
later while building this PnL audit.

FIX: replaced the one-shot `notified` boolean with a `last_notified_at`
timestamp - the reminder now re-fires every `REMINDER_INTERVAL_SECONDS`
(1800s / 30 min) for as long as the retry loop keeps failing on a
stale token, instead of firing exactly once per session. Same
`send_push_notification()` call, same message, just no longer
suppressed after the first send. 634/634 existing tests still pass
(no test file specifically covers this top-level script, matching
this project's existing convention of leaving thin entrypoint glue
untested).

Deployed live: confirmed no open positions across any of the 14 books
first (market already closed, 23:34 IST), ran `deploy/deploy.sh` as
`turion` (not root, per the established ownership-drift lesson) via
`sudo -u turion bash -c`. Git fast-forwarded cleanly, dependencies
installed, all 3 services restarted successfully, reconnected with a
fresh token within 1 second. (The script's own final `sudo systemctl
status` step failed again - same known, harmless, pre-existing
sudoers gap noted 29-Aug: `restart`/`start` are in turion's NOPASSWD
scope, `status` isn't - the actual restarts had already succeeded.)

==================================================

Status

🟢 Stable

Current Version

v0.0.72 (repeating missing-login reminder, deployed live)

--------------------------------------------------

Next Session

1. If a missing-login day happens again, confirm the 30-min repeat
   reminder actually fires more than once in the logs - this fix is
   deployed but not yet live-tested against a real missing-login
   morning.

2. Both whipsaw problems (oi_footprint, RSI-momentum rapid-re-entry)
   remain open per 04/05-Sep's exhaustive testing - no new ideas this
   session, this was a pure PnL-audit and reliability-fix session.

==================================================
