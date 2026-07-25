# TURION AI Trader

PROJECT STATUS

==================================================

Project

TURION AI Trader

--------------------------------------------------

Version

v0.0.13

--------------------------------------------------

Build Status

🟢 Stable

--------------------------------------------------

Project Started

01-Jul-2026

--------------------------------------------------

Last Updated

25-Jul-2026

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

✅ Android App                (Flutter, 5 tabs - Portfolio/Best trade/
                               Watchlist/News/History - committed and
                               merged to main 19-Jul, installed on
                               phone via adb, reads GitHub raw JSON,
                               refreshed every 15 min by GitHub Actions)

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
                           (square_off_best_trade.py)

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

• PAUSED 21-Jul (not started): user asked for Best
  Trade / Watchlist trade alerts to also appear as a
  real push notification inside the TURION AI Trader
  Android app (Firebase Cloud Messaging), Telegram
  staying on alongside it. Plan agreed: user sets up a
  Firebase project + hands over google-services.json
  and a service-account key; Claude wires up
  firebase_core/firebase_messaging in the Flutter app
  (topic-based, no per-device token management) +
  report/push_notifier.py + a new
  FIREBASE_SERVICE_ACCOUNT GitHub secret across the
  four trading workflows. This dev sandbox has no
  Flutter SDK, so the final `flutter build apk` +
  `adb install` step happens on the user's own machine,
  same as the 19-Jul/20-Jul Android installs. Resuming
  this evening per the user's request.

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

- Explicitly NOT pursuing: Gap-fill (opposite thesis to
  Gap-and-Go, fewer opportunities), combining all
  strategy types into one signal (overfitting/conflicting-
  signal risk - one clear approach per instrument type
  instead).

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

Only after Priority 2 + 3: select Broker (Upstox /
Angel One - free API) → Broker Integration (also
unlocks a paid/reliable Option Chain data source,
and is the prerequisite for true live/real-time
data instead of the current 15-min GitHub Actions
refresh - discussed cost with the user 19-Jul,
roughly ₹0-2500/month depending on broker chosen)

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

v0.0.13

Next Version

v0.0.14

==================================================

END OF DOCUMENT
