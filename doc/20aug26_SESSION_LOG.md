# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260820-001

--------------------------------------------------

Date

20-Aug-2026

--------------------------------------------------

HEALTH-CHECK SCHEDULING - TRIED SESSION-CRON, THEN GITHUB ACTIONS,
THEN PAUSED PENDING VPS - continuation of 19-Aug's report/market_
checks.py build (see doc/19aug26_SESSION_LOG.md). Today's session
tried actually running it on demand and hit a real gap: run_pre_
market_check.py's Fyers-token check needs a LOCAL desktop login
(`python -m strategy.fyers_auth`, writes to this machine's own .env) -
completely separate from the mobile app's login, which updates the
FYERS_ACCESS_TOKEN GitHub Actions secret instead (confirmed by reading
strategy/github_secrets.py) and never touches local .env. Neither
local .env token had ever been read before today, because every one
of this project's 60+ modules runs on GitHub Actions, never on this
desktop - this was the first thing that needed live data run locally,
which is why the gap never surfaced before.

While checking GitHub for whether the morning's mobile login had
worked, found (and flagged, not fixed - see below) a real unrelated
bug: the "Fyers Login Trigger" workflow's retry-rebase logic breaks
when a push conflict retry hits leftover unstaged changes ("cannot
pull with rebase: You have unstaged changes"), losing that run's
secondary state commit even though the actual Fyers login step itself
succeeded fine. Filed as a background task rather than fixed inline
(out of scope for the health-check work) - fix is `git pull --rebase
--autostash` instead of the current plain `git pull --rebase`, same
pattern likely duplicated across other workflow YAML files.

Considered moving the check to run AS a GitHub Actions workflow
instead of locally (reuses the existing secret, no separate login,
survives this session closing) - user initially agreed, started
reading existing workflow YAML (.github/workflows/fyers_trigger.yml,
fyers_scheduled_check.yml) as a template, then the user reconsidered
mid-build and asked to just wait for the VPS instead of building
either the session-cron or the GitHub-Actions version.

RESULT: all 4 of yesterday's CronCreate jobs deleted. report/market_
checks.py + run_pre_market_check.py + run_market_check.py remain
committed, tested (17/17), and working when run directly - but NOTHING
IS SCHEDULED anywhere. Real scheduling stays parked until the VPS
(10-Sep track) exists. doc/PROJECT_STATUS.md's health-check entry
updated to reflect this explicitly, so a future session doesn't assume
these checks are still running or try to rebuild the GitHub-Actions
version without asking first.

Also same session: made a local backup of the repo (excluding
regenerable build/dist/mobile_app-build output, ~286MB of the real
~1.4GB folder) to D:\TURION_AI_Trader_19082026_backup_1 - confirmed
.env is included. Off-machine copy (OneDrive/USB) deferred - OneDrive
on this machine is installed but not signed in, and the user doesn't
have a spare pendrive on hand right now.

--------------------------------------------------

OVERNIGHT-CARRY PATTERN - CONFIRMED ACROSS ALL BOOKS, ONE SEPARATE
NEW FINDING - user asked to verify the known simple_st1_slcap_nifty
-Rs 1,23,027.15 trade (18-Aug entry 14:56:05, 19-Aug exit 08:33:03,
Stop Loss, 61.5x the intended cap - the date-blind-squareoff bug's
signature case, fixed 19-Aug) and check every other book for the same
pattern. Scanned every reports/*_portfolio.json's Closed Trades for
Entry-date != Exit-date, then ran report/market_checks.py's
detect_unusual_trade() on each.

CONFIRMED: exactly 10 OTHER books hit the identical 18-Aug-evening ->
19-Aug-08:31-08:33-exit pattern, matching 19-Aug's session log claim
of "10 other books" exactly - simple_st1_banknifty (-3,478, 4.1x),
simple_st1_slcap_banknifty (-10,912, 5.5x), st2_banknifty (-4,270,
5.0x), st2_nifty (-17,538, 50.1x), st2_slcap_banknifty (-5,284, 3.8x),
st2_slcap_nifty (-16,960, 50.1x), st3_banknifty (-11,056, 9.8x),
st3_nifty (-11,096, 50.2x), st3_slcap_banknifty (-6,494, 3.9x),
st3_slcap_nifty (-45,202, 50.0x). All already covered by the 19-Aug
squareoff.py fix - no new action needed on these.

NEW, SEPARATE FINDING - reports/fyers_options_portfolio.json (the
original single-strategy prototype, strategy/fyers_options_paper_
trading.py, "Strategy"/"Index" fields empty unlike every newer book):
one closed trade, Entry 2026-08-08 17:38:18 (a SATURDAY) -> Exit
2026-08-11 09:17:03, Net PnL -Rs 56,097.46 (30.3x the intended cap).
Checked further: this book's Entry Times on 6-Aug range from 14:41 to
20:58 IST (NSE closes 15:30) and include a second Saturday entry
(15-Aug 23:33). strategy/fyers_options_paper_trading.py has NO
day-of-week or market-hours gating anywhere in the module (confirmed
by reading it) - unlike every newer strategy module. This is a
DIFFERENT, NOT-YET-FIXED bug (the engine can apparently open/manage
positions from stale data outside real trading hours entirely,
not just fail to detect an already-past squareoff time) - NOT covered
by the 19-Aug squareoff.py fix, since that fix only addresses
DETECTING a past squareoff, not preventing entries when the market is
closed to begin with. Flagged as a background task, not fixed inline
(this old engine may be deprecated/superseded by fyers_multi_strategy_
options.yml - worth confirming that before spending fix effort on it).

--------------------------------------------------

Next Session

1. Same as 19-Aug's item 1 (Firebase Console + service account key) -
   still open, still the real unblock for durable scheduling.

2. Same as 19-Aug's item 2 (durable Scheduled Task) - still open.
   Do NOT default to a GitHub-Actions-workflow version of the health
   check without asking the user first - already explicitly declined
   once today (20-Aug) in favor of waiting for the VPS.

3. Resume the paused Vultr VPS signup walkthrough - unchanged from
   19-Aug's item 3.

4. Low-priority, flagged not fixed: the git-rebase-retry bug in
   .github/workflows/fyers_trigger.yml's "Commit updated Fyers state"
   step (`git pull --rebase` -> `git pull --rebase --autostash`,
   check other workflow YAML files for the same duplicated pattern).
   A background task was spawned for this same session - check if it
   was picked up before redoing the investigation.

5. Off-machine backup copy (OneDrive sign-in, or a USB/pendrive once
   the user has one) - the local D:\ backup made today does not
   protect against this laptop itself failing/being lost.

6. NEW, flagged not fixed: strategy/fyers_options_paper_trading.py
   (reports/fyers_options_portfolio.json) has no day-of-week/market-
   hours gating - see "OVERNIGHT-CARRY PATTERN" above. First confirm
   whether this old single-strategy prototype is still actively
   scheduled (fyers_options_watch.yml, cron-job.org-triggered - can't
   check from here) or superseded/dead, before deciding whether it's
   worth fixing at all.

==================================================

END OF SESSION
