# TURION AI Trader

PROJECT STATUS

==================================================

Project

TURION AI Trader

--------------------------------------------------

Version

v0.0.15

--------------------------------------------------

Build Status

🟢 Stable

--------------------------------------------------

Project Started

01-Jul-2026

--------------------------------------------------

Last Updated

06-Aug-2026

--------------------------------------------------

Current Phase

Phase 2

Trading & AI Intelligence

==================================================

PROJECT PROGRESS

Overall Progress

🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜

79%

--------------------------------------------------

Foundation

██████████

100%

Status

🟢 Stable

--------------------------------------------------

Market Intelligence

██████████

100%

Status

🟢 Stable

--------------------------------------------------

Trading Intelligence

█████████░

90%

Status

🟢 Paper Trading Live (automated) + Option Chain / Options
   Decision Engine added

--------------------------------------------------

AI Intelligence

███████░░░

70%

Status

🟡 Weighted scoring + News sentiment + cross-symbol
   Best Trade ranking done, ML pending

==================================================

PROJECT MILESTONES

✅ Professional Folder Structure

✅ Live NIFTY Data Download

✅ Live Market Chart

✅ EMA Engine

✅ RSI Engine

✅ Market State Engine v1

✅ Reasoning Engine v1

✅ Market Structure Engine v1

✅ Data Validation Engine v1

✅ Report Engine v1

✅ Excel Database Engine v1

✅ Professional Excel Dashboard

✅ Support & Resistance Engine

✅ Candlestick Engine

✅ Volume Engine

✅ ATR Engine

✅ Option Chain Engine        (PCR/Max Pain/OI - real data
                               needs a non-blocked network,
                               degrades gracefully on NSE 403)

✅ AI Decision Engine         (weighted scoring)

✅ Paper Trading              (multi-symbol, automated)

✅ Backtesting

✅ News Engine                (RSS sentiment, free feeds)

✅ Options Decision Engine    (CE/PE, kept separate from
                               equity signal/paper-trading logic)

✅ Best Trade Engine          (ranks stocks + index options +
                               news into one daily locked pick)

⬜ Broker Integration         (broker not selected)

🟡 Desktop Dashboard          (PySide6 built + verified, not committed)

✅ Android App                (Flutter, 5 tabs - Portfolio/Intraday/
                               Swing/News/History (renamed 29-Jul from
                               Best trade/Watchlist for clarity) -
                               committed and merged to main 19-Jul,
                               installed on phone via adb, reads GitHub
                               raw JSON, refreshed every 15 min by
                               GitHub Actions. UPDATE 29-Jul: Portfolio
                               and History now show both Swing and
                               Intraday portfolios (previously
                               Intraday's closed trades were invisible
                               in the app); added a tap-to-open
                               candlestick chart per position/trade with
                               Entry/Stop Loss/Target/Exit overlays
                               (reports/candles.json, refreshed
                               ~15-min by paper_trade.yml).

⬜ Algorithmic Trading        (needs broker)

⬜ TURION AI Trader v1.0

--------------------------------------------------

Progress: 24 / 29 milestones done (~83%), 1 more in-progress
(Desktop App working locally, pending commit)

==================================================

EXTRA FEATURES (beyond original milestone list)

✅ Signal Filters (Structure + S/R + Volume +
   Candlestick combined)

✅ Telegram Notifications

✅ Multi-Symbol Watchlist Scanner
   (NIFTY 50 + Bank Nifty + 50 companies)

✅ GitHub Actions Automation (24/7, no laptop)

✅ Pre-Market Report (08:45 IST daily)

✅ Windows Encoding Fix + requirements.txt

✅ Unit Test Suite (45 pytest tests - signal_engine,
   ai_decision_engine, paper_trading, backtest_engine,
   risk_engine - all pure logic, ~3.5s, no network)

✅ Telegram delivery confirmation logging
   (PR #1, separate session)

✅ Paper-trade cron reliability fix
   (:07/:22/:37/:52 offset avoids GitHub Actions
   top-of-hour scheduling load - PR #1)

✅ News Engine (free RSS - Moneycontrol +
   Economic Times, keyword sentiment scoring)

✅ Option Chain Engine (PCR, Max Pain, OI
   Call/Put Writing, IV - degrades gracefully
   when NSE blocks the network instead of
   crashing the pipeline)

✅ Options Decision Engine (BUY CE / BUY PE,
   kept fully separate from equity signal logic)

✅ Best Trade Engine + refresh_shortlist.py
   (every 30 min, wide daily-interval scan) +
   daily_best_trade.py (every ~5 min, live
   15m/5m/1m alignment check) - ranks Nifty 50
   stocks + NIFTY/BANKNIFTY options + news
   sentiment on one scale and locks the single
   highest-probability intraday pick, with a
   top-5 shortlist as backup context.
   Recommendation only - same "Claude never
   executes a real trade" rule applies.

✅ Multi-Timeframe Engine - 15-minute candles
   set the trend, 5-minute candles are the
   entry decision, 1-minute candles confirm
   timing; a trade only fires when all three
   agree. Replaced an earlier "check every 30
   min" design after the user asked for
   something closer to live/continuous checking.

✅ Best Trade Paper Trading - if the locked
   pick is an equity trade, it opens a real
   intraday paper position (own portfolio file,
   separate from the swing-style watchlist
   paper trading) between 10:00 IST and 14:15
   IST, gets its Stop Loss/Target checked every
   ~5 min all day (not just once at the end),
   and force-closes by 14:45 IST via
   square_off_best_trade.py + a third GitHub
   Actions workflow, so it never silently
   carries over like a swing trade. Index option
   picks stay recommendation-only (no live
   premium feed to mark P&L against).

✅ Multi-Timeframe Backtest Tool (mtf_backtest.py,
   19-Jul) - backtests the 15m(trend)/5m(entry)
   alignment core of the Multi-Timeframe Engine.
   Analysis only, never wired into paper trading -
   the user explicitly wants 15m kept to context/
   analysis, with 5m+ as the only timeframe that
   can actually open a trade. See Known Issues for
   what the sweep found.

✅ Confidence-Based Position Sizing + Portfolio
   Risk Cap (19-Jul, strategy/paper_trading.py) -
   the Daily-timeframe watchlist strategy (the one
   proven profitable in backtest) now sizes new
   entries by risking 1-2% of current equity,
   scaled by how far above the AI Decision Engine's
   60% threshold the confidence is (60% -> half
   risk, 100% -> full risk; always >=1 share so a
   signal is never skipped for being expensive).
   MAX_CONCURRENT_POSITIONS (15) blocks new entries
   once the portfolio is already at capacity.
   Backward compatible - the 14 positions already
   open keep whatever quantity they were opened
   with; only new entries going forward use the
   new sizing.

✅ Alignment History Log (29-Jul, daily_best_trade.py's
   append_alignment_history) - researched after the user
   asked why a specific candle/symbol (TATASTEEL) didn't
   trigger a trade and there was no way to check, since
   reports/best_trade_pick.json only ever holds the latest
   check. The entry-scan run now appends one line to
   reports/alignment_history.jsonl with every shortlisted
   symbol's full 15m/5m/1m Aligned/Reason/Bias/Decision/
   Confidence - not just the aligned ones that made it into
   that run's ranking. Rolling 7-day retention (pruned on
   every write that happens) so the working file doesn't
   grow unbounded. Answers "why didn't X trade at time Y"
   after the fact instead of only in the moment.
   THROTTLED same day: the workflow itself still runs every
   ~1 min, but every run is a permanent git commit regardless
   of the file-size pruning above - so writes are now capped
   to once per 5 min (ALIGNMENT_HISTORY_THROTTLE_MINUTES),
   cutting the git-history growth rate ~5x. The shortlist
   itself only refreshes every 30 min anyway, so 5-min
   granularity loses little for the "why didn't X trade"
   use case this exists for. Raised and fixed the same
   session, before this ever ran for real - the user asked
   "won't this fill up GitHub storage?" and was right to.

==================================================

CURRENT ARCHITECTURE

Live Market Data (yfinance)

↓

Data Validation Engine

↓

Indicator Engines
(EMA + RSI + ATR + Volume)

↓

Market State / Structure / Support-Resistance /
Candlestick Engines

↓

Signal Engine (with Filters)
+ AI Decision Engine (weighted score)

↓

Paper Trading Engine (multi-symbol)

↓

Report Engine → Console / Excel Dashboard /
Telegram / Desktop App

Separate daily path (options are never mixed
into the equity path above):

refresh_shortlist.py (every 30 min): Watchlist
Scan (stocks + indices) + News Engine (RSS
sentiment) + Option Chain Engine → Options
Decision Engine (NIFTY / BANKNIFTY CE / PE)
→ reports/best_trade_shortlist.json

↓

daily_best_trade.py (every ~5 min): reads the
shortlist, checks 15m/5m/1m alignment per
candidate (Multi-Timeframe Engine) + monitors
any open position's Stop Loss/Target live

↓

Best Trade Engine (ranks everything, locks
one pick + top-5 shortlist)

↓

Report Engine → Console / Excel ("Best Trade"
sheet) / Telegram

==================================================

AUTOMATION (GitHub Actions - runs in cloud)

• Pre-Market Report      → 08:45 IST, Mon-Fri

• Watchlist Paper Trade  → every 15 min (offset
                           :07/:22/:37/:52),
                           08:37-16:22 IST, Mon-Fri.
                           UPDATE 21-Jul: native GitHub
                           `schedule:` trigger removed
                           (was under-firing to ~4x/day) -
                           now triggered externally by
                           cron-job.org hitting
                           workflow_dispatch. Verified
                           landing at the intended cadence
                           (35 runs on 21-Jul).

• Best Trade Shortlist    → every 30 min + one pre-market
                           run at 08:45 IST, Mon-Fri
                           (refresh_shortlist.py) - wide
                           daily-interval scan + news +
                           option chain, written to
                           reports/best_trade_shortlist.json

• Best Trade Entry Scan   → every ~5 min, ~09:20-14:45 IST,
                           Mon-Fri (daily_best_trade.py) -
                           checks shortlist candidates'
                           15m/5m/1m alignment; only opens
                           a position between 10:00 IST
                           (ENTRY_START) and 14:15 IST
                           (LAST_ENTRY_CUTOFF); monitors any
                           open position's Stop Loss/Target
                           every run regardless of time.
                           UPDATE 21-Jul: native GitHub
                           `schedule:` trigger removed (was
                           under-firing to ~3x/day) - now
                           triggered externally by
                           cron-job.org every 1 min (widened
                           from the original 5-min plan).
                           Verified landing at the intended
                           cadence (100+ runs on 21-Jul).

• Best Trade Square-Off   → 14:45 IST, Mon-Fri (45 min
                           before NSE's 15:30 close)
                           (square_off_best_trade.py).
                           BROKEN 29-Jul, FIXED same day: was
                           still on GitHub's native `schedule:`
                           trigger, never migrated to
                           cron-job.org like the other two - see
                           Known Issues for the full history. A
                           third cron-job.org job ("Best Trade
                           Square-Off Trigger") now POSTs to
                           this workflow's workflow_dispatch
                           every 5 min, 14:40-15:15 IST
                           (`10,15,20,25,30,35,40,45 9 * * 1-5`
                           UTC) Mon-Fri - a safety window around
                           14:45 rather than the 1-min/15-min
                           cadence the other two need, since
                           this only ever needs to fire reliably
                           once, not frequently. Verified
                           working via a manual test run (204,
                           then a real workflow_dispatch run
                           completed successfully). Not yet
                           confirmed at the real 14:45 IST
                           cadence on a live trading day - first
                           real firing will be the actual test.

• Portfolio state auto-committed back to repo

• All alerts delivered to Telegram (now logs
  success/failure in the Action run output).
  UPDATE 25-Jul: report/notifier.py now also fires a
  Firebase Cloud Messaging push notification to the
  TURION AI Trader app alongside every Telegram alert
  (topic-based - "trade_alerts" - no per-device token
  tracking needed). LIVE AND VERIFIED 25-Jul (same day,
  second session): google-services.json committed,
  FIREBASE_SERVICE_ACCOUNT GitHub secret set, new APK
  built via the build_android_apk.yml GitHub Actions
  workflow and installed on the user's phone via adb,
  then confirmed end-to-end by manually triggering
  pre_market_report.yml and having the user confirm the
  push notification actually arrived. Telegram is
  unaffected either way.

• CONFIRMED WORKING 13-Jul: both workflows fired
  automatically on schedule and opened 7 real paper
  positions (HDFCBANK, ICICIBANK, BAJFINANCE,
  SUNPHARMA, TITAN, BAJAJ-AUTO, TECHM)

• CONFIRMED WORKING 17-Jul: all three Best Trade
  workflows manually triggered on the real GitHub
  Actions runner (via workflow_dispatch, ahead of
  their first real scheduled firing) - Shortlist
  Refresh succeeded first try (6 stock candidates,
  2 option candidates, both News Engine and Option
  Chain Engine reachable with no fetch errors).
  Entry Scan and Square-Off both failed their first
  try on an unrelated bug (see Known Issues → fixed),
  then succeeded once re-triggered after the fix.

• FIRST REAL BEST TRADE ENGINE OUTCOMES, 21-Jul: after
  the price-fetch crash fix (see Known Issues), the
  engine produced its first two real results the same
  day - ULTRACEMCO closed on Stop Loss (Entry
  ₹12,105.00, Exit ₹12,042.54, PnL -₹62.46), then
  ICICIBANK opened as a fresh position (Entry
  ₹1,464.10, SL ₹1,461.12, Target ₹1,470.07). Zero
  real outcomes from 17-Jul to 21-Jul were caused by
  the crash, not by the strategy never finding an
  aligned candidate.

==================================================

KNOWN ISSUES

• FIXED 17-Jul: Best Trade Entry Scan and Square-Off
  workflows crashed (`git add reports/
  best_trade_portfolio.json` failing with "pathspec
  did not match any files") on a repo where that file
  had never been created yet - only discovered by
  manually triggering the workflows instead of
  waiting for Monday. Fixed with `git add <file> ||
  true` in all three Best Trade workflows.

• RESOLVED 17-Jul (was: unconfirmed whether GitHub
  Actions can reach NSE/RSS): confirmed via the manual
  trigger above - both the Option Chain Engine and
  News Engine fetched successfully from the real
  GitHub Actions runner, no "Available: False" or
  "Headlines fetched: 0" in the log. This dev
  sandbox's proxy blocking those same domains during
  earlier local testing was a sandbox-only artifact.
  Still worth re-checking over a few real trading
  days since NSE's IP blocking isn't perfectly
  consistent.

• TATAMOTORS.NS / LTIM.NS - no Yahoo data
  ("Quote not found" / delisted, reconfirmed on the
  real GitHub Actions run 17-Jul), need correct
  symbols.

• 15m strategy CONFIRMED weak, 19-Jul: exhaustive
  15-combo SL/Target sweep on NIFTY (fixed % - same
  method as the profitable Daily-timeframe tuning)
  was net-negative in every single case, best only
  -259.67 PnL. Tuning parameters cannot fix this -
  the entry signal itself has no edge on 15m alone.
  15m must only be used as trend context, never as
  a standalone signal (see mtf_backtest.py below).

• Multi-Timeframe (15m/5m) alignment core also
  tested standalone, 19-Jul: fixed %-based SL/Target
  net-negative; best ATR-based combo (0.5x SL / 1.5x
  Target) was roughly break-even (+4.00 PnL, 72
  trades, 34.7% win rate) on NIFTY - no real edge
  once real-world costs are considered. Conclusion:
  do NOT drop the live Best Trade Engine's 1m
  confirmation requirement - there is no backtest
  evidence that would help, and 1m only ever narrows
  candidates (adds selectivity), never creates false
  positives on its own.

• IMPROVED (not yet profitable) 23-Jul: added an
  optional Daily-timeframe alignment requirement to the
  15m/5m backtest (strategy/multi_timeframe_backtest.py,
  require_daily_alignment=True) - also require the Daily
  candle's Bias to agree, at the user's suggestion since
  Daily is the one timeframe with a proven edge. Tested
  on the same best-known combo (0.5x SL/1.5x Target,
  NIFTY, 60d): trades dropped 67->20, win rate improved
  35.82%->45.0%, max drawdown dropped 118.21->43.29, and
  the net-of-transaction-cost loss shrank roughly 4x
  (-Rs 1,950 -> -Rs 547 at a flat Rs 30/trade guess).
  Still net-negative, so not tradeable yet, but a real,
  measurable improvement - unlike Candlestick confirmation
  (tested earlier the same day), which hurt every strategy
  it was added to. Worth pursuing further: try Daily-
  alignment on more SL/Target combos, or combine it with
  the BANKNIFTY Momentum+VIX options finding.
  CORRECTED 23-Jul (real % cost model, see below):
  re-checked with strategy/transaction_costs.py instead of
  the flat guess - real cost was Rs 514.12 for these 20
  trades (an index-level "1 unit" position is worth
  ~Rs 24,000+, so % cost lands close to the earlier flat
  guess here, unlike the cheap-stock cases below) - Net
  PnL -Rs 460.73, similar conclusion (not yet profitable,
  but a real improvement over the no-Daily-filter case).

  EXTENDED 24-Jul: added an optional trailing Stop-Loss
  (use_trailing_stop=True, strategy/multi_timeframe_
  backtest.py) that replaces the fixed Target - ratchets
  the Stop-Loss up as the trade makes new highs, letting a
  strong trend run further instead of capping out at a
  fixed ATR-multiple Target. Tested three trail distances
  on the same Daily-aligned NIFTY combo (0.5x initial SL):
  - Trail = 0.5x ATR (same as initial SL): HURT results -
    all 24 trades whipsawed out via the trail, gross PnL
    flipped negative (-Rs 20.37).
  - Trail = 1.0x ATR: BEST result found all week - gross
    +Rs 62.58 (beats the fixed-target's +Rs 42.03), net
    -Rs 450.95 (least negative net PnL of any NIFTY combo
    tested this week, better than the fixed-target's
    -Rs 460.73 too).
  - Trail = 1.5x ATR: worse than 1.0x (+Rs 43.19 gross,
    -Rs 470.33 net) - gives back too much profit before
    exiting.
  Lesson: trail distance needs its own tuning, independent
  of the initial Stop-Loss distance - too tight whipsaws
  out of real trends, too wide gives back too much of the
  peak. Still net-negative after real transaction costs,
  so not tradeable yet, but the best NIFTY intraday result
  found to date. Worth sweeping more trail-distance values
  and combining with other SL/Target starting points next.

  FURTHER EXTENDED 25-Jul: added an optional ADX filter
  (require_adx_above, strategy/multi_timeframe_backtest.py
  + new indicators/adx.py) requiring the 15m trend
  timeframe's ADX above a threshold before entering -
  filters out weak/choppy conditions, the kind that
  whipsawed the 1.0x-ATR trailing stop above. Swept 5
  thresholds (no filter, 15, 20, 25, 30) on the same best-
  known combo (Daily-aligned NIFTY, 0.5x initial SL, 1.0x
  ATR trail): net loss shrank monotonically as the
  threshold rose - -Rs 450.95 (no filter, 20 trades) ->
  -Rs 428.10 (ADX>15) -> -Rs 243.94 (ADX>20) -> -Rs 99.33
  (ADX>25, best found to date, 78% less negative than no
  filter) -> -Rs 107.07 (ADX>30, worse than 25 - too
  restrictive). Win rate rose alongside it, 45.0% (no
  filter) to 83.33% (ADX>25). Still net-negative, so not
  tradeable yet, but the clearest single improvement found
  this week. CAVEAT: ADX>25's result comes from only 6
  trades - too small a sample to trust on its own; treat
  as a promising direction needing a longer test window,
  not a confirmed edge.

  TESTED 29-Jul: a profit-aware intraday square-off rule,
  researched after the user asked why Best Trade Engine
  positions weren't closing on time (that turned out to be
  an infrastructure bug - see Known Issues below - but the
  strategy question underneath was worth testing separately).
  New intraday_squareoff_time parameter: at 14:45 IST, a
  position in profit switches to a trailing Stop-Loss for the
  rest of the day (protects the gain, lets it run) instead of
  a hard close; a position in loss/flat closes immediately and
  (optionally) blocks new entries for the rest of that day.
  Result: NOT a real improvement. Net PnL (-Rs 438.29, 19
  trades) landed within noise of the already-known trailing-
  stop result (-Rs 450.95) and the ADX>25 combo (-Rs 99.07 vs
  -Rs 99.33 previously) - a ~Rs 12 difference either way.
  Blocking re-entry after a loss-at-cutoff had *zero* effect
  (identical trades, identical PnL) because a trade surviving
  to 14:45 while still in loss essentially never happened in
  this data - Alignment Broke / Stop Loss had already closed
  the real losers well before the cutoff, so the new "protect
  the loser" branch had nothing left to protect against.
  Conclusion: the idea doesn't add value on top of what
  Alignment Broke + the existing trailing stop already do.
  Not adopted.

• PROMISING (not yet tradeable) 30-Jul: India VIX regime
  filter, applied to this file's *equity* entries (first
  August-plan candidate tested - see Priority 2) rather than
  only the BANKNIFTY options case it was originally found for
  (22-Jul). New require_vix_in_band parameter: only enter when
  ^INDIAVIX is inside its own recent rolling percentile band
  (same methodology, backward as-of joined - no look-ahead).
  Tested on the Daily-aligned NIFTY, 0.5x SL combo (no
  trailing stop, no ADX - a clean baseline for this specific
  comparison): baseline 22 trades, 31.82% win rate, -Rs
  614.57 net. VIX 20-80 percentile band: 11 trades, -Rs
  312.82 (49% less negative). VIX 10-90 (wider): 14 trades,
  -Rs 395.59 (weaker, as expected from a looser filter). VIX
  30-70 (tight, matching the original BANKNIFTY band exactly):
  6 trades, 50.0% win rate, -Rs 115.37 - an 81% reduction from
  baseline, and landing within noise of the ADX>25 result
  above (-Rs 99.33, also 6 trades) - two independently-found
  filters converging on a similar magnitude of improvement is
  a mildly reassuring signal, not just one cherry-picked
  result. Stacking both filters together (VIX 20-80 + ADX>25)
  over-restricts to a single trade - too small to mean
  anything, don't combine them. Still net-negative and small
  sample (6 trades), same caveat as every other finding this
  week - promising, not confirmed.

• REJECTED 30-Jul: partial profit booking on the proven
  Daily-timeframe strategy (August-plan candidate #4, see
  Priority 2) - book half the position at a nearer 1x-ATR
  target instead of the live strategy's single 3x-ATR
  all-or-nothing Target, trail the other half with a Stop-
  Loss instead of waiting for the full target (see
  strategy/daily_partial_booking_backtest.py, analysis-only,
  same entry signal as the live/proven strategy for a fair
  like-for-like comparison). Tested against the existing
  baseline (strategy/backtest_engine.py's run_backtest,
  1.5x SL/3x Target, unchanged) on NIFTY + 3 stocks, 2y daily:
  worse in 3 of 4 cases - NIFTY -Rs 87.75 -> -Rs 455.84,
  ICICIBANK -Rs 117.45 -> -Rs 173.09, and notably RELIANCE
  (baseline's one actually-profitable case, +Rs 167.16) cut
  to +Rs 86.81 - halving the winner's gain. Only HDFCBANK
  improved slightly (-Rs 72.48 -> -Rs 56.91). Win rate rose
  everywhere (the nearer 1x target is easier to hit), but
  that's a vanity metric here, not real profit - the trades
  where the full 3x target would eventually have been reached
  are exactly the trades this costs the most on, since booking
  half early caps the upside from letting a real trend run.
  Root cause is the mirror image of the reasoning behind the
  ADX/VIX filters that *did* help: those cut bad trades before
  they lost money; this cuts good trades before they made
  their real money. Not adopted.

• PROMISING (not yet tradeable) 25-Jul: Gap-fill - bet
  that a significant open-vs-previous-close gap reverts
  back toward the previous close during the day, the
  opposite thesis to Gap-and-Go. Explicitly not pursued
  earlier (see Priority 3's original reasoning below) -
  tested now to check that assumption rather than leave it
  unverified (see strategy/gap_fill_backtest.py, analysis-
  only). Ran on NIFTY, BANKNIFTY, and 6 NIFTY 50 stocks
  (same 6 as the ORB/VWAP sweep) at default params (0.3%
  gap threshold, 1.0x ATR SL), then swept 5 gap thresholds
  x 4 SL multiples on NIFTY specifically:
  - NIFTY: the only clear winner - best combo (0.5% gap
    threshold, 1.0x ATR SL) gave +Rs 413.45 net over 60d
    (20 trades, 45.0% win rate) - the first backtested
    intraday candidate to land net-positive after real
    transaction costs. Several nearby combos (0.3-0.5%
    threshold, 0.5-2.0x SL) also net-positive, not just
    one cherry-picked cell.
  - RELIANCE: also net-positive at the same NIFTY-tuned
    params (+Rs 82.04, 25 trades, 56.0% win rate), though
    weaker.
  - BANKNIFTY: strongly net-negative (-Rs 778.55) even at
    NIFTY's best params - does not generalize.
  - ICICIBANK, HDFCBANK, TCS, BAJFINANCE, TITAN: all
    mildly net-negative at the same params.
  CAVEAT: only 20 trades over a 60-day window for the
  NIFTY result - real, but a small sample from one backtest
  period, the same caveat as every other single-window
  result in this document. Before trusting this as
  tradeable: re-test over a different/longer date range to
  rule out a lucky 60-day window, and only then consider
  paper-trading it live (never wire straight into real
  capital). Not wired into any paper trading yet - this is
  research only, per this repo's rule that engines don't
  make trading decisions and Claude never executes a real
  trade.

  SPLIT-WINDOW CHECK, same day: Yahoo only ever serves the
  trailing ~60 days of 5m data (no way to reach further
  back for a truly independent window), so instead split
  the one available window into two ~4-week halves and ran
  each separately (strategy/gap_fill_backtest.py's new
  start/end parameters) - a same-approach 44 more real
  minutes vs. a check for whether the edge held steady
  across the period, not proof of a longer track record.
  Result: NOT uniform. First half (31-May to 28-Jun) was
  strongly positive (+Rs 290.71, 7 trades, 57.14% win
  rate); second half (28-Jun to 26-Jul, the more recent
  one) was roughly flat (-Rs 18.04, 6 trades, 33.33% win
  rate) - not a strong reversal, but not confirming the
  full-window edge either. Revised read: the full-window
  +Rs 413.45 was concentrated in the earlier half, not
  spread evenly - weakens confidence that this is a stable,
  ongoing edge rather than a stretch that happened to work.
  Still worth tracking (nothing here rules it out), but
  should not be treated as more proven than the ADX-filter
  or BANKNIFTY-options findings above - all three are in
  the same "promising, needs more real days" bucket now.

• Desktop App verified working locally, but not yet
  committed to the repo. (Android App committed
  19-Jul - see milestone above.)

• "App not installed" installing the Android APK via
  WhatsApp self-chat, even after uninstalling the
  previous version - turned out to be
  INSTALL_FAILED_INSUFFICIENT_STORAGE (phone at 99%
  storage), not a signing or transfer-corruption
  issue. `adb install` over USB surfaces the real
  Android installer error instead of the generic
  Play Store dialog - worth reaching for first next
  time this happens instead of guessing.

• NOT YET FIXED, confirmed 3x (25-Jul, 28-Jul, 29-Jul):
  every GitHub Actions build_android_apk.yml run signs the
  APK with a fresh, runner-local debug keystore (nothing
  persists one across runs), so `adb install -r` against
  the previous build always fails with
  INSTALL_FAILED_UPDATE_INCOMPATIBLE ("signatures do not
  match"). Worked around each time by uninstalling the old
  copy first - harmless (app has no local state worth
  keeping, everything lives in the GitHub-hosted JSON) but
  repetitive. Real fix: commit a fixed debug.keystore to
  the repo and point mobile_app/android/app/
  build.gradle.kts at it so every build signs identically
  and `adb install -r` can update in place. Not done yet.

• CONFIRMED 20-Jul: GitHub Actions' free-tier cron
  scheduler badly under-fires the Best Trade Entry
  Scan workflow's every-5-min schedule (`*/5 3-9 * *
  1-5`, meant to fire ~84x during 08:30-15:30 IST
  market hours). Checked via the public GitHub REST
  API (no login needed): only 3 runs actually fired
  all day - 11:47 IST, 3:08 IST, and 5:33 IST (the
  last one outside the configured 3-9 UTC window
  entirely, meaning it was queued for hours before
  running). Only one of those three landed inside the
  10:00-14:15 IST entry window, which is almost
  certainly why the Best Trade Engine has opened zero
  real positions so far - it isn't getting the number
  of chances the design assumes, not a strategy/logic
  problem. This is a known GitHub Actions limitation
  on low-traffic public repos with very frequent
  schedules, not something fixable in our code -
  likely needs an external trigger (e.g. a free
  cron-ping service hitting workflow_dispatch via the
  GitHub API) if reliable 5-min cadence is required
  before pursuing broker integration.

• CONFIRMED 20-Jul: same under-firing pattern on
  Watchlist Paper Trade Check (`paper_trade.yml`,
  cron `7,22,37,52 3-10 * * 1-5` - every 15 min,
  meant to fire ~32x during 08:30-16:00 IST). Checked
  the last 15 runs via the public GitHub REST API:
  every single trading day (15/16/17/20-Jul) got only
  ~4 runs, roughly 2 hours apart, never the intended
  15-min cadence - e.g. 20-Jul: 11:35, 15:13, 17:35
  IST. This is consistent day over day, not a one-off
  delay, so it looks like a hard ceiling GitHub applies
  to this repo's scheduled-workflow frequency
  regardless of the cron granularity requested (5 min
  and 15 min schedules both landed at ~2-hour spacing).
  Effect on Watchlist Paper Trading: Stop-Loss/Target
  hits are still detected correctly (a breached level
  is still a breached level whenever the next run
  checks it), but the recorded Exit Time/Price can lag
  the real intraday move by up to ~2 hours, and
  Last Price/Last Checked on open positions is only as
  fresh as the last run, not truly 15-min-live. Same
  root cause and same possible fix (external trigger)
  as the Best Trade Entry Scan issue above.

• MITIGATED 20-Jul: set up an external trigger via
  cron-job.org (free tier) to work around the GitHub
  Actions cron under-firing above. Two cron-job.org
  jobs POST to GitHub's `workflow_dispatch` REST API
  (both workflows already had `workflow_dispatch:` as
  a trigger, so no workflow YAML changes were needed):
  - "Best Trade Entry Scan Trigger" - every 1 min,
    03-09 UTC, Mon-Fri (`* 3-9 * * 1-5`) - widened from
    the original 5-min plan to maximize the Best Trade
    Engine's chances of catching 15m/5m/1m alignment
    before the 26-Jul review, since it still has zero
    real trade outcomes
  - "Watchlist Paper Trade Trigger" - every 15 min,
    03-10 UTC, Mon-Fri (`7,22,37,52 3-10 * * 1-5`) -
    matches the original intended cadence
  Both verified working via TEST RUN (204 No Content)
  and cross-checked on GitHub's Actions run history
  (workflow_dispatch runs appeared immediately). Auth
  is a fine-grained GitHub PAT scoped to only this repo,
  Actions: Read and write, Metadata: Read-only, stored
  only in cron-job.org's own header field. Native
  GitHub `schedule:` triggers were initially left in
  place as "harmless redundancy" - UPDATE 21-Jul: this
  was wrong, it was the actual source of the git-push
  races documented below (two near-simultaneous runs
  both committing). Removed the native `schedule:`
  trigger from both workflows entirely once confirmed -
  cron-job.org's workflow_dispatch is now each
  workflow's only trigger. Effective starting 21-Jul.

• A separate Claude session (branch
  claude/tula-repocha-actress-hob5j0) fixed the
  Telegram/cron issue in parallel - merged as PR #1.
  Watch for multiple sessions editing the same repo
  at once going forward.

• FIXED 21-Jul: daily_best_trade.py and
  square_off_best_trade.py crashed
  (`TypeError: float() argument must be a string or a
  real number, not 'Series'`) on every single run once
  a real Best Trade position existed, because
  yfinance's yf.download() now returns MultiIndex
  columns even for a single-symbol request. This left
  the very first real Best Trade position (ULTRACEMCO)
  completely unmonitored for Stop Loss/Target from
  ~10:01 IST until caught and fixed the same day -
  every cron-job.org-triggered run in between failed,
  which is what the user actually noticed first (the
  failure emails). Fixed by flattening the Close
  column before calling float() on it, same pattern
  strategy/watchlist_scanner.py already used for a
  different MultiIndex case. Pushed straight to main
  (not a feature branch) given a real position was
  unmonitored. See doc/21jul26_SESSION_LOG.md for the
  full investigation.

• FIXED 21-Jul: cron-job.org's 1-minute cadence on the
  Best Trade Entry Scan trigger caused two kinds of git
  push races between overlapping workflow runs - both
  looked like job failures (more false-alarm emails)
  but never actually lost committed data:
  (1) simple fast-forward rejection, whichever run
  pushed second - fixed with a push-retry loop (pull
  --rebase + push, up to 3x) in all three Best Trade
  workflows;
  (2) genuine content conflicts, when two overlapping
  runs both made a real, conflicting decision (e.g.
  both tried to open a position independently) - a
  plain rebase retry can't auto-merge that, so fixed
  more deeply: on a push rejection the workflow now
  discards its own local write, hard-resets to whatever
  actually landed on origin, and re-runs the same
  Python script against that real state (safe because
  all three scripts already reload state from disk and
  only act/notify on genuine changes - no duplicate
  Telegram pings). Both fixes pushed to main.

• DONE 25-Jul (started 21-Jul, code-complete same day,
  fully live 25-Jul): Best Trade / Watchlist trade alerts
  now also fire as a real push notification inside the
  TURION AI Trader Android app (Firebase Cloud Messaging,
  topic-based - "trade_alerts" - no per-device token
  management), alongside Telegram (unchanged). Backend
  verified live via a manual workflow run (both channels
  sent successfully). Along the way, found and fixed a
  real bug in report/push_notifier.py: a malformed
  FIREBASE_SERVICE_ACCOUNT secret raised uncaught instead
  of degrading gracefully, which would have skipped the
  "commit portfolio state" step on all four trading
  workflows (GitHub Actions skips later steps after a
  failed one) - fixed to always degrade to a skipped push
  notification, never a crash. The final `flutter build
  apk` + `adb install` step needed a **local** Claude Code
  session (Desktop app, pointed at a local folder with Git
  installed) - this dev sandbox has no Flutter SDK and no
  access to the user's phone/USB, a hard boundary, not a
  setup gap. Also added .github/workflows/
  build_android_apk.yml (manual, builds the APK on
  GitHub's runner as a downloadable artifact) as a
  fallback that doesn't need local Flutter either.

• FIXED 28-Jul: paper_trade.yml (Watchlist Paper Trade
  Check) never received the 21-Jul git-race retry/resync
  fix that the three Best Trade workflows got that day -
  it only had the earlier `git pull --rebase` line. Caused
  3 real consecutive failures the morning of 28-Jul
  (03:07/03:22/03:37 UTC) - a ref-level race against Best
  Trade Entry Scan's 1-min-cadence pushes to the same
  `main` branch (not a same-file conflict, they touch
  different report files). Applied the identical
  discard-local-write/hard-reset/re-run-script fix used on
  the other three workflows, verified live. No trading
  data was lost (same as every prior instance of this bug
  class), but 3 consecutive 15-min checks were skipped
  that morning.

• FIXED 23-Jul: every backtest's transaction-cost
  assumption was a flat ~Rs 30/trade guess - user
  correctly pointed out real broker charges are almost
  entirely percentage-of-turnover (brokerage capped at
  Rs 20/order, STT 0.025% sell-only, exchange charges
  ~0.003%, stamp duty 0.003% buy-only, 18% GST on top),
  not a flat rupee amount, so a flat guess badly
  overstates cost on cheap/small trades and roughly
  matches it on expensive/index-level ones. Built
  strategy/transaction_costs.py modeling Zerodha's
  published rates (representative of discount brokers)
  and wired it into strategy/orb_vwap_backtest.py,
  vwap_pullback_backtest.py, ema_volume_breakout_backtest.py,
  and multi_timeframe_backtest.py, replacing every flat-
  cost parameter. See the corrected figures inline below
  and in the transaction-cost note under Priority 6 - none
  of 22-Jul's rejected strategies flip to profitable, but
  the losses are meaningfully smaller than first reported.

• CONCLUSIVELY REJECTED 22-Jul: ORB (entry) + VWAP
  (direction filter) + Volume-spike (confirmation) for
  stocks, the intraday candidate researched 21-Jul (see
  strategy/orb_vwap_backtest.py, analysis-only). Sweep of
  48 parameter combos (4 volume-spike thresholds x 6
  ATR SL/Target ratios x 2 Opening-Range lengths) across
  6 NIFTY 50 stocks (ICICIBANK, RELIANCE, HDFCBANK, TCS,
  BAJFINANCE, TITAN; 5m candles, 60d): every single combo
  was net-negative after an estimated Rs 30/trade real
  cost, ranging from -Rs 8,669 (best) to -Rs 41,645
  (worst). Root cause: the entry fires far too often
  (189-1,406 total trades across the 6 stocks depending
  on parameters) for its tiny gross edge (best case only
  +Rs 60.71 gross across all 6 stocks/60 days) to survive
  transaction costs - not fixable by retuning, same
  conclusion pattern as the 15m-strategy finding above.
  Do not pursue this combination further for stocks.

  CORRECTED 23-Jul: the Rs 30/trade figure above was a
  flat guess and overstated real cost for these small
  (1-share) trades - see the real percentage-based
  transaction-cost model below. Re-run with the corrected
  model at default params: net loss per stock shrank from
  roughly -Rs 6,500/-7,700 to just -Rs 144/-1,330 (e.g.
  ICICIBANK -Rs 6,584 -> -Rs 299, HDFCBANK -Rs 6,497 ->
  -Rs 144). Still net-negative on every stock, so the
  REJECTED verdict stands, but nowhere near as
  catastrophically as first reported - the real problem
  is the gross edge being too small/inconsistent, not
  overstated transaction costs.

• CONCLUSIVELY REJECTED 25-Jul: Supertrend trend-flip
  entry, optionally filtered by CPR bias (close vs. the
  previous calendar day's Pivot), researched from the
  22-Jul external strategy list (see
  strategy/supertrend_cpr_backtest.py, analysis-only; new
  building-block indicators indicators/supertrend.py and
  indicators/cpr.py, unit-tested, not yet used by any
  other strategy). Swept 12 ATR SL/Target combos (0.5x/
  1.0x/1.5x SL x 1.5x/2.0x/3.0x/4.0x Target) on both NIFTY
  and BANKNIFTY (5m candles, 60d): every single combo net-
  negative after real transaction costs, from -Rs 873
  (best: NIFTY, 1.0x SL/2.0x Target, 44 trades, 34.09% win
  rate) to -Rs 2,645 (worst: BANKNIFTY, 0.5x SL/2.0x
  Target). The CPR bias filter roughly halved trade count
  on NIFTY (98 -> 44) and reduced net loss at the same
  1.0x/2.0x combo (-Rs 2,262 unfiltered -> -Rs 873
  filtered), but never flipped net-positive. Same root
  cause as every other rejected intraday candidate this
  week: gross edge (NIFTY's best case only +Rs 238 across
  all 44 trades) too small relative to trade frequency to
  survive transaction costs. Do not pursue Supertrend+CPR
  further as a standalone intraday entry for either index
  - Supertrend/CPR remain available as building blocks for
  a different combination if one is proposed later.

• PROMISING (not yet tradeable) 22-Jul: Momentum (RSI)
  + India VIX filter for BUY CE/BUY PE, researched 21-Jul
  (see strategy/momentum_vix_backtest.py, analysis-only).
  No free historical option-premium data exists, so this
  backtests directional accuracy on the underlying only
  (NIFTY/BANKNIFTY spot) - a "win" means the underlying
  moved far enough in the predicted direction to have
  been a profitable CE/PE buy in principle, not a real
  rupee P&L. Swept 42 combos (3 India-VIX percentile
  bands x 14 ATR SL/Target ratios) on both indices
  (15m candles, 60d):
  - NIFTY: only 9/42 combos (21%) positive, best only
    +524.26 points, most combos meaningfully negative
    (down to -880.17) - no reliable edge, REJECTED.
  - BANKNIFTY: 38/42 combos (90%) positive - a
    consistent result, not a cherry-picked one. Best
    found: VIX in its 30th-70th percentile band, 1.5x
    ATR Stop-Loss / 4.0x ATR Target - 38 trades, 42.11%
    win rate, +3,775.53 underlying points over 60 days
    (roughly +6.6% of BANKNIFTY's ~57,127 spot level).
  Before trusting the BANKNIFTY result as tradeable:
  still needs a real option-premium/theta-decay cost
  model (directional accuracy is necessary but not
  sufficient - the edge could still be erased by premium
  decay) and a net-of-costs check, same as the
  transaction-cost note below. Not wired into any paper
  trading yet.

• FIXED 29-Jul (same day as found): best_trade_squareoff.yml
  had been stuck on GitHub's native `schedule:` trigger
  (`15 9 * * 1-5` = 14:45 IST) - never migrated to
  cron-job.org like Best Trade Entry Scan / Watchlist Paper
  Trade Check were on 20-Jul, on the assumption that a
  once-a-day job wouldn't hit the same under-firing problem.
  It does: checked the last 7 real runs via the GitHub
  Actions API, every one fired 2-3.5 hours late (20-Jul
  +2h44m, 21-Jul +2h04m, 22-Jul +2h05m, 23-Jul +2h05m, 24-Jul
  +1h57m, 27-Jul +3h22m, 28-Jul +2h13m), and on 29-Jul it
  didn't fire at all - a real Best Trade position (TATASTEEL)
  sat open more than an hour past NSE close before the user
  noticed and it was manually closed via workflow_dispatch
  (Entry Rs 186.89, Exit Rs 187.60, PnL +Rs 0.71 - no data
  lost, same as every other instance of this bug class, but
  the "never carries overnight" design guarantee came close
  to breaking for the first time). FIXED: user added a third
  cron-job.org job ("Best Trade Square-Off Trigger") POSTing
  to workflow_dispatch every 5 min, 14:40-15:15 IST
  (`10,15,20,25,30,35,40,45 9 * * 1-5` UTC) - same pattern as
  the existing two, walked through together this session
  (cron-job.org's visual schedule builder rejected the `/5`
  step syntax in the crontab-expression field, needed the
  explicit comma-separated minute list instead). Verified via
  a manual test run (204, then workflow_dispatch completed
  successfully) - not yet confirmed at the real 14:45 IST
  cadence on a live trading day, that's the real test still
  to come.

• ADDED + TESTED, 02-Aug: Crash Protection Engine
  (strategy/crash_protection_engine.py, detect_crash_state) -
  researched after the user asked whether this project has
  any protection against a sudden market crash. It didn't -
  every existing safeguard (per-trade Stop-Loss, position
  sizing, MAX_CONCURRENT_POSITIONS cap, Best Trade Engine's
  forced 14:45 square-off) limits how much any *one* trade or
  *one* day can lose, but nothing looked at the market itself
  and paused new entries during a crash. Flags a day as
  "crash state" if either that day's own return is <= -4.0%
  or the rolling 5-day cumulative return is <= -10.0% (both
  trailing-only, no look-ahead) - thresholds calibrated
  against 19 years of real NIFTY daily history (2007-2026,
  yfinance period="max"), covering 2008, COVID-2020, the
  24-Aug-2015 Black Monday, and the 4-Jun-2024 election-result
  crash. 4 unit tests (tests/test_crash_protection_engine.py),
  all passing. Wired in as an optional require_no_crash_state
  parameter on strategy/multi_timeframe_backtest.py (default
  False/off) - only gates new entries, never touches an
  already-open position's Stop-Loss.

  TESTED same day against the VIX 30-70 combo (30-Jul's best
  finding - Daily-aligned NIFTY, 0.5x SL, no trailing stop, no
  ADX, VIX in its 30th-70th percentile band): re-ran the exact
  combo first as a sanity check and reproduced the recorded
  -Rs 115.37 net PnL / 6 trades / 50.0% win rate exactly, then
  re-ran the same combo with require_no_crash_state=True added.
  Result: IDENTICAL - same 6 trades, same -Rs 115.37 net PnL,
  zero change. Cause: the 60-day window this backtest pulls
  (yfinance's 15m/5m history limit) contained no single day
  hitting -4% or 5-day window hitting -10% on NIFTY, so the new
  filter never actually fired - a null result caused by the
  test window being calm, not evidence the filter does nothing.
  Consistent with the engine's own calibration note (~1.9
  single-day-crash-grade days/year historically) - a 60-day
  window without one is unsurprising, not a good window to
  judge this filter's effect in. Would need either a historical
  daily-only backtest spanning a real crash period (2008/2020/
  Aug-2015/Jun-2024) or continued live/paper monitoring across
  enough calendar time to actually hit a crash day to say
  anything about its real effect. Still NOT wired into live
  paper trading.

• FIXED 03-Aug: every timestamp shown in the Android app
  (trade Entry/Exit times, chart "Updated ..." caption)
  read ~5.5 hours earlier than it actually happened - the
  user noticed the mismatch and asked for a check.
  Root cause: reports/*.json's "Entry Time"/"Exit Time"/
  "Generated At" fields are all plain Python
  datetime.now() on a GitHub Actions runner (UTC) - every
  engine's IST-aware datetime is only ever used internally
  for market-hours gating, never for what actually gets
  persisted. mobile_app's formatBackendTimestamp() parsed
  that raw UTC string and displayed it as-is with no
  timezone shift. Fixed by parsing as UTC and adding the
  +5:30 IST offset before formatting (one shared function,
  fixes Portfolio/History/trade-detail-sheet/chart-caption
  everywhere at once) - see mobile_app/lib/widgets/
  common.dart. The backend's own stored timestamps are
  unchanged (still raw UTC, an internal detail) - this was
  a display-only fix, deliberately not a data migration.

• ADDED 03-Aug: History screen's Intraday section never
  showed its own Cash figure the way the Swing section
  does - Best Trade's portfolio has always tracked Cash
  independently (two separate Rs 100,000 paper accounts,
  not a shared pool - the user asked to confirm this same
  session, see strategy/best_trade_paper_trading.py and
  strategy/paper_trading.py's own INITIAL_CAPITAL), just
  never surfaced in the app. Added the same Cash StatPill
  Swing already has.

• LEANING REJECTED, 03-Aug: NIFTY/BANKNIFTY options
  money-management strategy (full Rs 1,00,000 capital in
  one ATM option/day, fixed % net profit target, fixed %
  Stop-Loss, one trade/day) - user-requested design, see
  strategy/nifty_options_backtest.py (analysis-only),
  indicators/black_scholes.py (premium ESTIMATE - no real
  historical option premium data exists, confirmed 30-Jul),
  strategy/options_transaction_costs.py (real options F&O
  cost model, separate from the equity one). 8 new passing
  unit tests.

  FOUND AND FIXED a modeling bug along the way: repricing
  off LIVE, continuously-updating India VIX every candle
  made Stop-Loss exits overshoot their nominal threshold by
  4-9x (nominal -0.5% SL realizing -4.48% avg/-13.76% worst
  at 5m, still -2.20% avg/-3.92% worst at 1m). Freezing IV
  at entry (hold_iv_fixed_at_entry=True, default) did NOT
  fix it (-4.76% avg, unchanged) - disproving the VIX-noise
  theory. Real cause: short-dated (3-day) ATM options are
  inherently this leveraged (a routine 0.1% NIFTY move can
  swing an ATM option's value ~8%) - not a bug. The
  overshoot gap stayed ~constant (~4 percentage points)
  regardless of the nominal SL tested (0.5-5%) - useful for
  real risk-sizing (expect a "Stop Loss" day's real loss to
  run ~4 points past whatever nominal SL is set).

  TESTED three variants after widening target/SL to 2-5%
  (to actually contain the leverage found above):
  1. NIFTY, forced-entry (RSI>=50 tie-break, guarantees a
     trade every day, NOT this repo's tested signal): broadly
     positive (best: Target 5%/SL 5%, +106% over 57 days,
     56% win rate) - but built on an invented, unvalidated
     direction rule, likely fit to this one 60-day window.
  2. NIFTY, REAL tested signal (momentum_vix_backtest.py's
     Momentum(RSI>60/<40)+VIX-band filter, trades <1x/day):
     INCONSISTENT - Target 3%/SL 5% alone lost Rs 13,219
     while neighboring combos were positive. Confirms 30-Jul's
     finding that this signal has no reliable edge on NIFTY.
  3. BANKNIFTY, same real signal (the one index the 22-Jul
     test found a strong 38/42-combo directional edge on):
     CONSISTENTLY, substantially NEGATIVE on every combo
     (worst: -Rs 1,14,539/-114.5% over 52 days). Important
     finding on its own - correct DIRECTION does not equal
     real option PROFIT once premium decay/leverage/costs
     are modeled, exactly the gap 22-Jul's own caveat warned
     about. CAVEAT: BANKNIFTY's weekly expiry was
     discontinued Nov-2024 (monthly only) - this backtest's
     fixed days_to_expiry=3 assumption is much less realistic
     for BANKNIFTY than for NIFTY (still weekly), so some of
     this negative result may be inflated leverage from the
     approximation rather than pure proof the idea fails.

  OVERALL: no tested variant showed a reliable, trustworthy
  edge once real premium economics were modeled - the one
  clean-looking result (NIFTY forced-entry) rests on a
  direction rule already known to lack real edge. Leaning
  REJECTED as currently designed; not wired into any paper
  trading. Next step if revisited: a real BANKNIFTY expiry
  calendar instead of the fixed 3-day approximation, before
  treating the negative BANKNIFTY result as final.

==================================================

NEXT DEVELOPMENT PLAN

Priority 1

FCM push-notification feature - LIVE AND VERIFIED 25-Jul
(report/push_notifier.py, report/notifier.py, Flutter
firebase_core/firebase_messaging wiring, all four
trading workflows' FIREBASE_SERVICE_ACCOUNT secret,
google-services.json committed). APK built via the
build_android_apk.yml GitHub Actions workflow (no
Flutter SDK needed on the user's machine) and installed
via adb; a manual pre_market_report.yml trigger
confirmed the push notification arrives on the user's
phone alongside Telegram. Next: just monitor a few real
trade alerts over the coming days to confirm it keeps
working reliably, not just this one manual test.

--------------------------------------------------

Priority 2

Run the Daily-timeframe watchlist paper trading
(with confidence-based sizing + risk cap) for
1 more week - review ~26-Jul via the Android app's
History tab / reports/paper_portfolio.json. Agreed
with the user 19-Jul: don't start intraday-strategy
design or broker/live-data work before this review.
Now also watch the two real Best Trade Engine
outcomes from 21-Jul (ULTRACEMCO closed on SL,
ICICIBANK opened) now that the price-fetch crash is
fixed and real data is actually flowing.

UPDATE 29-Jul: agreed plan for August - let both
engines run through the full month collecting real
results before drawing firm conclusions (as of 29-Jul:
Watchlist 8 closed trades since 11-Jul, Best Trade
Engine 18 closed trades since 21-Jul - both still well
short of the ~30-50 trades usually needed for
statistical confidence; Watchlist accumulates much
slower than Intraday given its swing-style hold times).
In parallel, keep researching new strategy candidates
(see Priority 3) rather than waiting idle for August's
data to accumulate - agreed direction, in priority
order:
1. DONE 30-Jul: India VIX regime filter applied to
   equity entries - see Known Issues for the full
   result (30-70 percentile band: -Rs 115.37 net, 6
   trades, an 81% reduction from the no-filter
   baseline). Promising, same small-sample caveat as
   everything else - not wired into live paper trading.
2. NOT TESTABLE 30-Jul: option chain PCR/Max Pain as
   equity support/resistance - unlike every other
   candidate here, NSE's option chain API has no
   historical archive (only today's live snapshot), so
   this cannot be backtested against past data the way
   VIX/price data can. Confirmed the live fetch itself
   is also currently failing (403 even from the user's
   home network, not just the documented datacenter-IP
   block) - see strategy/option_chain_engine.py. Only
   testable prospectively (tracked live going forward),
   not retroactively - shelved for now, not rejected on
   the idea's merits.
3. TESTED 30-Jul, inconclusive: time-of-day entry
   filter on the Daily-aligned NIFTY baseline (22
   trades, split into first-90-min/midday/last-stretch
   buckets of 5-11 trades each) - all three buckets
   landed within a similar range (-Rs 25 to -Rs 35 net
   per trade), no bucket stood out as meaningfully
   better or worse. Sample far too small per bucket to
   be conclusive either way; also surfaced that this
   combo's 31.82% *gross* win rate is 0% once real
   transaction costs are applied per trade - the tight
   0.5x-ATR stop makes individual wins smaller than the
   round-trip cost on an index-sized position. Not
   pursued further at this sample size.
4. REJECTED 30-Jul: partial profit booking on the
   Daily-timeframe strategy - see Known Issues for the
   full breakdown. Worse than the existing 1.5x SL/3x
   Target baseline in 3 of 4 tested symbols, notably
   halving the gain on the one case (RELIANCE) where
   the baseline was actually profitable. Not adopted.
Two riskier, less-precedented directions flagged for
later if the above don't pan out: sector momentum/
sympathy moves, and a consolidation-breakout quality
filter.

--------------------------------------------------

Priority 3

Intraday strategy design - not the reused EMA/RSI swing
logic (flagged earlier as a bigger, ~2-3 hour task).
Researched 21-Jul, backtested 22-Jul (analysis-only
scripts, ahead of the 26-Jul review - safe to do early
since nothing was wired into live paper trading; see
Known Issues for full results):

- Stocks (Best Trade Engine): ORB + VWAP + Volume-spike
  - CONCLUSIVELY REJECTED, 22-Jul. 48-combo sweep across
  6 stocks, every single combo net-negative after
  transaction costs (best case -Rs 8,669). Do not pursue
  further - see strategy/orb_vwap_backtest.py for the
  (kept, analysis-only) implementation and Known Issues
  for the numbers.

- Options: Momentum (RSI) + India VIX filter, BUY CE/BUY
  PE only (rejected option-selling strategies like the
  "9:20 short straddle" - different risk profile, margin
  required, doesn't fit the buy-only architecture).
  Backtested 22-Jul on the underlying only (no free
  option-premium history exists, so this measures
  directional accuracy, not real premium P&L):
  - NIFTY: REJECTED - only 9/42 parameter combos
    positive, no reliable edge.
  - BANKNIFTY: PROMISING - 38/42 combos positive (90%),
    best found (VIX 30-70 percentile band, 1.5x SL/4.0x
    Target ATR) gave 38 trades, 42.11% win rate, +3,775.53
    underlying points over 60d. Consistent across nearly
    every combo tested, not a cherry-picked result.
    See strategy/momentum_vix_backtest.py.

Next step for BANKNIFTY options: still needs (a) a real
option-premium cost model before trusting this as
tradeable (directional accuracy on the underlying is a
necessary but not sufficient condition - premium/theta
decay could still erase the edge), and (b) net-of-costs
evaluation like the transaction-cost note below. Not yet
wired into any paper trading - waits for the 26-Jul
review before any live logic changes.

REGULATORY NOTE, 22-Jul: confirmed via NSE/SEBI rule
changes (effective Nov-2024) that directly affect this
BANKNIFTY finding's real-world tradeability -
BANKNIFTY's WEEKLY options expiry was discontinued (NSE
now allows only one benchmark index per exchange to have
weekly expiry - that's NIFTY, not BANKNIFTY). BANKNIFTY
options now only expire monthly, which changes theta
decay dynamics significantly versus what a weekly-expiry
assumption would imply - the option-premium cost model
above must account for monthly-expiry theta, not
weekly. Also: NIFTY/BANKNIFTY lot sizes increased
substantially (NIFTY 25->75, BANKNIFTY 15->30), raising
the real capital required per lot to trade this even in
future live testing.

- Supertrend trend-flip + CPR bias filter (from the 22-Jul
  external strategy list) - CONCLUSIVELY REJECTED 25-Jul
  on both NIFTY and BANKNIFTY, every SL/Target combo
  net-negative. See Known Issues for the full breakdown.

- Gap-fill (opposite thesis to Gap-and-Go) - UPDATE 25-Jul:
  tested rather than left as an assumption, see Known
  Issues. PROMISING on NIFTY specifically (+Rs 413.45 net,
  60d), does not generalize to BANKNIFTY or most stocks.
  Needs a second test window before trusting it further.

- Explicitly NOT pursuing: combining all strategy types
  into one signal (overfitting/conflicting-signal risk -
  one clear approach per instrument type instead).

- Also tested and REJECTED 22-Jul (from a strategy list
  the user got from another AI assistant and asked to
  verify against our own backtests, rather than trust
  blindly):
  - Plain ORB (no VWAP/Volume filter) on the same 6
    stocks - worse than the combined approach: 320-416
    trades per stock (vs 189-252 combined), net loss
    -Rs 9,500 to -Rs 12,500 per stock.
  - VWAP Pullback (price pulls back to touch VWAP, then
    bounces in the trend direction - a different entry
    style than the ORB breakout) - 9-combo sweep across
    the same 6 stocks, every combo gross-negative before
    even subtracting costs. See
    strategy/vwap_pullback_backtest.py.
    CORRECTED 23-Jul (real % cost model, see below): at
    default params (1.0x SL/2.0x Target), per-stock net
    losses shrank to roughly -Rs 46 to -Rs 886 (from
    -Rs 1,200 to -Rs 3,900 under the old flat-cost guess)
    - REJECTED verdict unchanged since gross PnL itself
    is already negative/near-zero in aggregate, which no
    cost correction can fix, but confirming this wasn't
    as catastrophic as first reported either.
  - 50 EMA + Volume Breakout (swing, daily candles) -
    small sample (2-9 trades/instrument over 2y) but
    mostly negative, and clearly underperforms the
    existing proven Daily/Watchlist strategy (which
    combines EMA+RSI+Structure+S/R+Candlestick+Volume via
    the AI Decision Engine, not just EMA+Volume alone) -
    confirms the multi-engine weighted-scoring approach
    matters, a single simple rule isn't enough. See
    strategy/ema_volume_breakout_backtest.py.

- Tested adding Candlestick-pattern confirmation
  (strategy/candlestick_engine.py, already part of the
  proven Daily strategy but unused in any 22-Jul intraday
  backtest) to ORB, VWAP Pullback, and the BANKNIFTY
  Momentum+VIX signal - it did NOT help any of them, and
  measurably HURT the BANKNIFTY result (best combo
  dropped from +3,775.53 to +179.48 points). Reason:
  candlestick patterns (Hammer/Engulfing/Doji) are
  reversal signals, logically mismatched with
  continuation/momentum-style entries - don't require
  candlestick confirmation on these strategy types.

--------------------------------------------------

Priority 4

Commit Desktop App (PySide6) to the repo,
package as .exe (PyInstaller)

--------------------------------------------------

Priority 5

Fix TATAMOTORS / LTIM ticker symbols

--------------------------------------------------

Priority 6

DECIDED, 03-Aug: Broker = Fyers (free API tier), chosen
over Upstox/Angel One after comparing API data-richness
(historical options data especially - the exact gap this
session's options-strategy research ran into), documentation
quality, and cost. User already holds an unused Angel One
account - kept in reserve as a free secondary data source if
Fyers has reliability issues later, not for order execution
(multi-broker execution explicitly rejected as unnecessary
complexity at this paper-trading stage). Zerodha (Kite
Connect, ₹2000/month, strongest ecosystem/community support
for AI-driven algo trading specifically) deliberately
deferred - user's own call: reconsider only once real AI/
algo-trading logic is actually being implemented (not yet),
not before.

Account opening needs the user's own KYC (PAN, Aadhaar,
bank details, signature, live-photo/video KYC, and - since
this project trades Options - income proof: 6-month bank
statement, salary slip, ITR, or Form 16, per SEBI's F&O
requirement) - Claude cannot do this step (personal/financial
documents), user must open the account themselves. Once API
key/secret exist, the integration CODE can start immediately
and safely even while Watchlist/Best Trade Engine trades are
still open - it's a new, separate module (this repo's engine-
separation rule), not a change to the existing yfinance-based
paper trading engines. The actual cutover from yfinance to
Fyers as the live data source is a later, separate step that
will need care around open positions - just building/testing
the integration does not.

Broker Integration itself (once account+API ready) → also
unlocks a paid/reliable Option Chain data source, and is the
prerequisite for true live/real-time data instead of the
current 15-min GitHub Actions refresh - discussed cost with
the user 19-Jul, roughly ₹0-2500/month depending on broker
chosen (now decided: ₹0, Fyers free tier).

PLAN AGREED, 03-Aug, once the user has a Fyers account + API
key/secret:

1. Keep the existing yfinance-based engines (strategy/
   paper_trading.py, strategy/best_trade_paper_trading.py)
   completely untouched - they keep running exactly as now.
2. Build a NEW, separate Fyers module/engine (working name:
   strategy/fyers_options_engine.py or similar - a dedicated
   options engine, on top of/alongside today's analysis-only
   strategy/nifty_options_backtest.py) - reads/writes only its
   own new files, never touches the yfinance engines' state.
   First check empirically how far back Fyers' historical API
   actually serves data for expired option contracts (may be
   limited - if so, fall back to building our own archive by
   polling the live option chain going forward, same pattern
   as reports/alignment_history.jsonl).
3. Two tracks, in parallel: (a) re-run existing/new strategies
   (ADX filter, VIX filter, today's options money-management
   idea, etc.) as backtests against real Fyers historical data
   once available, to check today's yfinance/Black-Scholes-
   estimate-based findings against real numbers; (b) a new
   daily automated job (mirrors the existing GitHub Actions
   paper-trading workflows) that takes real paper trades off
   Fyers' LIVE data into a separate reports/fyers_test_
   portfolio.json - both builds real-time track record AND
   accumulates real historical premium data over time.
4. Mobile app: no change needed to switch data sources (it
   only ever reads whichever JSON file it's pointed at). A
   toggle ("yfinance (Live)" / "Fyers (Test)") to view both
   portfolios side by side in-app is a good later addition -
   build it AFTER fyers_test_portfolio.json actually has data
   in it, not before.
5. Only after Fyers is proven reliable over real time: a
   deliberate, separate cutover step moves live paper trading
   from yfinance to Fyers - tag trades from that point with a
   "Data Source" field so historical (yfinance-era) and new
   (Fyers-era) trades stay distinguishable in the record.

UPDATE 04-Aug - STEP 1-2 EXECUTED (account, auth, first real
data check):

• Fyers account opened + activated by the user (own KYC/income
  proof), API app created, Primary IP whitelisted (flagged as
  likely dynamic - a home-ISP IP, may need updating later).

• strategy/fyers_auth.py built - login/access-token flow
  against Fyers' raw REST API, not their official fyers-apiv3
  SDK (its aiohttp dependency failed to build on this machine's
  Python 3.14.6 - no prebuilt wheel, no MS C++ Build Tools).
  Full login flow run live and VERIFIED via Fyers' /profile
  endpoint (real account confirmed: TUSHAR RAJENDRA INGAVALE,
  FAK37571). Access token is a DAILY token - needs the login
  flow re-run each trading day; not yet automated (user chose
  manual-first).

• Data-coverage tested LIVE against the real API (not guessed):
  - 1-min INDEX data: confirmed real candles back to ~9 years
    (2017 ok, 2016 no_data - true cutoff somewhere between).
    100-day max per request (120+ days = "Invalid input") -
    needs pagination for a multi-year pull, straightforward.
  - Daily INDEX data: confirmed back to at least 2006 (20y).
  - THIS IS A MAJOR UPGRADE over yfinance's ~60-day intraday
    limit that constrained nearly every backtest finding
    recorded in this project to date - removes the recurring
    "small sample, one window" caveat, once re-tested.
  - Options: real live bid/ask/LTP/OI/volume confirmed working
    (options-chain-v3). CONFIRMED (via Fyers' public NSE F&O
    symbol master CSV, 75k+ rows) that EXPIRED option contracts
    are structurally absent - not a Fyers-specific gap, a
    property of how exchange-listed option symbols work (they
    stop existing after expiry). No broker is expected to serve
    genuinely old option premium data for this reason.
  - Futures: cont_flag=1 (continuous futures) gave real data
    back to at least Jan-2024 (1.5+ years, likely more, not
    fully pushed) - futures get real multi-year history in a
    way options structurally cannot (only the month changes,
    no strike dimension). A new avenue worth considering for a
    futures-based strategy.
  - Charges: no live API found (published rate card only,
    consistent with strategy/options_transaction_costs.py's
    modeled approach).
  - "AI connection"/MCP tab seen in Fyers' dashboard: NOT YET
    checked (site is JS-heavy, WebFetch can't render it; the
    Browser tool is policy-blocked from trading platforms) -
    open question for next session.

• Researched paid historical-options-data vendors (TrueData,
  Global Datafeeds, Sensibull) via live WebFetch - none publish
  exact historical depth on their public pages (gated behind
  sales contact); TrueData's general pricing found (Rs 1,440-
  2,796/month tiers) but not options-specific depth. NSE
  Bhavcopy (free, nseindia.com) is the one confirmed FREE real
  historical options source, though EOD-only (no intraday).
  Decision: don't spend on paid vendors yet - use the free
  Fyers-collection path below first.

• strategy/fyers_options_collector.py built (STEP 3b's "build
  our own archive" fallback) - manual-run script, snapshots the
  live NIFTY+BANKNIFTY option chain (5 strikes around ATM,
  nearest expiry) and appends every leg to reports/
  options_premium_history.jsonl (real bid/ask/LTP/OI/volume).
  First real snapshot taken and verified (44 records). Kept
  MANUAL for now (not on GitHub Actions) - the daily-token
  requirement above adds real complexity to automating this
  compared to the existing yfinance workflows; revisit once the
  manual version has proven itself useful.

• CAUGHT A SECURITY NEAR-MISS: Notepad saved the user's first
  .env edit as ".env.txt" (auto-appended extension) - a
  duplicate secrets file NOT covered by .gitignore's exact
  `.env` pattern, sitting untracked. Caught via `git status`
  before any git add/commit touched it - deleted the duplicate,
  added `.env.txt` to .gitignore as a safety net.

STEP 3 EXECUTED, same day - Fyers-based Swing + Intraday
paper trading engines built and tested (user pushed back on an
initial over-cautious "1-2 days" coding estimate, correctly
pointing out most of the existing analysis logic is already
data-source-agnostic - revised down to ~4-6 hours, which held):

• strategy/fyers_data.py - the one genuinely new piece: an
  adapter returning Fyers candles in yf.download()'s exact
  output shape, so analyze_symbol/calculate_rsi/calculate_atr/
  get_market_structure/etc. all work completely unchanged
  against it. Paginates past Fyers' 100-day/request intraday
  limit automatically. Found and fixed a rate-limit issue
  scanning 52 symbols back-to-back (retry-with-backoff +
  proactive delay).

• strategy/fyers_watchlist_scanner.py + strategy/fyers_paper_
  trading.py (Swing) and strategy/fyers_multi_timeframe_engine.py
  + strategy/fyers_best_trade_paper_trading.py + fyers_daily_
  best_trade.py (Intraday, deliberately simpler than the
  original - no shortlist/news/option-chain ranking yet) - both
  TESTED LIVE on real Fyers data: Swing opened 12 real BUY
  positions scanning the full NIFTY 50 watchlist (reports/
  fyers_test_portfolio.json); Intraday correctly found RELIANCE
  15m/5m/1m-aligned Bearish. All existing yfinance engines
  completely untouched - runs fully in parallel, own files only,
  same as the already-agreed plan above. Not yet on GitHub
  Actions - same daily-token-refresh question as the options
  collector (three options discussed: full auto-login with
  stored PIN+TOTP - flagged as a real security-risk increase if
  those ever leaked; a Telegram 1-tap reminder; an in-app
  WebView login button that never handles PIN/password in our
  own code - undecided).

STEP 4 EXECUTED, same day - real-premium options paper trading
+ app rewrite (user correction: the Fyers tab showing equity
Swing/Intraday was redundant with what already works on
yfinance - OPTIONS was the actual reason Fyers was integrated):

• strategy/fyers_options_paper_trading.py - same money-
  management rules researched 03-Aug (ATM strike, RSI-direction
  CE/PE, NET %-of-capital Target/Stop-Loss/Square-Off), but now
  using REAL Fyers quotes (bid/ask/LTP via /data/quotes for the
  exact held contract) instead of the Black-Scholes ESTIMATE the
  03-Aug backtest had to rely on. TESTED LIVE end-to-end: opened
  a real CE 24600 position at real premium 103.25, then
  correctly Square-Off closed it (net -Rs 219.95, real
  transaction costs) on the next check. 3 new passing tests.

• App: added the "Fyers" bottom-nav tab (6th tab; existing
  "Portfolio" relabeled "yfinance" for clarity), then REWROTE it
  same day per the user's correction to show this options
  portfolio (reports/fyers_options_portfolio.json) instead of
  equity data - custom cards in fyers_portfolio_screen.dart
  (not reusing widgets/common.dart's equity-shaped cards, which
  use different field names - that shared file stays untouched).
  Built + installed on the user's phone via adb, twice (once per
  rewrite), flutter analyze clean both times.

• DECIDED: of the three daily-token-refresh automation options,
  user chose the in-app WebView login button - weighed the
  PAT-in-app residual risk (a scoped, Actions-only GitHub PAT
  embedded in the APK, extractable if reverse-engineered, but
  limited to triggering this repo's own workflows only) against
  convenience, and confirmed the repo must stay PUBLIC either
  way (the app's raw.githubusercontent.com fetches need it -
  going private would break every existing screen).

STEP 5 EXECUTED, same day - the WebView login button BUILT and
VERIFIED WORKING END-TO-END (not just designed):
fyers_trigger_run.py + .github/workflows/fyers_trigger.yml +
mobile_app's new FyersLoginScreen. User did the two setup-only-
they-could-do steps (fine-grained GitHub PAT, 90-day expiry -
their own choice after discussing the no-expiry risk; FYERS_
APP_ID/FYERS_SECRET_KEY as GitHub repo secrets). Two real bugs
surfaced only via live testing (not caught by analyze/local
runs) and fixed: (1) a multi-path `git add file1 file2 file3 ||
true` silently discards EVERYTHING if even one file doesn't
exist yet (reports/fyers_best_trade_portfolio.json, until the
first Fyers Intraday position ever opens) - cost two real runs'
state before being caught and fixed (one `git add <file> ||
true` per file); (2) the WebView fired the redirect callback
twice from one tap, sending a second, always-failing trigger
(auth codes are one-time-use) - fixed with a guard flag. Also
hit a Windows-specific Kotlin/Gradle cross-drive (C: vs D:)
compiler crash in webview_flutter_android twice - fixed with
kotlin.incremental=false. FINAL VERIFIED RESULT: one tap -> real
Fyers login -> GitHub Actions run -> real CE 24600 option
position opened at real premium (Rs 103.25) -> correctly
committed to reports/fyers_options_portfolio.json, fyers_test_
portfolio.json, and options_premium_history.jsonl (44 records).

LIMITATION SURFACED, same day (right after the win above): user
asked to confirm "just log in once each morning, right?" - it's
NOT quite that yet. Today's button press runs the whole pipeline
exactly ONCE at the moment it's tapped - it does not continuously
monitor the day the way the existing yfinance workflows do
(checked every ~1-15 min via cron-job.org). A position opened at
the moment of the tap would not be checked again for Stop-Loss/
Target/Square-off until the button is tapped again. User wants
TRUE continuous same-day automation. PLAN for next session (not
yet built): Fyers' access token is valid for the WHOLE trading
day once obtained, not just one call - so (1) one morning login
stores that day's token as a GitHub Actions secret (updated via
the API), (2) separate, already-scheduled workflows (new
cron-job.org triggers, same pattern as the existing yfinance
Watchlist/Best Trade workflows) read that stored token every few
minutes for continuous checks, no further login needed until
tomorrow. Deliberately NOT the full auto-login-with-stored-PIN/
TOTP option rejected earlier (real account-access risk) - only a
short-lived, narrowly-scoped access token gets stored, not login
credentials.

BUG FOUND 05-Aug (diagnosed, NOT fixed - user chose to defer
the actual code change to later): the in-app "Login to Fyers"
button gets stuck on "loading" forever right after typing the
mobile number and tapping Continue - the embedded WebView never
progresses past Fyers' own login form. ROOT CAUSE (confirmed
live): Fyers' login page is protected by Google reCAPTCHA, which
reliably hangs inside embedded WebViews (Google treats it as an
automated/non-standard browser and never completes verification).
Confirmed this is NOT a Fyers-account/credentials problem: the
user opened the exact same login URL directly in their phone's
Chrome browser and it worked fine, reaching the expected
"127.0.0.1 refused to connect" redirect with a valid code visible
in the address bar (the same benign error strategy/fyers_auth.py's
desktop flow already documents as expected).

FIXED, same day (local machine session): rewrote mobile_app/
lib/screens/fyers_login_screen.dart exactly as suggested above -
"Login to Fyers" now opens the login page via url_launcher in
the device's real external browser, user pastes the redirected
URL/auth_code back into a text field. Dropped webview_flutter,
added url_launcher + the AndroidManifest.xml <queries> entry.
Built, installed, TESTED LIVE - real login completed this way,
trigger workflow ran successfully (confirmed via the GitHub
Actions API).

CONTINUOUS SAME-DAY AUTOMATION ALSO DONE, same session (04-Aug's
deferred Priority 6 plan, now built and verified): strategy/
github_secrets.py (PyNaCl sealed-box encryption per GitHub's
Actions-secrets API) lets fyers_trigger_run.py share each
morning's access token as the FYERS_ACCESS_TOKEN repo secret
(via a separate REPO_ADMIN_PAT, Secrets:write, server-side
only). Two new workflows reuse that shared token with no fresh
login: fyers_options_watch.yml (~1 min - user correctly pushed
back on an initial single 5-min-for-everything design, pointing
out real option premium moves several % within a minute per
04-Aug's leverage finding) and fyers_scheduled_check.yml (~5
min - Swing/Intraday don't benefit from faster checks than
their own timeframes). No separate square-off workflow needed -
both fyers_daily_best_trade.py and fyers_options_paper_trading.py
already self-check their square-off time on every run.

REAL BUG caught via live testing: the user's first REPO_ADMIN_PAT
was missing the "Secrets" permission entirely (a separate
category from "Actions" on GitHub's fine-grained PAT form, easy
to miss) - 403 on the public-key fetch step. Fixed by editing
the token's permissions. FINAL VERIFICATION (via the real GitHub
Actions API): after the fix, one more login shared the token
successfully, then both new workflows were manually dispatched
and BOTH succeeded reusing it, no fresh login needed.

cron-job.org SETUP DONE AND VERIFIED, same session: both new
jobs created (reusing the existing yfinance jobs' GitHub PAT for
Authorization - Actions:write covers any workflow in the repo,
no new cron-job.org-side PAT needed). Caught and fixed two real
setup mistakes via the user's own screenshots: the Options Watch
job's "Enable job" toggle was left off (cron-job.org saves a
disabled job silently, no warning - caught via the dashboard
showing it grayed out "Inactive"), and the Scheduled Check job
simply didn't exist yet (only 4 of the expected 5 jobs showed on
the dashboard). Both fixed, each re-verified with a manual TEST
RUN checked against real GitHub Actions run history. END STATE:
the full chain (one morning login -> shared token -> two
independently-scheduled workflows checking options every ~1 min
and Swing/Intraday every ~5 min, all day, no further login
needed) is live and confirmed working, not just built.

RE-TESTING PROVEN STRATEGIES ON REAL FYERS DATA, 05/06-Aug
(the deferred priority, now underway): built strategy/fyers_
multi_timeframe_backtest.py and strategy/fyers_backtest_engine.py
(Fyers-sourced counterparts to the existing yfinance backtest
tools) - found and fixed a real bug along the way (strategy/
fyers_data.py wrongly assumed daily candles had no per-request
range limit; Fyers actually caps at 366 days/request even for
"D" resolution, same as intraday resolutions just larger).

SIGNIFICANT FINDING - Swing (Watchlist), FULL 52 symbols, 2
years real data, the "proven" Daily-timeframe combo (1.5x SL/
3x Target ATR, filters on): 486 trades, 30.86% win rate, net
-Rs 7,427 (raw points). Only 19/50 (38%) symbols individually
profitable. This is a much larger, real sample than whatever
originally established this strategy as "the one with a proven
backtest edge" (repeated throughout this document's history) -
with that larger sample, the aggregate looks net-negative, not
clearly profitable. NEEDS FOLLOW-UP before fully trusting this
over the original claim: check whether the original "proven"
result came from a different (smaller/luckier) sample, a
different exact parameter combo, or whether something about
Fyers-vs-yfinance data itself differs enough to matter.

Intraday (Best Trade core) full-50-symbol, 1-year test is IN
PROGRESS as of this entry (see doc/05aug26_SESSION_LOG.md for
the two real problems hit along the way - a premature process
kill caused by buffered stdout looking like a hang, and Fyers'
daily token expiring mid-run at midnight, both understood and
recovered from). Partial result so far (5/50 symbols): all 5
net-negative.

Before any real capital is used (raised 21-Jul):
current paper-trading/backtest PnL is gross - it does
not subtract real per-trade costs. UPDATE 23-Jul: the
initial ₹20-40/round-trip flat guess was itself wrong -
user pointed out real broker charges are almost entirely
percentage-of-turnover (brokerage capped at ₹20/order,
STT 0.025% sell-only, exchange charges, stamp duty
0.003% buy-only, 18% GST), not a flat rupee amount.
Built strategy/transaction_costs.py modeling this
properly (Zerodha's published rates) and re-ran the
22-Jul intraday backtests with it - results are
meaningfully less negative for cheap stock trades (a
flat guess badly overstated cost when position value is
small, e.g. ICICIBANK's ORB net loss shrank from -₹6,584
to -₹299), while index-level trades stayed close to the
earlier flat estimate (cost naturally scales with the
~₹24,000+ per-unit value there). None of 22-Jul's
strategies flip to net-positive with the corrected
model, but the picture is much less pessimistic than
first reported. Both the Watchlist and Best Trade
Engine's own evaluations still need this same real-cost
check before trusting them as "profitable" - not done
yet for those two (only the new intraday-candidate
backtests use strategy/transaction_costs.py so far).
Fix this before Broker Integration, not after.

--------------------------------------------------

Priority 7

Tune the News Engine's keyword lexicon and
Best Trade Engine's weighting once 1-2 weeks
of real daily picks can be compared against
outcomes

--------------------------------------------------

Priority 8

Algorithmic Trading (after broker, user-supervised -
Claude never executes a real trade regardless; this
would be the user's own automation on top of broker
APIs, not something Claude does)

==================================================

LONG TERM ROADMAP

Paper Trading (live now)

↓

Desktop Dashboard (.exe)

↓

Broker Integration

↓

Live Trading (user-approved orders only)

↓

Algorithmic Trading (supervised)

--------------------------------------------------

STAGED CAPITAL PLAN (agreed 30-Jul)

The user's own staged plan for how far paper trading needs
to go before any real money, and how much:

1. August: keep both engines running, tune strategies with
   the real data as it accumulates (see Priority 2's four
   candidates - VIX filter promising, PCR/Max Pain shelved,
   time-of-day inconclusive, partial booking rejected).

2. If results hold up: get a broker API (Priority 6 -
   Upstox/Angel One, free-tier, still to be selected).

3. One more month of paper trading, this time against the
   broker's real data feed (not just yfinance) - checks
   whether the strategy still holds up on the data source
   it will actually trade against.

4. If that holds up too: start with Rs 10,000 of real
   capital - Claude still never executes a trade regardless
   of this stage; the user places every real order.

5. If Rs 10,000 is profitable: scale to Rs 1,00,000.

6. Continue forward using that Rs 1,00,000.

Process suggestions raised alongside the plan (not
financial advice - risk/engineering process only):

- Gate each stage on trade COUNT, not calendar time - a
  calendar month gives the Intraday engine ~40-50 trades
  (enough) but the slower Watchlist/Swing engine only
  ~15-20 (probably not enough) at current pace. Judge the
  two engines' readiness separately, not on one shared
  clock.
- Start the Rs 10,000 stage with only ONE engine (most
  likely Intraday, given its faster feedback loop), not
  both at once - less complexity and risk on the first real-
  money test.
- Define a stop/rollback rule up front, not just a scale-up
  rule - e.g. an explicit loss threshold or a run of
  consecutive losses that sends it back to paper trading,
  decided before the money is on the line, not improvised
  mid-drawdown.
- Once on a real broker, compare actual fill prices against
  this codebase's modeled transaction costs (strategy/
  transaction_costs.py, built off Zerodha's published rates)
  - real slippage may differ from the model.
- Ramp into the Rs 1,00,000 stage gradually (reduced size for
  the first couple of weeks, not full size immediately) -
  same principle already built into the Watchlist strategy's
  confidence-based position sizing.
- Treat the system's signals mechanically through the Rs
  10,000/Rs 1,00,000 stages too - no manual overrides based
  on gut feel, or it becomes impossible to tell whether the
  strategy itself is working.

==================================================

DEVELOPMENT RULES

• Never modify working modules.

• Add new functionality as separate engines.

• Every engine must have one responsibility.

• Engines return structured data only.

• Report Engine handles presentation.

• Options logic kept separate from stock/index logic.

• Claude never executes a real trade -
  final action is always the user's.

==================================================

Status

🟢 Stable

Current Version

v0.0.15

Next Version

v0.0.16

==================================================

END OF DOCUMENT
