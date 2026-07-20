# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260720-001

--------------------------------------------------

Date

20-Jul-2026

--------------------------------------------------

Version

v0.0.11 (no version bump - infra/ops work, no code
feature added)

==================================================

Today's Achievements

✅ Diagnosed the Android "App not installed" error
   that persisted even after uninstalling the old
   app - ruled out APK corruption via WhatsApp
   transfer (verified zip integrity, byte-identical
   file; the 155 MB vs 162 MB the user saw was just
   MiB vs MB display, not real data loss). Connected
   the phone via USB/adb and got the real Android
   installer error: INSTALL_FAILED_INSUFFICIENT_
   STORAGE (phone at 99% storage). User freed space,
   install succeeded via `adb install`.

✅ Verified the freshly-installed 5-tab app on the
   real device (screenshots from the user) - all 5
   tabs render, Portfolio/Watchlist show live data,
   Best Trade/News/History correctly show empty
   states pending their first automated run.

✅ Discussed with the user what "live," "AI," and
   "algo trading" actually mean in this project's
   current state - confirmed the "AI" Decision Engine
   is a transparent rule-based weighted scorer (not a
   trained ML model), no broker/algo execution exists,
   and Claude will never execute a real trade
   regardless of future broker integration (permanent
   CLAUDE.md rule). Discussed live-data architecture
   (15-min-lag GitHub Actions snapshot vs true
   real-time) and rough live-data cost
   (₹0-2500/month depending on broker).

✅ User decided the next-steps sequence (recorded in
   memory + PROJECT_STATUS.md): 1 week Daily-strategy
   review (~26-Jul) -> intraday strategy design/test
   -> broker + months of paper trading on real
   live data -> only then consider an ML model, since
   ML needs labeled real trade-outcome data, not
   purchased historical candles.

✅ Set up a scheduled task ("turion-daily-strategy-
   review", fires 26-Jul 09:00 IST) to automatically
   pull that week's paper trading results and prompt
   the user on the intraday-strategy go-ahead.

✅ Checked today's real trading activity - Watchlist
   Paper Trading: 1 closed trade (HDFCBANK, Stop Loss,
   -₹22.12), 13 open positions all showing live
   unrealized gains via the new Last Price field.
   Best Trade Engine: shortlist had 5 BUY + 1 SELL
   candidates but zero positions opened.

✅ Found the real reason the Best Trade Engine has
   zero trade outcomes: confirmed via the public
   GitHub REST API (no login needed) that both
   `best_trade_entry_scan.yml` (every 5 min intended)
   and `paper_trade.yml` (every 15 min intended) are
   badly under-firing on GitHub's free-tier scheduler
   - only ~3-4 runs/day actually happen, roughly 2
   hours apart, consistent across every trading day
   checked (15/16/17/20-Jul). This is a scheduling
   infrastructure limit, not a strategy/logic problem.

✅ Fixed it: set up cron-job.org (free) as an external
   trigger hitting both workflows' `workflow_dispatch`
   REST endpoint - Best Trade Entry Scan every 1 min,
   Watchlist Paper Trade every 15 min, both restricted
   to market hours/weekdays via crontab expressions.
   No workflow YAML changes needed (workflow_dispatch
   was already enabled on both). Verified both jobs
   work (204 No Content on TEST RUN) and that the
   dispatched runs actually appear on GitHub's Actions
   history. Auth: a fine-grained GitHub PAT scoped to
   only this repo, Actions read/write only.

==================================================

Bugs Fixed

• Android APK install failure - root cause was
  device storage (INSTALL_FAILED_INSUFFICIENT_
  STORAGE via adb), not signing or file corruption.

• GitHub Actions scheduled-workflow under-firing for
  both cron-based trading workflows - mitigated via
  an external cron-job.org trigger (see above). Not a
  code bug - a platform scheduling limitation.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data.
Report Engine displays. Excel Engine stores history.
Options logic kept fully separate from normal
NIFTY/stock trading logic.

Claude never executes a real trade - final action is
always the user's, regardless of any future broker
integration.

==================================================

Next Session

1. Verify (21-Jul onward) that the cron-job.org
   triggers are actually landing at the intended
   1-min / 15-min cadence, via the public GitHub API

2. Let the scheduled review (26-Jul 09:00 IST) run -
   review real Daily-strategy + Best Trade Engine
   results with the higher-frequency data now flowing

3. Only after that review: design + backtest an
   intraday strategy (ORB/VWAP-based)

4. Fix TATAMOTORS / LTIM ticker symbols

5. Commit Desktop App (PySide6), package as .exe

==================================================

END OF SESSION
