# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260923-001

--------------------------------------------------

Date

23-Sep-2026

--------------------------------------------------

GITHUB ACTIONS HEALTH CHECK - FOUND AND FIXED A REAL, WEEK-LONG DATA-
LOSS BUG IN `fyers_multi_strategy_options.yml`. User asked to check
how GitHub Actions runs have been going. `gh run list` showed two
separate patterns:

1. A large burst of "cancelled" runs (95/100 recent) for the "Fyers
   Multi-Strategy Options Watch" workflow - expected, not a bug: this
   is GitHub's own concurrency-group behavior (only the latest queued
   run survives when several pile up faster than they can execute,
   see the workflow's own 07/26-Aug notes) given cron-job.org's ~1-min-
   per-strategy trigger rate.

2. A genuinely real problem: ~100 outright FAILURES over 15-22-Sep, all
   traced to the same root cause - a rebase CONTENT CONFLICT in
   `reports/fyers_options_st3_banknifty_portfolio.json`, recurring
   despite the workflow's existing shared concurrency group (added
   26-Aug specifically to prevent exactly this). The group serializes
   this workflow's own runs, but under cron-job.org's trigger rate,
   queued runs stack up faster than the OLD 3-attempt, no-delay retry
   loop could clear a conflict once one occurred.

REAL DATA-LOSS BUG FOUND while investigating: the retry loop's own
comment claimed "commit still exists locally for the next run (~2 min
later)" when all 3 attempts failed - this is FALSE. GitHub-hosted
runners are ephemeral (torn down at job end), so a run that exhausts
its retries doesn't defer its work to some future run - it loses that
run's real, already-computed trade/portfolio update permanently, with
no trace left anywhere. Every one of the ~100 failed runs this week
represents a genuinely lost update (though `st3_banknifty` isn't one
of the 14 live VPS books - it's an older GitHub-Actions-only strategy,
so no impact on the actual live trading books this project tracks
daily).

FIX: widened the retry loop from 3 attempts (no delay) to 8 attempts
with a short random backoff (5-15s) between each, spreading out
competing runs instead of retrying in lockstep - meaningfully reduces
(does not eliminate) the odds of exhausting retries under load.
Corrected the misleading "next run" comment to say plainly that a
failure after all retries is a real, permanent loss, not a deferral.
A genuine simultaneous conflict on a REAL portfolio file (not the
already-carved-out `fyers_candles.json` cache) still aborts rather
than guessing which side's trade data to keep - same safety principle
as the existing candle-cache special case, just with much wider margin
before that fallback is ever reached. Pushed directly (workflow YAML
files take effect on GitHub's side automatically - no VPS deploy step
applies here).

==================================================

Status

🟢 Stable

Current Version

v0.0.72 (unchanged - GitHub Actions workflow fix only, no VPS/app code)

--------------------------------------------------

Next Session

1. Watch `gh run list --workflow "Fyers Multi-Strategy Options Watch"
   --status failure` over the next few days to confirm the failure
   rate on `st3_banknifty` actually drops - this fix reduces the odds
   but wasn't live-load-tested against real concurrent trigger volume.

2. If failures persist even with 8 retries, the real fix is a proper
   JSON-aware merge for portfolio files (union the two runs' Closed
   Trades lists instead of a line-based git merge) - bigger change,
   only worth it if the wider retry margin alone doesn't resolve this.

==================================================
