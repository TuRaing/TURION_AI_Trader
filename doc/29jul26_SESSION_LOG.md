# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260729-001 (cloud session - claude.ai/code, not a
local machine session - see 25-Jul/28-Jul logs for why
that distinction matters for this repo)

--------------------------------------------------

Date

29-Jul-2026

--------------------------------------------------

Version

v0.0.14 (no version bump - one manual recovery action,
fix itself deferred to the user)

==================================================

Today's Achievements

✅ Explained the Best Trade Engine vs Watchlist Paper
   Trading distinction to the user in detail (useful
   reference for future sessions - see 28-Jul log for the
   fuller writeup):
   - Best Trade Engine = intraday only, one locked pick,
     closes same day via Stop Loss / Target / forced
     Intraday Square-Off at 14:45 IST.
   - Watchlist Paper Trading = risk-managed swing trading
     (has a hard Stop Loss/Target on every trade, so not
     passive buy-and-hold), no time limit - stays open
     until Stop Loss / Target / a daily-candle SELL
     signal, can run for days to weeks.

✅ User asked to check why today's Best Trade Engine
   intraday position (TATASTEEL, opened 10:01 IST) hadn't
   closed yet. Investigated and found a real, live bug:

   ROOT CAUSE: .github/workflows/best_trade_squareoff.yml
   still uses GitHub's native `schedule:` trigger
   (`15 9 * * 1-5` = 14:45 IST) - it was never migrated to
   the cron-job.org external trigger that fixed this exact
   under-firing problem for Best Trade Entry Scan and
   Watchlist Paper Trade Check on 20-Jul (the assumption
   then was "square-off only fires once/day, races are
   unlikely, so the native trigger is fine" - true about
   races, but GitHub's scheduler is unreliable regardless
   of race risk for a low-traffic public repo).

   EVIDENCE: checked the last 7 calendar days of real
   square-off runs via the GitHub Actions API - every
   single one fired 2-3.5 hours late instead of at 14:45
   IST (20-Jul: +2h44m, 21-Jul: +2h04m, 22-Jul: +2h05m,
   23-Jul: +2h05m, 24-Jul: +1h57m, 27-Jul: +3h22m, 28-Jul:
   +2h13m). Today (29-Jul) it hadn't fired AT ALL by 16:32
   IST (1+ hour after NSE close) - the worst case of the
   pattern, and the one the user actually noticed.

   IMMEDIATE FIX: manually triggered
   best_trade_squareoff.yml via workflow_dispatch at 16:33
   IST. Closed TATASTEEL cleanly - Entry Rs 186.89, Exit
   Rs 187.60 (Intraday Square-Off), PnL +Rs 0.71. Verified
   in reports/best_trade_portfolio.json (Position: null).

   PERMANENT FIX: NOT YET DONE - deferred at the user's
   request (only actionable from their own cron-job.org
   account, and they wanted to do it once home rather than
   right now). Needs a third cron-job.org job POSTing to
   best_trade_squareoff.yml's workflow_dispatch endpoint,
   same pattern as the existing two (Best Trade Entry Scan
   Trigger, Watchlist Paper Trade Trigger) - see 20-Jul log
   for the exact setup (fine-grained PAT, Actions:
   read/write scope). Suggested cadence: once around 14:45
   IST is enough (unlike the 1-min/15-min triggers, this
   one doesn't need frequent firing - just reliable firing
   at roughly the right time, e.g. every 5 min from
   14:40-15:15 IST as a safety window, `is_new_entry`/
   `Position is None` guards already prevent any harm from
   firing when there's nothing to close).

==================================================

Bugs Fixed

• best_trade_squareoff.yml - NOT YET FIXED (root cause
  identified, one instance manually recovered - see
  above). GitHub's native cron under-firing (documented
  20-Jul for the other two trading workflows) also affects
  this one; it was simply never migrated to cron-job.org
  at the time. Until the user adds a cron-job.org trigger,
  expect this to keep firing 2+ hours late (or not at all)
  and to need manual workflow_dispatch recovery on days
  it's not caught.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data. Report
Engine displays. Excel Engine stores history. Options
logic kept fully separate from normal NIFTY/stock trading
logic.

Claude never executes a real trade - final action is
always the user's.

==================================================

Next Session

1. USER TO DO (at home): add a third cron-job.org trigger
   for best_trade_squareoff.yml's workflow_dispatch
   endpoint - see "PERMANENT FIX" above for the exact
   pattern to copy. Until then, watch for the position
   silently carrying past 14:45 IST again and recover
   manually the same way (workflow_dispatch via the GitHub
   Actions API/UI).

2. Let the (still-overdue) 26-Jul-style review happen at
   the next opportunity - both engines now have several
   more days of real results since the last check (28-Jul
   log): Watchlist net +Rs 469.36 as of 28-Jul, Best Trade
   Engine has had many more real trades since 21-Jul (see
   reports/best_trade_portfolio.json's Closed Trades for
   the full list) including today's TATASTEEL.

3. Apply strategy/transaction_costs.py's real cost model
   to the Watchlist and Best Trade Engine's own live
   evaluations (carried over from 23-Jul, still not done).

4. Commit Desktop App (PySide6), package as .exe (carried
   over).

5. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

END OF SESSION
