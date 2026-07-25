# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260725-001

--------------------------------------------------

Date

25-Jul-2026

--------------------------------------------------

Version

v0.0.12 -> v0.0.13

==================================================

Today's Achievements

✅ MULTI-SESSION RECONCILIATION: this session's own
   local state had gone stale - it last synced with main
   on 21-Jul (right after the MultiIndex crash fix and
   the two-layer git-race fix), then kept working from
   that snapshot through a "start the FCM feature now"
   request without re-fetching first. Before pushing the
   FCM commit, a routine `git log HEAD..origin/main`
   check surfaced ~400 commits this session hadn't seen -
   including real trading automation across 22/23/24-Jul
   and a second parallel session's own reconciliation
   work on 21-Jul evening (which had already reviewed
   *this* session's morning fixes, found and fixed a
   second git-push race on paper_trade.yml, removed the
   native GitHub `schedule:` triggers as the real root
   cause of the races, and reviewed + deleted the
   claude/repo-access-61bplm branch after flagging a real
   design conflict with the user). Stopped, read all of
   doc/21jul26_SESSION_LOG.md (including the other
   session's appended part 2), doc/22jul26_SESSION_LOG.md,
   doc/23jul26_SESSION_LOG.md, doc/24jul26_SESSION_LOG.md,
   and the full current PROJECT_STATUS.md before writing
   or pushing anything else, per this repo's own CLAUDE.md
   session-continuity rule ("if you discover another
   session's commits already merged into main mid-session,
   say so explicitly and reconcile").

✅ Confirmed no actual conflict with the FCM work in
   progress: every intervening session's "Next Session"
   list still carried the FCM feature as "paused 21-Jul,
   not started" all the way through 24-Jul, and
   report/notifier.py / report/push_notifier.py did not
   exist anywhere in that history - safe to add as new
   files. The two workflow files this session had already
   edited (best_trade_entry_scan.yml, paper_trade.yml)
   had been further edited by the other 21-Jul session
   (native `schedule:` trigger removed, pull-rebase added
   to paper_trade.yml) - re-verified after the cherry-pick
   that both changes coexist correctly (no reintroduced
   `schedule:` trigger, retry logic intact, new
   FIREBASE_SERVICE_ACCOUNT env var present) before
   pushing to main.

✅ FCM push-notification feature - code complete (see
   PROJECT_STATUS.md Priority 1 for the full breakdown):
   - report/push_notifier.py - sends to the
     "trade_alerts" FCM topic via firebase-admin, lazily
     initialized from the FIREBASE_SERVICE_ACCOUNT env
     var, never raises (graceful skip if unconfigured,
     same philosophy as Option Chain Engine's NSE-403
     handling).
   - report/notifier.py - thin wrapper firing both
     Telegram and the new push channel from one call;
     replaced all six send_telegram_message() call sites
     (daily_best_trade.py x2, square_off_best_trade.py,
     watchlist_paper_trade.py, paper_trade.py,
     pre_market_report.py, watchlist_scan.py) with
     notify().
   - Flutter: firebase_core + firebase_messaging added,
     app subscribes to the trade_alerts topic and
     requests notification permission on startup
     (topic-based, so no per-device token management is
     needed server-side); google-services Gradle plugin
     wired into both android/settings.gradle.kts and
     android/app/build.gradle.kts;
     POST_NOTIFICATIONS permission added to
     AndroidManifest.xml for Android 13+.
   - FIREBASE_SERVICE_ACCOUNT wired into all four
     trading workflows (Entry Scan, Square-Off, Watchlist
     Paper Trade, Pre-Market Report) alongside the
     existing Telegram secrets.
   - Verified safe before pushing: py_compile on every
     touched Python file, a stubbed-feedparser import
     check exercising the full daily_best_trade.py ->
     refresh_shortlist.py -> notify import chain, a bare
     notify() call confirming both channels skip
     gracefully with neither secret set, and the full
     pytest suite (99 passing, 2 pre-existing sandbox-only
     skips unrelated to this change - feedparser's
     sgmllib3k dependency won't build in this dev sandbox).
   - Still blocked on the user for the two Firebase
     credential files before this goes live - see
     PROJECT_STATUS.md Priority 1.

==================================================

Bugs Fixed

(None - today's Python/workflow changes are additive
[new notification channel], not fixes. See Multi-Session
Reconciliation above for what this session verified
rather than broke.)

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

S20260725-002

--------------------------------------------------

Today's Achievements (Part 2)

✅ MULTI-DEVICE SESSION CONTINUITY: user works on this
   repo from more than one local copy - an older clone at
   D:\Desktop\TURION_AI_Trader (git ownership not yet
   trusted, no GitHub remote auth configured) and a fresh
   copy at D:\TURION_AI_Trader. Verified both against
   origin/main per this repo's CLAUDE.md rule before doing
   anything else: found local main was 16 commits behind
   origin/main (the Part-1 session's FCM work + Android
   APK workflow + trade-detail UI + several [skip ci]
   portfolio updates) with no conflicts against this
   session's own pending uncommitted work, fast-forward
   pulled cleanly. Also swept every claude/* remote branch
   (doc-directory-madhil-sarva-lqg5lj,
   tula-repocha-actress-hob5j0, tula-github-access-y1hlub)
   - all three are stale/empty, nothing unmerged to
   reconcile.

✅ First-time local dev environment setup on the user's
   actual Windows machine (not this dev sandbox): Git for
   Windows was not installed at all - installed it
   (defaults throughout, Git Credential Manager as the
   credential helper), then authenticated GitHub push
   access via GCM's browser-based OAuth flow (device had
   no cached credential before this). Confirmed both read
   and write access working (git pull, git push, and the
   GitHub REST API via the same cached GCM token for
   Actions calls below).

✅ FCM push notification - LIVE AND VERIFIED END-TO-END,
   first real confirmation since the feature went
   code-complete in Part 1. Built the Android APK via the
   build_android_apk.yml GitHub Actions workflow (avoids
   needing Flutter SDK installed locally - none was
   found), downloaded the artifact via the GitHub REST API
   using the cached GCM token, and installed it on the
   user's phone (Motorola Edge 20 Fusion) via adb.
   Non-trivial along the way:
   - adb wasn't installed either - downloaded Android
     platform-tools directly from Google (no full Android
     Studio needed just for adb).
   - Phone wasn't detected by Windows at all at first
     (not a driver/mode issue - literally no new USB
     device enumerated on replug). Root cause was USB
     debugging's per-computer authorization never having
     been granted - toggling USB debugging off/on plus
     "Revoke USB debugging authorizations" forced Android
     to re-show the RSA-fingerprint "Allow USB debugging?"
     prompt, after which adb devices listed the phone
     immediately.
   - Install failed with a raw
     "Requested internal only, but not enough space"
     installer exception - phone was at 100% storage
     (469 MB free, then still only 472 MB after a first
     round of cleanup). Needed a second, more aggressive
     cleanup (clear all app caches + delete old WhatsApp
     media) to get to ~994 MB free before install would
     proceed - confirms the "few hundred MB is not enough"
     lesson from the storage issue logged in Part 1's
     Known Issues.
   - Install then failed with
     INSTALL_FAILED_UPDATE_INCOMPATIBLE (existing
     com.turion.turion_ai_trader signed with a different
     key than this GitHub Actions build). Uninstalled the
     old copy first, then the new APK installed cleanly.
   - Verified live: manually triggered
     pre_market_report.yml (workflow_dispatch, always
     calls notify() once regardless of trade signals) via
     the GitHub REST API, watched the run reach
     conclusion=success, and the user confirmed the push
     notification actually arrived on the phone. Telegram
     delivery unaffected (same notify() call).
   Net effect: Priority 1 (FCM) in PROJECT_STATUS.md moves
   from "code-complete, blocked on user" to "live and
   confirmed working" - see there for the updated status.

--------------------------------------------------

Bugs Fixed (Part 2)

(None - see the adb/storage/signature troubleshooting
above, all environment setup rather than repo bugs.)

--------------------------------------------------

Known local-only state (not yet committed)

D:\TURION_AI_Trader has an uncommitted, in-progress
change: strategy/multi_timeframe_backtest.py gained an
optional require_adx_above parameter (15m-trend ADX
filter, indicators/adx.py, new file) to test filtering out
weak/choppy conditions on the trailing-stop intraday
candidate from Part 1/24-Jul. Not evaluated or committed
yet this session - next session should either finish
evaluating it (per Priority 3 below) or explicitly decide
to discard it, rather than letting it sit uncommitted
indefinitely.

==================================================

PART 3 (same day, continued)

✅ First-time local Python setup on the user's actual
   Windows machine too (Python 3.14.6, installed from an
   installer already sitting in D:\download from an
   earlier, unrelated download) - needed to actually run
   and verify new code locally instead of only reasoning
   about it. Full test suite: 126 passed, no regressions.

✅ Built indicators/supertrend.py and indicators/cpr.py
   (the two "not yet built" items carried over from every
   prior session's Next Session list) - pure calculation
   engines, unit-tested (6 new tests), not yet used by any
   strategy. Supertrend reuses the existing ATR engine
   rather than recomputing True Range.

✅ Backtested them together (strategy/
   supertrend_cpr_backtest.py, analysis-only, same pattern
   as every other *_backtest.py in this repo) on NIFTY and
   BANKNIFTY - CONCLUSIVELY REJECTED, see
   PROJECT_STATUS.md Known Issues for the full 12-combo
   sweep result. Indicators themselves stay in the
   codebase as reusable building blocks even though this
   particular combination didn't work out.

✅ Finished evaluating the ADX filter carried over
   uncommitted from 24-Jul (strategy/
   multi_timeframe_backtest.py's require_adx_above,
   indicators/adx.py) - swept 5 thresholds on top of the
   best-known combo (Daily-aligned NIFTY, 0.5x SL, 1.0x
   ATR trail). Net loss shrank from -Rs 450.95 (no filter)
   to -Rs 99.33 at ADX>25 - the best single result found
   all week, though from only 6 trades (small-sample
   caveat noted in PROJECT_STATUS.md). Kept and committed
   rather than discarded, given the clear directional
   improvement.

✅ Backtested Gap-fill (strategy/gap_fill_backtest.py,
   analysis-only) - the one item on the strategy list
   marked "explicitly not pursued" rather than actually
   tested. First genuinely net-positive intraday result
   found in this project: NIFTY at 0.5% gap threshold /
   1.0x ATR SL gave +Rs 413.45 net over 60d (20 trades,
   45.0% win rate); RELIANCE also positive (+Rs 82.04) at
   the same params; BANKNIFTY and 5 other stocks stayed
   net-negative - a NIFTY-specific edge, not a general one.
   See PROJECT_STATUS.md Known Issues for the full
   threshold/SL sweep. Flagged as PROMISING, not tradeable
   yet (one 60-day test window is not enough to trust on
   its own) - not wired into any paper trading.

==================================================

Next Session

1. FCM is now live - no longer blocked. Monitor a few real
   trade alerts over the next few trading days to confirm
   push notifications keep arriving reliably alongside
   Telegram, not just this one manual test.

2. Let the scheduled review (26-Jul 09:00 IST) run as
   planned - review real Daily-strategy + Best Trade
   Engine results (both producing real data reliably
   since 21-Jul).

3. Finish or discard the uncommitted ADX-filter experiment
   in strategy/multi_timeframe_backtest.py /
   indicators/adx.py (see "Known local-only state" above)
   before starting anything else in that file, to avoid a
   third session finding it in a half-done state. If
   pursuing the intraday candidate further generally:
   sweep more trailing-stop distances/initial SL combos
   and BANKNIFTY Momentum+VIX (carried over from 24-Jul).

4. Apply strategy/transaction_costs.py's real cost model
   to the Watchlist and Best Trade Engine's own live
   evaluations, not just the analysis-only intraday
   backtests (carried over from 23-Jul).

5. Commit Desktop App (PySide6), package as .exe (carried
   over).

6. Fix TATAMOTORS / LTIM ticker symbols (carried over).

7. Supertrend and CPR indicators - built and backtested
   this session (Part 3), REJECTED as a standalone
   intraday entry. No longer an open item; the indicators
   remain available if a different combination is proposed
   later.

==================================================

END OF SESSION
