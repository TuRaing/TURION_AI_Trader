# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260728-001 (cloud session - claude.ai/code, not a
local machine session)

--------------------------------------------------

Date

28-Jul-2026

--------------------------------------------------

Version

v0.0.13 (no version bump - one workflow fix, no new
feature)

--------------------------------------------------

Environment Note

This entry was written by a Claude **cloud** session
(remote sandbox, no local filesystem/USB/adb access -
see 25-Jul log for why that matters). The FCM APK
build + phone install itself was completed separately
by the user via a **local** Claude Code Desktop session
on their own machine (git pull + flutter build +
adb install) - that local session may not have logged
its own work here, so noting it explicitly for
continuity.

==================================================

Today's Achievements

✅ Confirmed the FCM push-notification feature (started
   25-Jul) is now fully live end-to-end: backend was
   already verified sending successfully (see 25-Jul
   log), and the user has now built the release APK via
   a local Claude Code session and installed it on their
   phone. Both Telegram and in-app push notifications are
   live going forward.

✅ Explained the difference between the two trading
   engines at the user's request (useful reference for
   future sessions too):
   - Best Trade Engine: intraday only. Opens 10:00-14:15
     IST, closes same day via Stop Loss / Target / forced
     "Intraday Square-Off" at 14:45 IST - never carries to
     the next day. One locked pick at a time.
   - Watchlist Paper Trading: swing-style, no time limit.
     Stays open until Stop Loss / Target / a daily-candle
     SELL signal - can hold for days to weeks (e.g.
     ULTRACEMCO has been open since 17-Jul). Clarified
     it's risk-managed swing trading (has a hard Stop Loss
     and Target on every trade), not passive buy-and-hold
     investment.

✅ Checked Watchlist Daily-strategy health at the user's
   request: net +Rs 469.36 across 5 closed trades
   (BAJAJ-AUTO Target +Rs 643.92 and HDFCBANK/INDUSINDBK/
   ADANIPORTS/BHARTIARTL Stop Loss losses), 14 open
   positions (2 new since 21-Jul: BAJAJ-AUTO re-entry
   22-Jul, HCLTECH 23-Jul, HEROMOTOCO/EICHERMOT 27-Jul).
   Manually verified all 14 against their Stop Loss/
   Target bands - none breached, monitoring correct.

✅ FOUND AND FIXED a real live bug while checking
   paper_trade.yml's run history: 3 consecutive failures
   this morning (03:07/03:22/03:37 UTC, 28-Jul) from a
   git push race. Root cause: paper_trade.yml never
   received the 21-Jul deeper git-race fix (discard-local-
   write, hard-reset, re-run-script-against-real-state)
   that the three Best Trade workflows got that day - it
   only had the earlier `git pull --rebase` line. Made
   worse by Best Trade Entry Scan's 1-minute cron-job.org
   cadence colliding with this 15-minute workflow's push
   to the same `main` branch (a ref-level race, not a
   same-file conflict - they touch different report
   files). Applied the identical retry+resync pattern used
   on the other three workflows, pushed to main (864e728),
   and verified live via a manual workflow_dispatch run
   (success).

==================================================

Bugs Fixed

• paper_trade.yml (Watchlist Paper Trade Check) - missing
  the 21-Jul git-race retry/resync fix that all three Best
  Trade workflows already had. Caused 3 real failed runs
  today before being caught and fixed. No trading data was
  lost (same as every prior instance of this class of bug
  - it's a "job reports failure" problem, not a
  correctness problem), but it did mean 3 consecutive
  15-min checks were skipped this morning.

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

1. Let the scheduled review (26-Jul review, now overdue -
   should happen at the next opportunity) look at both
   engines' now-multi-day real results: Watchlist net
   +Rs 469.36, Best Trade Engine's own real outcomes (see
   25-Jul log) - decide on Priority 2/3 next steps
   (intraday strategy, BANKNIFTY Momentum+VIX option
   premium cost model, etc.) per PROJECT_STATUS.md.

2. Apply strategy/transaction_costs.py's real cost model
   to the Watchlist and Best Trade Engine's own live
   evaluations (carried over from 23-Jul, still not done).

3. Commit Desktop App (PySide6), package as .exe (carried
   over).

4. Fix TATAMOTORS / LTIM ticker symbols (carried over).

5. Supertrend and CPR indicators (from the 22-Jul external
   strategy list) not yet built (carried over).

==================================================

END OF SESSION
