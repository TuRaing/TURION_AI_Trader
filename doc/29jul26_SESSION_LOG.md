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

PART 2 (same day, separate session)

Session ID

S20260729-002 (local machine session - Claude Code
Desktop, D:\TURION_AI_Trader - has Flutter/adb/USB
access the cloud session in Part 1 does not)

--------------------------------------------------

Today's Achievements (Part 2)

✅ User couldn't tell Watchlist ("Swing") from Best Trade
   ("Intraday") apart in the app or in Telegram/push
   messages - just the raw names weren't enough context.
   Tagged both everywhere user-facing: Telegram/console
   message headers (report/report_engine.py - "(Swing)"/
   "(Intraday)" suffixes) and the Android app (AppBar
   titles get the full tag, bottom-nav labels just say
   "Swing"/"Intraday" given limited space). Display text
   only - no file/function/JSON-key renames, so live
   automation and the app's own data reads were unaffected.

✅ Portfolio and History tabs previously only ever showed
   Watchlist (Swing) data - Best Trade (Intraday)'s own
   portfolio file was never read there at all, so a closed
   intraday trade was invisible in the app once it left the
   Best Trade tab's single "today's position" view. Both
   tabs now fetch both portfolio files and show them in
   clearly separated, badge-tagged sections (Swing/
   Intraday), open positions and closed trades alike.

✅ Built a candlestick chart (tap any position/trade to
   open it) - three rounds of user feedback, each addressed
   same day:
   1. First version: bare candles, no numbers - useless per
      the user. Added a price axis, a selected-candle OHLC
      readout (defaults to the latest candle), tap/drag
      crosshair to inspect any candle, and period High/Low/
      Change stats.
   2. User asked where the trade's own buy/current-price
      comparison was - the chart had candles but no trade
      context. Added ChartReferenceLine overlays (dashed
      lines for Entry/Stop Loss/Target/Exit) plus a summary
      card (Entry price -> Current/Exit price, Rs and %
      difference, direction-aware so a SELL trade's math
      isn't inverted).
   Data source: a new backend engine (indicators-style -
   strategy/candle_data_engine.py + root refresh_candles.py)
   that fetches recent candles for every symbol referenced
   in either portfolio and writes reports/candles.json,
   piggybacked onto paper_trade.yml's existing 15-min
   external trigger rather than a new cron-job.org job.
   Periodic refresh (~15 min), not tick-by-tick live -
   documented as such in the app itself. Hand-rolled
   CustomPainter widget, no new pub.dev chart dependency
   (avoids a build-time version-resolution risk that
   couldn't be verified locally - no Flutter SDK on this
   machine either, same constraint as every prior session).

✅ Verified all of the above via 4 real GitHub Actions APK
   builds + adb installs on the user's phone (Motorola Edge
   20 Fusion) this session - each one caught something the
   others couldn't: local Dart syntax review can't substitute
   for an actual `flutter build apk` when there's no Flutter
   SDK to run `flutter analyze` against directly.

✅ CONFIRMED (3rd occurrence): every GitHub Actions APK
   build produces a differently-signed debug APK (no stable
   debug.keystore persisted across runners), so `adb install
   -r` fails with INSTALL_FAILED_UPDATE_INCOMPATIBLE against
   whatever was installed from the previous build - the old
   copy must be uninstalled first every time. Worked around
   manually again; a real fix (commit a fixed debug keystore,
   point Gradle at it) is still outstanding - see Known
   Issues in PROJECT_STATUS.md.

✅ Diagnosed a real network outage mid-session: github.com/
   api.github.com (and githubstatus.com) became unreachable
   from this machine for an extended period while google.com
   and raw.githubusercontent.com kept working - confirmed
   consistent across curl, PowerShell's Invoke-WebRequest,
   and the browser tool (ruling out a single-tool sandboxing
   artifact), no proxy/hosts-file cause found. Resolved by
   the user restarting their router - likely an ISP-side
   routing issue specific to GitHub's IP range, not fixable
   from software. Session date rolled from 28-Jul to 29-Jul
   during the outage.

--------------------------------------------------

Bugs Fixed (Part 2)

(None - see the recurring debug-keystore signing issue and
the transient network outage above, environment/tooling
friction rather than repo bugs.)

--------------------------------------------------

PART 3 (same day, continued)

✅ Fixed the recurring debug-keystore signing mismatch (item
   6 below, done same session): generated a fixed
   mobile_app/android/app/debug.keystore (standard Android
   debug credentials, not a secret) and added a "sharedDebug"
   signingConfig in build.gradle.kts pointing at it. Verified
   properly - built twice in a row and the second `adb
   install -r` succeeded with NO uninstall step first, unlike
   every prior build this week.

✅ Updated the Android App milestone in PROJECT_STATUS.md
   (item 7 below, done same session) to reflect the renamed
   tabs and the new chart screen.

✅ User asked why Intraday (Best Trade Engine) positions
   weren't closing on time - explained the real cause (see
   Part 1: best_trade_squareoff.yml's GitHub-native schedule
   under-firing, not yet fixed) - then user proposed a
   *different*, strategy-level idea on top of that infra fix:
   at the 14:45 cutoff, let a profitable position ride
   (trailing Stop-Loss) until 5 min before close instead of
   force-closing it, but still force-close a losing one at
   14:45 and skip new entries the rest of that day. Backtested
   rather than assumed - added intraday_squareoff_time (+
   squareoff_trailing_atr_mult, block_reentry_after_loss_
   squareoff) to strategy/multi_timeframe_backtest.py. Result:
   NOT a real improvement over what's already known - Net PnL
   landed within ~Rs 12 of the existing best trailing-stop and
   ADX>25 results, and the "no re-entry after a loss" rule had
   *zero* measurable effect (a trade surviving to 14:45 while
   still in loss essentially never happens - Alignment Broke/
   Stop Loss already close real losers earlier). See
   PROJECT_STATUS.md Known Issues for the full breakdown. Not
   adopted, but the feature stays in the backtest module in
   case a different combination is worth trying later. Full
   test suite (126 tests) still passes.

--------------------------------------------------

Bugs Fixed (Part 3)

(None - see the intraday square-off finding above, a tested-
and-not-adopted strategy idea rather than a bug.)

--------------------------------------------------

Next Session (Part 2/3 additions)

6. DONE this session: fixed the recurring debug-keystore
   signing mismatch (mobile_app/android/app/debug.keystore +
   build.gradle.kts).

7. DONE this session: updated the Android App milestone
   description in PROJECT_STATUS.md.

8. USER TO DO (carried over from Part 1): add the third
   cron-job.org trigger for best_trade_squareoff.yml - see
   Part 1's "PERMANENT FIX" for the exact setup. Steps were
   given to the user this session; not yet confirmed done.

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
