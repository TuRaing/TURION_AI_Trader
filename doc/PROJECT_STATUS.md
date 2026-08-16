# TURION AI Trader

PROJECT STATUS

==================================================

Project

TURION AI Trader

--------------------------------------------------

Version

v0.0.19

--------------------------------------------------

Build Status

🟢 Stable

--------------------------------------------------

Project Started

01-Jul-2026

--------------------------------------------------

Last Updated

07-Aug-2026

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

✅ Broker Integration         (UPDATE 04/05/06-Aug: Fyers selected,
                               account+API live. Full auth (raw REST
                               OAuth, external-browser login + one-
                               tap app trigger), real historical +
                               live data (fyers_data.py), Swing +
                               Intraday + Options paper trading
                               engines all running on real Fyers
                               quotes. Options: 7 named strategies -
                               simple_st1/st2/st3/st4/gapfill (10
                               books, NIFTY+BANKNIFTY each), their
                               "threshold" profit-lock variant (10
                               more books), vix_filter (BANKNIFTY-
                               only, 1 book), oi_footprint (2 books) -
                               23 books total as of 08-Aug. Continuous
                               same-day automation (one
                               morning login -> shared token -> GitHub
                               Actions + cron-job.org triggers all
                               day, no further login needed). This is
                               real data/paper-trading integration -
                               NOT real order placement yet, see
                               Algorithmic Trading below.

🟡 Desktop Dashboard          (PySide6 built + verified, not committed
                               - unchanged since 25-Jul, still pending)

✅ Android App                (Flutter, now 9 tabs - yfinance/Intraday/
                               Swing/News/History/Fyers/Options/
                               Threshold Options/Options Summary (grew
                               from the original 5 as Fyers/Options
                               were added 04-06-Aug, then Threshold
                               Options + Options Summary added 08-Aug).
                               UPDATE 06-Aug:
                               Options tab restructured into strategy-
                               tabs x 2 index-subtabs (5 strategy-tabs
                               as of 07/08-Aug's gapfill addition), own
                               history each; Fyers Swing/Intraday now
                               show full closed-trade history (not
                               just the latest); newest-trade-on-top
                               ordering; Fyers-sourced candlestick
                               chart-on-tap (separate from the
                               yfinance one); a real timestamp double-
                               shift bug fixed. See 06aug26_SESSION_
                               LOG.md for the full list.

⬜ Live Trading               (user-approved real orders via Fyers -
                               NOT started: no real order-placement
                               code exists yet, only paper trading.
                               Needs the Rs 10,000 staged-capital gate
                               to be reached first - see STAGED
                               CAPITAL PLAN. Claude will still never
                               execute a trade itself at this stage
                               either - the user places every order,
                               this milestone is about building the
                               "review and approve" UI/flow.)

⬜ Algorithmic Trading        (fully autonomous, still user-supervised
                               - the final stage, after Live Trading
                               proves out. Broker now exists, so this
                               is no longer blocked on that - it's
                               blocked on Live Trading being reached
                               and proven first.)

⬜ TURION AI Trader v1.0

--------------------------------------------------

Progress: 25 / 30 milestones done (~83%) - Broker Integration moved
✅ this session; Algorithmic Trading's old single milestone split
into Live Trading (manual-approved real orders) + Algorithmic
Trading (autonomous) to reflect that broker data integration and
real order execution are different-sized remaining steps. 1 more
in-progress (Desktop App working locally, pending commit).

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

• FIXED 06-Aug: Android app's "yfinance" and "History" tabs (and,
  latently, "Fyers"/"Options" too) showed a blank flat-gray screen -
  root cause found once the user sent a screenshot (a plain gray
  box filling the whole body, no spinner/error/text - the exact
  signature of Flutter's default release-mode ErrorWidget for an
  uncaught build() exception, not a data problem, which is why the
  earlier JSON/field-level checks turned up nothing). Real bug: in
  portfolio_screen.dart / history_screen.dart / fyers_portfolio_
  screen.dart / fyers_options_screen.dart, `child: RefreshIndicator
  (onRefresh: _fetch, child: _buildBody())` calls _buildBody()
  EAGERLY as a constructor argument - Dart evaluates it immediately,
  before LoadingErrorWrapper's own loading/hasData check ever runs -
  and _buildBody()'s first line (`final portfolio = _portfolio!;`)
  null-check-crashes on every build where _portfolio is still null
  (the first frame, or any build following a failed/slow fetch).
  This turned what should have been a harmless spinner or a
  friendly "Could not load data / Retry" screen into a permanent
  crash whenever that screen's fetch had any hiccup - explains why
  it was specifically paper_portfolio.json/best_trade_portfolio.json
  (the latter rewritten very frequently by live automation, more
  exposed to a transient fetch failure) that actually manifested it,
  even though Fyers screens carried the identical latent bug. FIXED:
  guard the call site so _buildBody() only runs once _portfolio is
  actually non-null, in all 4 affected screens. Also added a 15s
  timeout to api.dart's fetchJson so a stalled request resolves to a
  retry-able error instead of hanging _loading forever. flutter
  analyze clean; built a fresh release APK and installed it on the
  user's phone via adb (device re-authorized this session).

• TESTING ARTIFACT IDENTIFIED, 06-Aug: the Fyers Options
  portfolio's big +₹26,472.24 (+26.47%) "Target" win (Cash grew
  ₹1,00,000 -> ₹1,25,982.63) is NOT a trustworthy live result -
  its Entry Time was 05-Aug 00:14:54 IST, well outside NSE market
  hours (09:15-15:30), which only happened because of this
  session's own manual fyers_trigger_run.py test runs overnight
  while debugging the login/PAT/automation fixes. A price
  recorded at a non-market moment (likely a stale last-close
  quote) compared against a later real intraday quote can produce
  an inflated-looking move that would not have been achievable as
  an actual trade. RESET, same day: cleared reports/fyers_options_
  portfolio.json back to a fresh ₹1,00,000/no-trades state so the
  record only reflects the properly-gated live automation going
  forward, not this test artifact.

• FIXED 06-Aug: FOUND AND FIXED (before real capital, but a real
  correctness bug regardless) - strategy/fyers_options_paper_
  trading.py had NO entry-time gate at all (unlike the equity
  Best Trade engine's 10:00-14:15 IST window), so it could open
  (and did open) a position during NSE's pre-open auction session
  before regular continuous trading even starts at 09:15 IST.
  Diagnosed after the user asked "is the options data real?"
  following a day where 10 real trades ran 06-Aug: verified via
  the real GitHub Actions run history (public API) that
  fyers_options_watch.yml fired reliably every ~1 min all morning
  with zero gaps (129 runs, all success) - ruling out a scheduling
  gap as the cause of trade #1's outsized +24.03% "Target" hit in
  under 6 minutes. Root cause instead: trade #1's Entry Time was
  09:11:51 IST, before the 09:15 market open - pre-open auction
  quotes are indicative, not real continuous-market prices, and
  the auction-to-open transition produced a large, discontinuous,
  not-really-achievable premium jump. All other trades that day
  (entered after 09:15) showed normal-sized overshoot past the
  2%/5% thresholds (2-8 points), consistent with the already-
  documented ~1-min check cadence + short-dated-option leverage,
  not a bug. FIXED: added MARKET_OPEN_TIME = (9, 15) - check_or_
  open() now skips opening a new position before 09:15 IST
  (an already-open position still gets checked/closed normally
  regardless of time, same as before). 3 existing unit tests still
  pass; module imports clean.

• FIXED 06-Aug: ROOT CAUSE of Intraday never opening a real
  position + Swing's 15 open positions never getting fresh checks -
  two compounding bugs, found by digging into the real GitHub
  Actions run history (public API) instead of assuming the strategy
  code was at fault:
  1. The "Fyers Scheduled Check Trigger" cron-job.org job (meant to
     hit fyers_scheduled_check.yml every ~5 min, running Swing +
     Intraday together) had simply never been created - the
     dashboard showed only 4 Fyers/yfinance jobs, no Scheduled
     Check job. Confirmed via the workflow's run history: only 3
     runs total ever, vs. Options Watch's 129 runs in one morning.
     FIXED: user repurposed an inactive leftover duplicate job
     (renamed, repointed at fyers_scheduled_check.yml/dispatches,
     Mon-Fri ~5-min market-hours schedule, enabled) - verified via
     Test Run landing on GitHub Actions.
  2. Even the runs that DID fire weren't saving their results. All
     3 Fyers workflows' commit step retried a rejected git push
     with `git fetch` + `git reset --hard origin/main` - which
     DISCARDS the just-computed local commit entirely instead of
     just resyncing. Confirmed live in a real run's log: a real
     commit ("2 files changed") got made, the push was rejected
     (racing fyers_options_watch.yml's ~1-min-cadence pushes to the
     same branch), reset --hard wiped that commit, and the retry
     found nothing left to commit - the job still reported
     "success" with nothing actually saved. This is why Swing's
     Last Checked timestamps were stuck on 05-Aug despite the
     workflow appearing to run fine. FIXED in all 3 workflows
     (fyers_scheduled_check.yml, fyers_options_watch.yml, fyers_
     trigger.yml): commit once up front, then on a push conflict,
     rebase that commit onto latest origin and retry - never
     discard it. VERIFIED live: re-triggered after both fixes,
     Last Checked timestamps finally advanced to real time.
  Both fixes are now live; Intraday still hadn't caught a 15m/5m/1m
  alignment as of this entry (expected - the signal is selective by
  design), but is now actually getting checked every ~5 min for the
  first time since it was built.

• FIXED 06-Aug (same day, right after the fix above): once the cron
  job + git-race fixes let Intraday actually run, its first-ever
  real position (SBIN, opened ~14:07 IST) still wouldn't close
  despite being well past its 14:45 IST square-off time on every
  5-min check since. Root cause in fyers_daily_best_trade.py's
  monitor_open_position(): after a close, portfolio["Position"]
  becomes None, but the status print read it back via
  `portfolio.get('Position', {}).get('Name', symbol)` - dict.get()'s
  default only applies when the KEY is missing, not when its value
  is None, so this crashed with 'NoneType' object has no attribute
  'get' on every close attempt, BEFORE save_best_trade_portfolio()
  could persist it - the close was computed correctly in memory
  every single time and silently thrown away every single time.
  Fixed by reading the position's name before the close call
  instead of after. VERIFIED live: SBIN closed for real on the next
  trigger (Entry ₹1,081.90 -> Exit ₹1,085.00, Intraday Square-Off,
  PnL +₹3.10) - the first complete, real Fyers Intraday trade this
  project has ever produced.

• FIXED 06-Aug: fyers_portfolio_screen.dart's "Fyers" tab only ever
  showed the Intraday section's currently-OPEN position - once a
  trade closed (see the SBIN fix above) it just reverted to "No
  open intraday position today" with no way to see what had just
  happened, which is what made the SBIN close look like it hadn't
  worked even after the backend fix landed. Added a ClosedTradeCard
  fallback showing the latest Intraday closed trade when there's no
  open position, matching the pattern Swing's own EventBanner
  already used. flutter analyze clean; rebuilt and reinstalled the
  APK.

• FOUND 06-Aug (not yet fixed - documented for follow-up): the
  Options engine's real day-1 results expose an unfavorable risk/
  reward ratio. 49 real trades, 61.2% win rate (30 wins/19 losses) -
  but still a NET LOSS of -₹3,128.35 (Cash ₹1,00,000 -> ₹96,871.65).
  TARGET_NET_PCT=2.0 vs STOP_LOSS_PCT=5.0 needs a win rate above
  ~71% (5/(5+2)) just to break even at those exact nominal levels,
  and real overshoot past the nominal Stop-Loss (leverage effect,
  documented earlier this session) makes losses run even bigger in
  practice - so today's respectable-looking 61.2% win rate still
  wasn't enough. Worth testing a more symmetric target/stop ratio
  (or target > stop) before trusting this strategy's real-money
  potential - not changed yet, just documented.

• PHASE 1 DONE, 06-Aug - multi-strategy options paper trading (user
  request: several live strategies in parallel, each on NIFTY AND
  BANKNIFTY, own full ₹1,00,000 each). Built strategy/fyers_options_
  engine.py (one generalized, parameterized core, config-driven
  Target/Stop-Loss/index/lot-size instead of near-duplicate files) -
  original live strategy/fyers_options_paper_trading.py untouched.
  3 strategies through it (simple_st1: retuned symmetric 3%/3%;
  st2: Target 5%/SL 2%; st3: Target 5%/SL 5% - st2/st3 reuse the best
  ratios nifty_options_backtest.py's 06-Aug sweep found on Black-
  Scholes-estimated data, now testing them against real quotes). A
  4th, materially different strategy (st4: strategy/fyers_options_
  st4.py) needs its own module - one trade/day, entry requires BOTH
  15m/5m/1m multi-timeframe alignment AND 15m ADX>25 (this project's
  own two most-validated filters, reused rather than inventing an
  untested one - user explicitly asked for a recommendation first),
  then a trailing stop (1.0x the entry ATR, on the underlying's own
  spot price since Fyers has no per-contract candle history to ATR
  the premium itself) once net profit crosses ₹1,000. All 4 x 2
  indices (8 configs) wired into fyers_multi_strategy_options_run.py.
  9 new unit tests, full suite (152) passing. Manually verified
  simple_st1 end-to-end against real Fyers quotes (both indices
  opened real ATM positions correctly); also found and fixed a
  related gap the same test surfaced (no gate against a NEW entry
  after market close, only before open existed - added).

  AUTOMATION WIRED UP same session: .github/workflows/fyers_multi_
  strategy_options.yml (workflow_dispatch, correct commit-then-
  rebase-on-conflict pattern from the start). REDESIGNED after the
  user pointed out one shared cron-job.org job for all 8 configs
  means pausing it pauses every strategy at once - added a
  STRATEGY_NAME filter (env var / `strategy` workflow_dispatch input,
  default "all") so the SAME workflow can be triggered per-strategy.
  User set up 4 separate cron-job.org jobs (one per strategy, both
  indices together), each at 1-min cadence - independently pausable
  now. Verified the filter on the real GitHub Actions runner
  (dispatched with strategy=st2, only st2's 2 configs ran). NOTE: 3
  of the many manual verification triggers fired this session got
  stuck "queued" for 15-20+ min without starting, most likely from
  this session's own unusually high trigger volume (20+ manual
  dispatches across various Fyers workflows within an hour) rather
  than a real defect - 4 other runs in the same window completed
  successfully, proving the logic itself works. Real verification is
  tomorrow's regular cadence during actual market hours, not more
  manual bursts. STILL NOT DONE: the app's Options tab restructure
  (4 strategy-tabs x 2 index-subtabs, separate history each) - see
  doc/06aug26_SESSION_LOG.md's Next Session Priorities for the full
  remaining list (also includes: separate Swing/Intraday history
  lists in the app, newest-on-top ordering, a real Fyers-timestamp
  double-shift bug diagnosed but not fixed, and a Fyers-sourced
  candle-chart-on-tap design).

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

Intraday (Best Trade core) full-50-symbol, 1-year test: hit
Fyers' midnight daily-token expiry TWICE across two separate
overnight attempts (see doc/05aug26_SESSION_LOG.md and
doc/06aug26_SESSION_LOG.md) - each attempt's not-yet-run
symbols failed with "Could not authenticate the user" once the
token expired, requiring a fresh morning login and a resume
script reusing already-completed results. COMPLETED 06-Aug after
the second resume: 48/50 symbols (TATAMOTORS.NS/LTIM.NS still
have no valid Fyers symbol), 7,680 total trades, 29.48% win
rate, TOTAL NET PnL -31,200.17 (raw points, not rupee-
normalized). ZERO of 48 symbols profitable - worse than the
Swing finding below (18/49 profitable). Worst 5: MARUTI.NS
(-3,815.02), BAJAJ-AUTO.NS (-3,206.10), EICHERMOT.NS (-2,335.44),
APOLLOHOSP.NS (-2,026.66), DIVISLAB.NS (-1,936.43). Combined with
the Swing result below, this is now large-sample evidence that
BOTH of this project's core engines - not just one - are net-
negative on real Fyers data at real scale, not an isolated bad-
window result.

MAJOR FINDING, 06-Aug - Swing (Watchlist) + Bank Nifty, REAL
RUPEE position sizing (₹1,00,000 deployed independently per
symbol, not split across the watchlist - user's explicit
request), full NIFTY 50 + ^NSEBANK, 2 years real Fyers daily
data, the same "proven" combo (1.5x SL/3x Target ATR, filters
on): 477 trades across 49/51 symbols (TATAMOTORS.NS/LTIM.NS
still fail - no valid Fyers symbol, same as the yfinance-era
issue), 31.03% win rate, TOTAL NET PnL -₹1,28,490.80 (real
rupees, transaction costs included). Only 18/49 symbols
individually profitable. Bank Nifty specifically: 10 trades,
20% win rate, -₹5,417.21. Top winners: ADANIPORTS.NS
(+₹29,663.86), ADANIENT.NS (+₹26,471.54), HINDALCO.NS
(+₹23,517.61), HEROMOTOCO.NS (+₹23,328.70), SBILIFE.NS
(+₹13,387.77). Top losers: DRREDDY.NS (-₹24,033.36),
COALINDIA.NS (-₹20,425.15), BAJAJFINSV.NS (-₹19,929.45),
AXISBANK.NS (-₹19,267.09), TATASTEEL.NS (-₹18,859.40). This
CONFIRMS the raw-points finding above (net-negative at real
sample size) and makes it concrete in rupee terms - deploying
the full staged-capital plan's ₹1,00,000 per symbol on this
exact strategy across the real watchlist would have lost money
over the last 2 years, not made it. STILL NEEDS FOLLOW-UP (not
yet done): why does this contradict the document's own
repeated "proven" framing from earlier (smaller-sample) tests -
was that based on fewer symbols, a shorter window, different
exact parameters, or something about yfinance-vs-Fyers data
differing enough to matter. Do not treat the Daily-timeframe
Watchlist strategy as validated for real capital until this is
resolved. STCG tax (~20% on short-term equity gains) is NOT yet
included in this figure - user asked for it to be shown as a
separate after-tax column alongside pre-tax; strategy/
transaction_costs.py currently models only broker/exchange
charges, not capital-gains tax. Not yet built.

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

↓

TURION AI Trader v1.0

↓ (not yet defined in detail - see below)

v2.0 (a real "understanding" AI, not just weighted rules)

--------------------------------------------------

WHAT "v1.0" ACTUALLY MEANS (asked 07-Aug) - not a new technical
component, the checkpoint where every milestone above is not just
built but PROVEN: equity strategy net-negative finding resolved,
options strategies validated on real trades, Desktop Dashboard
committed, Live Trading built and successful through the Rs 10,000
-> Rs 1,00,000 staged plan, Algorithmic Trading running reliably
with guardrails for months (not days). Realistically many months
out from 07-Aug given Live Trading hasn't started and the equity
engines still need a real fix.

WHERE THE "AI" ALREADY IS (asked 07-Aug, since recent discussion
had drifted into pure execution/plumbing) - the AI Decision Engine +
Best Trade Engine already exist and run every real paper trade today
- they combine EMA/RSI/Structure/S-R/Candlestick/Volume + News
sentiment + Options chain data into one weighted score. This is the
"brain" already live. What's NOT built is real Machine Learning
("AI Intelligence: 70%, ML pending" in the Project Progress section
above) - the current brain runs on hand-picked, fixed weights, not
a model that learns.

v2.0 VISION (asked 07-Aug, explicitly NOT started, not even
designed in detail - just captured so the idea isn't lost): replace/
augment the rule-based brain with a genuinely "understanding" AI -
- Read news articles in FULL and reason about them (the current
  News Engine only does free-RSS keyword sentiment counting - "how
  many positive vs negative words" - not real comprehension).
- Synthesize price action + news + options data + macro context
  holistically (an LLM reasoning across all of it together) instead
  of separate hand-weighted scores bolted together.
- Learn from the system's OWN past trade outcomes and adjust its
  own rules over time, instead of the user manually re-tuning
  parameters by hand (like tonight's Target/Stop-Loss retuning).
- Possibly: explain its own reasoning in plain language on request
  ("why did you take this trade") instead of just a fixed log line.
Most likely approach if pursued: an LLM (e.g. Claude via API) doing
the news-reading/synthesis work, called at decision points (not
continuously - real per-call cost). Real, unbudgeted recurring cost
if built - needs its own scoping/cost discussion before starting,
same as the VPS+Firebase live-data plan above.

v3.0 and beyond: NOT defined, and deliberately not speculated on
further (asked 07-Aug) - each stage should inform the next one's
real design, and even v1.0 is many months out. Revisit only once
v1.0/v2.0 are real, not before.

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

HOW MANY MORE DAYS OF PAPER TRADING (asked 06/07-Aug): no single
fixed number - gated on trade COUNT per the rule above, not the
calendar, and today's real findings push this out further than the
original "one more month" plan assumed:

- The two ORIGINAL equity engines (Swing/Watchlist and Intraday/
  Best Trade) are now BOTH confirmed net-negative at real scale on
  real Fyers data (Swing: -Rs 1,28,490.80 across 49 symbols, only
  18 profitable; Intraday: -31,200.17 points across 48 symbols,
  ZERO profitable) - see 06-Aug's Known Issues entries. Real capital
  should NOT move forward on these two as currently tuned,
  independent of how many calendar days pass - either a fix/re-tune
  is needed, or the symbol-selective/futures-based redirection
  already flagged as a next step.
- The ORIGINAL single options strategy also closed today net-
  negative (-Rs 3,128.35, 49 trades, 61.2% win rate but bad risk/
  reward) and has now been retired (superseded by simple_st1,
  archived - see below).
- The 4 NEW options strategies (simple_st1/st2/st3/st4) only went
  live 06-Aug and have zero real trades yet. simple_st1/st2/st3
  trade multiple times/day (like the original) so could reach a
  meaningful ~30-50 trade sample within 1-2 real trading weeks.
  st4 (one high-confidence trade/day, selective by design) will
  take much longer to reach the same sample size - possibly
  30-60 trading days, since it may not fire every single day.

Bottom line: real capital is realistically AT LEAST several weeks
out, and gated on the equity engines' unresolved net-negative
finding getting a real answer (not just more calendar time passing)
as much as on the new options strategies accumulating enough trades.

DECIDED, 06/07-Aug: give the equity engines (Swing/Watchlist and
Intraday/Best Trade) exactly ONE MORE WEEK of live running as
currently tuned, then review and either retune or change the
strategy - not indefinite further waiting. Review point: 1 week
from 07-Aug (~14-Aug) - check real trades accumulated that week
against the already-known net-negative large-sample finding (Swing
-Rs 1,28,490.80/49 symbols, Intraday -31,200.17pts/48 symbols, 0/48
profitable) and decide then, don't let this drift past that date
without a decision.

MAJOR FINDING, 07-Aug - the 4 new options strategies' FIRST real
trading day was a large, broad loss, not just simple_st1/st2/st3's
Target/Stop-Loss ratio being off:

  simple_st1 NIFTY:      47 trades, 42.5% win rate, -Rs 23,237.07
  simple_st1 BANKNIFTY:  23 trades, 39.1% win rate, -Rs 21,952.40
  st2 NIFTY:              49 trades, 28.6% win rate, -Rs 30,987.29
  st2 BANKNIFTY:          21 trades, 28.6% win rate,    -Rs 123.24
  st3 NIFTY:              24 trades, 45.8% win rate, -Rs 23,946.12
  st3 BANKNIFTY:          12 trades, 33.3% win rate, -Rs 19,018.45
  st4 NIFTY:               1 trade,   0% win rate,   -Rs 5,400.02
  st4 BANKNIFTY:           1 trade,   0% win rate,   -Rs 3,189.38
  TOTAL across all 8 books: approximately -Rs 1,27,854 in ONE day
  (on Rs 8,00,000 total deployed paper capital - roughly 16%).

Why this matters more than a ratio problem: simple_st1 (3%/3%),
st2 (5%/2%), st3 (5%/5%) all use DIFFERENT Target/Stop-Loss ratios
- if the ratio were the main issue, at least one should have looked
meaningfully better than the others. All three lost heavily instead
(st2 NIFTY worst at -Rs 30,987 despite its ratio being the one
nifty_options_backtest.py's sweep found "best" on Black-Scholes-
estimated data). This points to the shared RSI-momentum ENTRY
signal itself lacking real directional edge on real premiums -
consistent with 22-Jul's original finding that "Momentum(RSI)+VIX
had no reliable edge on NIFTY" (only BANKNIFTY showed one, and only
on the underlying's direction, never checked against real premium
economics until now). High trade frequency (up to 49 trades in one
session) meant real transaction costs compounded quickly on top of
that.

DECIDED, 07-Aug: NOT stopping the 4 strategies early despite this -
continuing the already-agreed 1-week test as planned. IN PARALLEL,
build additional new strategy ideas (starting tomorrow, 08-Aug) with
genuinely different entry logic - not more Target/Stop-Loss ratio
variations on the same RSI-momentum signal, since today's result
suggests that entry signal itself is the real problem, not the exit
tuning.

GAP-FILL STRATEGY BUILT, 07/08-Aug - the first "different entry
signal" strategy promised right after the finding above. Added as a
5th named strategy (10th/11th book pair: reports/fyers_options_
gapfill_nifty_portfolio.json, fyers_options_gapfill_banknifty_
portfolio.json), its own Rs 1,00,000 x 2 indices, wired into
strategy/options_strategies.py's ALL_STRATEGIES and the app's
Options tab like the other 4.

Entry logic (strategy/fyers_options_gapfill.py) is genuinely
different from simple_st1/st2/st3 (RSI-momentum) and st4 (multi-
timeframe+ADX trend-continuation): bets that a significant open-vs-
previous-close gap REVERTS back toward the previous close during the
day, instead of continuing. Gap up -> buy PE (bet on reversion
down); gap down -> buy CE (bet on reversion up). Adapted from
strategy/gap_fill_backtest.py's exact rule (25-Jul research - the
ONE intraday candidate in this project's whole history that landed
net-positive after real transaction costs on NIFTY, +Rs 413.45/60d,
45% win rate - caveat: a split-window check found the edge
concentrated in the earlier half, not stable across the whole
window, so "promising", not "proven"). Target = previous close,
Stop-Loss = ATR-based on the side away from target, tracked on the
underlying's spot (not premium - same reasoning as st4, no reliable
per-contract premium history exists to compute levels directly).
Entry only allowed in an early-morning window (market open to
10:00 IST) - a gap-fill bet only makes sense taken early, by mid-
morning the day's real intraday action has already moved past the
at-open gap dynamics it counts on. One trade/day like st4. Tested
(tests/test_fyers_options_gapfill.py, all passing) before going
live. No trades yet as of 07-Aug (no qualifying gap that morning).

OPTIONS DATA VOLUME CHECK, 07-Aug - user asked how much real
options data exists. Two separate things:
- reports/options_premium_history.jsonl (raw option-chain snapshots,
  collected by strategy/fyers_options_collector.py): 5,808 records
  across 04-07-Aug, but very unevenly spread - 04-Aug (2 snapshots)
  and 05-Aug (4) are unusable, 06-Aug (32, uneven, some outside
  market hours) is thin, only 07-Aug (94 snapshots, ~4-5 min apart)
  has real density. Effectively 1 backtest-usable day exists so far.
- Actual live paper trades across all options books: 227 closed
  trades total (simple_st1/st2/st3/st4: 178 from 06/07-Aug combined
  + the retired original strategy's 49 frozen trades). Still far too
  few for a reliable per-strategy statistical read - consistent with
  the already-decided ~1-week review point.

07-AUG COARSE REPLAY (curiosity check, not a decision input) - user
asked to replay 07-Aug's first trade of each of the 6 simple_st1/
st2/st3 x NIFTY/BANKNIFTY books using ONLY the archived ~4-5 min
snapshots, instead of the live bots' continuous real-time quote
checks, to see how much the finer checking resolution actually
mattered. Result: exit reason (Target vs Stop-Loss) matched the
live outcome in 4/6 books, but FLIPPED in 2/6 (st2 BANKNIFTY: live
Target +Rs 6,234.81 vs coarse-replay Stop-Loss -Rs 2,238.37; st3
NIFTY: live Stop-Loss -Rs 5,750.16 vs coarse-replay Target +Rs
5,002.94) - a brief intraday spike/dip that the live bot's frequent
checking caught was invisible to the sparser archive, flipping the
outcome entirely in those 2 cases. Confirms the premium-history
archive is not reliable enough for a real backtest yet (too coarse,
one bad snapshot gap can invert a trade's result) - the right path
stays "keep collecting daily, revisit once several weeks of denser
data exist," not attempting a backtest on the current archive.

GITHUB CONNECTIVITY FAILURE (LOCAL MACHINE), 07-Aug - `git push`/
`git fetch` started failing with "Failed to connect to github.com:
443 ... Could not connect to server" mid-session, blocking the push
of the completed Gap-Fill commit. Diagnosed: DNS resolved fine
(20.207.73.82) but the TCP connection itself timed out; general
internet worked (google.com fine); switching networks (home WiFi ->
mobile hotspot) made no difference, ruling out an ISP-level block.
Root cause confirmed: local Windows Defender Firewall on this
specific machine. Toggling the Private-network firewall Off then
back On cleared whatever was blocking github.com specifically (both
`git fetch` and `git push` worked normally again with the firewall
back On afterward) - most likely a stale blocked-connection state/
cache rather than an active permanent rule, since it resolved itself
once toggled rather than needing an explicit allow-rule added. Noted
here in case it recurs - the fix is: temporarily turn off Windows
Defender Firewall (Private network, active profile) via Windows
Security > Firewall & network protection, retry, then turn it back
on immediately after.

DAILY PROFIT-LOCK ADDED, 08-Aug - after seeing st4's two trades (both
failed within 5-7 minutes) and simple_st1/st2/st3's high trade counts
(up to 49 in one day) on 07-Aug, user asked for every options
strategy to stop opening NEW trades for the rest of the day once
that day's already-REALIZED profit reaches Rs 2,000 - locks in a
good day instead of risking giving it back on a later trade.
Implemented as a shared helper (strategy/fyers_options_engine.py's
_today_realized_pnl(), summing Closed Trades' Net PnL whose Exit
Time falls on today's IST calendar day) plus one constant
(DAILY_PROFIT_LOCK_RS = 2000), reused by all 3 check_or_open
functions (the generic engine for simple_st1/st2/st3, fyers_options_
st4.py, fyers_options_gapfill.py) so the threshold only needs
changing in one place. Deliberately does NOT touch an already-open
position - that still runs to its own Target/Stop-Loss/Square-Off as
normal, only new entries are gated. For st4/gapfill (already one-
trade/day) this is a no-op today but kept for consistency if that
cap is ever relaxed. 9 new tests added (test_fyers_options_engine.py
- _today_realized_pnl sums only today's trades, ignores older ones,
zero when none), all 161 project tests passing.

THRESHOLD OPTIONS GROUP + APP SUMMARY TABLE, 08-Aug - after the daily
profit-lock was first added directly onto the 5 original strategies,
user asked to revert that (keep the originals exactly as they always
were) and instead run the SAME profit-lock as a completely SEPARATE
parallel group - "same strategy, but with the gate" - shown in its
own app tab, so the two can be compared side by side without touching
the already-running originals' books.

Implemented as a "threshold" variant of each of the 5 strategies
(strategy/options_strategies.py's THRESHOLD group: simple_st1_
threshold, st2_threshold, st3_threshold, st4_threshold, gapfill_
threshold, x2 indices = 10 more books, 20 total across the whole
options system now). Same entry/exit logic, own Rs 1,00,000 x2
indices each, own portfolio files - only daily_profit_lock=True
differs (make_strategy()/make_st4_config()/make_gapfill_config() all
gained a daily_profit_lock param, default False, so the originals are
provably unchanged). fyers_multi_strategy_options_run.py gained a
STRATEGY_NAME="threshold" group filter so all 10 threshold books run
off ONE cron-job.org trigger (not 5 more independently-pausable ones
like the originals - the user asked for one new tab/feature, not 5
more individually-pausable sub-strategies). 12 new tests (test_
options_strategies.py + additions to the engine/st4/gapfill test
files), all 173 project tests passing.

BUG FOUND + FIXED while wiring this up: .github/workflows/fyers_
multi_strategy_options.yml's commit step was missing `git add` lines
for the gapfill portfolio files entirely (added 07/08-Aug, never
added to this list) - meaning gapfill's real trade updates were being
computed correctly every run but silently discarded on the next
checkout, never actually persisted. Fixed, and the 10 new threshold
files added to the same list from the start so the same bug can't
repeat for them.

App changes: FyersMultiStrategyOptionsScreen (Options tab) made
generic (takes strategy names/descriptions as params instead of a
hardcoded list) so the new Threshold Options tab (fyers_threshold_
options_screen.dart) could reuse it instead of duplicating the whole
tab/list/portfolio-fetch UI. Also added 'gapfill' itself to the
Options tab's strategy list (it existed on the backend since 07/08-
Aug but was never wired into the app UI until now - found while
updating docs).

Also added, same day, at the user's direct request: a NEW "Options
Summary" tab (fyers_options_summary_screen.dart) - one combined table
across ALL 20 books (Options + Threshold Options), each row showing
Initial Amount (Rs 1,00,000, same for every book, hardcoded to match
every config's default), Current Amount (that book's "Cash" - i.e.
realized P&L basis, does NOT add an open position's unrealized mark-
to-market value, same convention the rest of the app already uses
for "Cash"), and Profit, plus a Total Investment / Total Current
Amount / Total Profit-Loss summary across all 20. App is now 9 tabs
(yfinance/Intraday/Swing/News/History/Fyers/Options/Threshold
Options/Options Summary) - up from 7 as of 06-Aug.

GPT STRATEGY LIST EVALUATED, 07/08-Aug - user pasted a ChatGPT-
sourced list of 5 strategy ideas (Market Structure+S/R+Candlestick+
Volume+Option Chain "Hybrid"; VWAP+EMA+Volume; Opening Range
Breakout; Option Chain+OI/PCR/Max Pain; ICT/Smart Money Concepts)
plus a "TURION Strategy v1.0" vision, asking for an evaluation
against this project's own already-tested candidates:
  1. Market Structure Hybrid - this IS essentially what the AI
     Decision Engine/Daily-Watchlist strategy already does (EMA+RSI+
     Structure+S/R+Candlestick+Volume) - not a new build, and that
     engine is currently net-negative live at large sample (-Rs
     1,28,490.80/49 symbols, 0/48 profitable).
  2. VWAP+EMA+Volume - CONCLUSIVELY REJECTED already, 22-Jul (48-
     combo ORB+VWAP+Volume sweep, every combo net-negative; separate
     EMA+Volume Breakout sweep also mostly negative).
  3. ORB - CONCLUSIVELY REJECTED, same 22-Jul sweep.
  4. Option Chain+OI/PCR/Max Pain - already built (Option Chain
     Engine) but SHELVED 30-Jul - NSE has no historical option-chain
     archive to backtest against. The Fyers real-premium snapshot
     collection started 04-Aug is a potential path around that exact
     blocker, but still too sparse as of 07-Aug (only ~1 usable day)
     - revisit in a few weeks once more data accumulates.
  5. ICT/Smart Money Concepts - the one genuinely untested idea on
     the list. Recommended waiting (6 existing options strategies
     still in their 1-week evaluation window), but user asked to
     build and backtest it anyway - see the entry directly below.

ICT/SMART MONEY CONCEPTS BUILT + BACKTESTED + REJECTED, 08-Aug -
built and tested per the user's explicit request above.

SCOPE: implemented the 4 concepts actually named - Liquidity (swing-
point detection), Break of Structure (BOS), Change of Character
(CHOCH), Order Blocks, Fair Value Gaps (FVG) - as pure, independently
tested functions (indicators/market_structure.py, 13 tests). NOT the
full ICT framework (no kill zones, premium/discount arrays, dealing
ranges - genuine ICT concepts but out of the scope actually asked
for). Entry rule (strategy/ict_smc_backtest.py): wait for a CHOCH ->
an Order Block or Fair Value Gap forms in the impulsive move right
after it -> enter when price retraces back into that zone, in the
CHOCH's direction. ATR-based Stop-Loss/Target (same convention as
every other backtest in this codebase, for an apples-to-apples
comparison against the already-rejected candidates rather than a new
R:R scheme invented just for this one). Analysis only, real
transaction costs via the existing cost model, no look-ahead (swings
only trusted once confirmed, zones only usable after the candle that
formed them). 16 tests (13 for the pure market-structure functions +
3 for the backtest wiring), 189 project tests total passing.

CONCLUSIVELY REJECTED, same day: swept 3 ATR SL/Target ratios (1.0/
1.5, 1.0/2.0, 1.5/2.0) x 2 swing-detection lookbacks (2, 3 candles)
across the SAME 8-symbol universe as the 22-Jul ORB/VWAP sweep
(NIFTY, BANKNIFTY, ICICIBANK, RELIANCE, HDFCBANK, TCS, BAJFINANCE,
TITAN; 5m candles, 60d) - 6 combos, 48 symbol-combo runs total. Every
single combo was net-negative in aggregate:

  SL 1.0/TGT 1.5, lookback 2: 845 trades, -Rs 12,683.84, 34.3% win rate
  SL 1.0/TGT 1.5, lookback 3: 662 trades, -Rs 8,833.00,  37.9% win rate
  SL 1.0/TGT 2.0, lookback 2: 836 trades, -Rs 12,183.70, 29.2% win rate
  SL 1.0/TGT 2.0, lookback 3: 659 trades, -Rs 8,795.84,  32.5% win rate
  SL 1.5/TGT 2.0, lookback 2: 811 trades, -Rs 10,650.59, 40.6% win rate
  SL 1.5/TGT 2.0, lookback 3: 655 trades, -Rs 8,488.65,  41.4% win rate

Every individual symbol was net-negative under every combo too, not
just the aggregate - BANKNIFTY was the worst (-Rs 5,357 to -Rs 8,427
depending on combo). Best-looking combo by win rate (SL 1.5/TGT 2.0,
lookback 3, 41.4%) is still deeply net-negative because the R:R
ratio needs a much higher win rate to break even (>42.9% at 1.5:2.0)
- consistent with the pattern already seen in this project's other
sweeps: a plausible-sounding multi-factor entry idea, still net-
negative once real transaction costs are applied to real price data.
5 for 5 now on the GPT strategy list: all evaluated, all either
already-rejected, shelved-on-data, or now freshly rejected. Code kept
in the repo (analysis-only, same convention as orb_vwap_backtest.py
etc.) as a documented, tested reference - not deleted.

CRON-JOB.ORG TRIGGERS FOR gapfill + threshold, 08-Aug - both had
their code live since earlier but NO cron-job.org trigger actually
calling them yet (found while reviewing the workflow's git-add bug).
User set up 2 more jobs by cloning an existing one and changing only
the `strategy` value in the POST body - "Gapfill Options Trigger"
(strategy":"gapfill") and "Threshold Options Trigger"
(strategy":"threshold"), both verified via real test runs (workflow_
dispatch logs confirmed correct STRATEGY_NAME and correct per-book
SKIPPED reasons - market/entry-window closed at test time, no
errors). 6 independent cron-job.org jobs now total: simple_st1, st2,
st3, st4, gapfill, threshold - all 20 books (Options + Threshold
Options) have live automation coverage as of today.

One real timing issue hit and understood during setup: a test run
fired ~50 seconds after triggering a fresh Fyers login still saw the
OLD/expired token, because the login workflow's own token-exchange-
and-secret-update step hadn't finished yet (pip install + OAuth
exchange took ~70-90s end to end) - not a bug, just needs a short
wait after login before the very next automated check picks up the
new token. Confirmed fine on the next test run once that time had
passed.

VIX FILTER STRATEGY BUILT + LIVE, 08-Aug - after a thorough "why is
everything failing" review (user asked for a 35-year-trader-style
diagnosis across all 11 tested approaches so far, all net-negative),
one concrete, evidence-based fix identified: 22-Jul's own Momentum
(RSI)+India VIX percentile-band finding was validated-but-never-
deployed (BANKNIFTY: 38/42 combos positive; NIFTY: rejected, only
9/42 positive) - the live options strategies (simple_st1/st2/st3) had
dropped the VIX filter and just used raw RSI. Built strategy/fyers_
options_vix_filter.py - BANKNIFTY ONLY (matching the validated
combo's own NIFTY rejection), RSI>60/<40 + India VIX inside its
trailing [30th,70th] percentile band (125x 15m candles = ~5 trading
days), ATR-based SL/Target on the underlying (1.5x/4.0x, the
validated combo's best parameters) - ports the exact 22-Jul finding
into real Fyers premiums for the first time (that finding only ever
measured directional accuracy on the underlying, no real premium
cost model existed then). Built as a NEW, separate strategy/book
(21st book total) rather than modifying simple_st1/st2/st3's
existing BANKNIFTY entries, to avoid contaminating their already-
running 1-week review. 6 new tests, 196 project tests passing.
7th cron-job.org trigger set up and verified live (workflow_dispatch
logs confirmed correct STRATEGY_NAME, no errors).

DECIDED, 08-Aug: loss-lock (mirror of the daily profit-lock - stop
new trades for the day after N consecutive Stop-Losses) and reducing
options trade frequency (a cooldown between entries) were both
identified as quick, cheap next steps in the same "why is everything
failing" review that led to the VIX-filter strategy - but user chose
to DEFER both until after the already-agreed 1-week review point
(~14-Aug), to let more real trades accumulate first rather than add
another gate on today's still-small sample. Not rejected, just
sequenced after more data exists - revisit at the 14-Aug review
alongside the equity-engine decision.

OI-FOOTPRINT STRATEGY BUILT + LIVE, 08-Aug - user's own idea, arising
from the "can we follow big institutions without them detecting us"
question: retail can never see real-time institutional order flow
(that data isn't published anywhere), but a real position being built
DOES leave a footprint in Open Interest - visible live via the option
chain this project already collects. Built strategy/fyers_options_oi_
footprint.py - adapts the classic OI+Price "buildup" framework
(normally applied to futures OI; adapted here to the ATM strike's
combined CE+PE OI since Fyers' chain doesn't expose futures OI
directly): Price up+OI up -> Long Buildup -> CE; Price down+OI up ->
Short Buildup -> PE; Price up+OI down -> Short Covering -> CE; Price
down+OI down -> Long Unwinding -> PE. Only fires on a >=5% combined-OI
change vs the last check (noise filter). Exit is deliberately small
and quick - fixed Rs 1,500 Target/Stop-Loss (rupee-based, not
percentage) per the user's own explicit design ("1k-2k profit, get
in and out", not a big directional bet). Both indices, 2 more books -
23 total across the whole options system now (10 original + 10
threshold + 1 vix_filter + 2 oi_footprint). 10 new tests, 207 project
tests passing. 8th cron-job.org trigger set up and verified live via
a real test run (no errors, correct STRATEGY_NAME).

APP CATCH-UP, 08-Aug - user asked "is this strategy in the app?" for
vix_filter and oi_footprint, and it wasn't - both had gone live on
the backend the same day but were never wired into the Options tab
(same class of gap as gapfill's earlier that same day). Fixed:
FyersMultiStrategyOptionsScreen's _strategyNames grew to all 7
(simple_st1/st2/st3/st4/gapfill/vix_filter/oi_footprint), and
_IndexTabs was generalized to take a per-strategy list of indices
(_strategyIndices map, default both) instead of hardcoding NIFTY+
BANKNIFTY for every tab - needed since vix_filter is BANKNIFTY-only
and showing an empty/error NIFTY subtab for it would have been
confusing. Options Summary's table also grew from 20 to 23 rows for
the same reason. APK rebuilt and reinstalled.

DECIDED, 08-Aug: oi_footprint stays OUTSIDE the Threshold group -
user explicitly declined adding a profit-lock variant for it (asked
directly, chose "no, keep it as is"). Reasoning matches oi_footprint's
own design: it's already a small, quick Rs 1,500 fixed Target/Stop-
Loss strategy (see its 08-Aug entry above) - a daily profit-lock on
top wasn't judged necessary. vix_filter also has no threshold variant
(never offered one). The Threshold group remains exactly the 5
original strategies' profit-lock variant, nothing more.

ARCHITECTURE PATTERNS, 08-Aug - user asked what design patterns exist
beyond check_or_open() (the polling pattern every strategy here
uses), for reference/decision-making going forward. Full list, what
each is, and where this project stands against it:

1. Polling / Check-based (WHAT WE USE) - check_or_open() is called
   periodically by an external trigger (cron-job.org), reads state
   from a JSON file, either manages an open position or looks for a
   new entry, always saves. Stateless between calls - all state lives
   in the file, not in memory - which is exactly why it works on
   GitHub Actions' ephemeral runners (no persistent process needed).
   Downside: a real price move between checks can be missed or
   overshot (already measured live - Target/SL overshoot by several
   points on the ~1-5 min cadence).

2. Event-driven / Reactive - react the INSTANT a price tick arrives
   instead of polling on a timer. Needs an always-on process (WebSocket
   listener on a VPS), not compatible with GitHub Actions. This is the
   same ground covered in the "milliseconds" discussion above -
   concluded NOT worth it for this project's holding-period style
   (minutes to hours), only matters for a fundamentally different
   strategy category (market-making/scalping) this project isn't
   pursuing.

3. Strategy Pattern (formal interface) - right now each strategy
   module just HAPPENS to define matching function names (_entry_
   signal, _check_position, check_or_open) by convention, not an
   enforced contract (no shared abstract base class/interface). A
   formal version would catch a missing/mismatched function at
   import time instead of at runtime. NOT built - convention has
   worked so far across 12 named strategies.

4. Centralized Risk Manager - Target/Stop-Loss/position-sizing/daily
   profit-lock logic currently lives INSIDE each strategy module
   separately (options_transaction_costs.py, DAILY_PROFIT_LOCK_RS are
   shared building blocks, but nothing routes every order through one
   common risk layer). A mature system has ONE risk layer every
   strategy's orders must pass through, enforcing rules across all of
   them at once. NOT built.

5. Portfolio-level Aggregation - the 23 options books are fully
   independent by design (for clean per-strategy comparison), so real
   CORRELATED exposure across strategies is invisible - e.g. if 6
   different strategies are all long BANKNIFTY CE at the same time,
   each looks like an independent small position, but the combined
   real risk is much larger than any one book shows. NOT built -
   DEFERRED to after the 14-Aug review (see below).

6. Shared Backtest-Live Engine - backtest scripts (strategy/*_
   backtest.py) and live strategy modules (strategy/fyers_options_*.py)
   duplicate the entry/exit logic separately by hand instead of
   sharing one engine that both backtesting AND live trading run
   through. Risk: the two can silently diverge - already happened
   once (nifty_options_backtest.py's Black-Scholes-estimated sweep
   showed +69%/57d, real-premium live results showed a large loss).
   NOT built - DEFERRED (see below).

DECIDED, 08-Aug: do NOT retrofit the 23 already-running books with
either #5 (Portfolio-level Aggregation) or #6 (shared Backtest-Live
Engine) right now - user chose to defer both until after the 14-Aug
review, same reasoning as the loss-lock/trade-frequency deferral
above (don't change code that's mid-way through accumulating real
trade data for a decision point). When #6 happens, it should apply to
NEW strategies going forward rather than rewriting the existing ones.
#2, #3, #4 were discussed but not explicitly scheduled - revisit if a
concrete need comes up (e.g. #4 becomes worth it once a premium-
selling/theta engine exists, since that needs real margin-aware risk
limits the current per-strategy approach doesn't provide).

GAPS VS A PROFESSIONAL ALGO TRADING SYSTEM, 08-Aug - user asked what's
missing compared to a real professional system, beyond the 6
architecture patterns above. Full list, then split by how soon each
is realistically actionable:

- Order Execution / OMS - no real order-placement code exists at all
  yet (paper only); single-broker (Fyers only, no redundancy); no
  pre-trade checks (margin availability, position limits) before an
  order would go out.
- Kill Switch - no global "stop everything now" mechanism across all
  23 books; only per-book profit-lock exists.
- Data depth - only candle-level data (15m/5m), not tick-by-tick; no
  automated data-quality validation (today's NaN corruption was
  caught by hand, not by a systematic check).
- Testing methodology - backtests use a single fixed historical
  window, no formal walk-forward (train/test split, rolled forward)
  discipline; the Threshold group is a crude A/B split, not a formal
  statistical A/B framework.
- Monitoring - no Sharpe ratio / Max Drawdown / Sortino ratio tracked
  anywhere, only raw rupee PnL; GitHub Actions run logs are the only
  log trail (ephemeral, hard to query historically).
- Capital allocation - every book gets an equal flat Rs 1,00,000
  regardless of performance; a real fund would allocate MORE to
  strategies that are working and less to ones that aren't.
- Compliance/Tax - STCG (~20%) after-tax column still not built
  (long-standing backlog item); no automated regulatory-limit
  checking.

SPLIT BY TIMELINE, 08-Aug:

QUICK (realistically doable ~1 week after the 14-Aug review, no new
infrastructure needed):
  - Kill Switch - one flag, checked at the top of every check_or_
    open(), same shape as the daily profit-lock gate already built.
  - Sharpe/Max Drawdown/Sortino tracking - pure calculation over
    Closed Trades data every book already has, no new data collection.
  - STCG tax column - narrow, self-contained, already backlogged.
  - Walk-forward testing discipline - a coding convention for NEW
    backtests going forward (train/test split), not a new system.
  - Data-quality validation on fetched quotes - same shape as the
    existing NaN guard in paper_trading.py, extended to more fields.
  - Basic pre-trade position-limit checks - a lighter first step
    toward the (deferred) centralized Risk Manager.

BIG (genuinely months of work, should NOT be rushed):
  - Real Order Execution/OMS - needs real broker order integration
    and extensive safety testing before ANY real capital is at risk.
  - Tick-level data storage - needs the VPS+WebSocket architecture
    already deferred under "LIVE-DATA ARCHITECTURE" below.
  - Multi-broker redundancy - not needed at current scale.
  - Dynamic capital allocation - circularly depends on having enough
    performance data to judge which strategies deserve more capital -
    i.e. depends on the 14-Aug review's own findings first.
  - Centralized Risk Manager - already flagged as a bigger, deferred
    architecture change (see ARCHITECTURE PATTERNS above).

3 CARRIED-OVER ITEMS CLOSED OUT, 08-Aug - user asked to finish the
remaining pending backlog from earlier sessions, same evening:

1. TATAMOTORS/LTIM Fyers symbols - FIXED. Root cause found by
   checking Fyers' own public symbol master files (NSE_CM.csv,
   NSE_FO.csv, both fetchable without auth): TATAMOTORS demerged into
   two listed entities (TMCV - Commercial Vehicles, TMPV - Passenger
   Vehicles) - only TMPV is F&O-eligible, so that's the one now
   mapped. LTIM (LTIMindtree) is listed on Fyers as "LTM" now, old
   ticker doesn't resolve. Both added as explicit overrides in
   strategy/fyers_data.py's symbol_to_fyers() (checked before the
   generic ".NS" rule), not changes to data/watchlist.py's shared
   symbol list. 7 new tests.

2. Real transaction-cost model + STCG tax - DONE for both live equity
   engines. strategy/paper_trading.py (Swing, multi-day delivery
   holds) gained a genuinely delivery-specific cost model (strategy/
   delivery_transaction_costs.py - STT on both sides not sell-only,
   DP charges, zero brokerage, different stamp duty rate from
   intraday) plus STCG (~20%) tax on gains, since delivery equity
   trades are actually subject to that tax. Cash now reflects real
   Net PnL; After-Tax PnL is a separate informational figure, not
   deducted from Cash (real tax is paid annually, not per-trade).
   strategy/best_trade_paper_trading.py (genuinely intraday) reuses
   the existing intraday cost model (transaction_costs.py) but
   deliberately shows NO STCG figure - intraday gains are speculative
   business income taxed at the trader's own income-slab rate in
   India, not the flat STCG rate, so no single number would be
   correct there. App's closed-trade detail view shows Cost/Net PnL/
   STCG Tax/After-Tax PnL when present. 10 new tests.

3. Desktop App packaged as .exe - DONE. desktop_app.py (PySide6
   dashboard) was already committed 14-Jul but never actually
   packaged - built and smoke-tested TURION_Desktop.exe (PyInstaller,
   --onefile --windowed, ~99MB) - launched cleanly, confirmed showing
   real live Watchlist/Paper Trading data via a screenshot. TURION_
   Desktop.spec (the reproducible build recipe) is tracked in git;
   build/ and dist/ (the actual .exe, too large for git history) are
   gitignored. Sent the built .exe directly to the user - run it from
   D:\TURION_AI_Trader (or copy it there first) since it reads
   reports/paper_portfolio.json via a relative path, same convention
   as every other script in this repo.

222 project tests passing after all 3.

169 GIT-CONFLICT FAILURES DIAGNOSED, 08-Aug - user reported "lots of
failure emails" for fyers_multi_strategy_options.yml. Checked via the
GitHub API: 169 total failed runs, ALL dated 07-Aug, ZERO on 08-Aug -
but 08-Aug is a Saturday (market closed, cron-job.org's weekday-only
schedules mostly weren't actually firing at real 1-min cadence today)
so "zero failures today" does NOT prove the underlying issue is
fixed - the real test is Monday's live cadence.

Root cause of the 169: a genuine REBASE CONTENT CONFLICT in reports/
fyers_candles.json specifically (confirmed in a failed run's log -
"CONFLICT (content): Merge conflict in reports/fyers_candles.json"),
not the simpler fast-forward-needed case the existing retry loop
already handled. Two overlapping runs both rewrote the whole file
fresh, so git's line-based merge couldn't reconcile them. Notably,
the failure recurred even with the per-strategy concurrency group
already in place (added 07-Aug morning, before these afternoon
failures) - the exact overlap source isn't fully pinned down (the
now-retired "Fyers Options Watch Trigger" workflow, active until
some point 06/07-Aug, is one candidate; not confirmed).

FIXED regardless of the exact mechanism: reports/fyers_candles.json
is a pure CACHE (fully regenerated fresh by every relevant run,
nothing authoritative lives only there), so a rebase conflict limited
to JUST that file is now auto-resolved by keeping whatever's already
on origin and continuing - this run's own candle data is superseded
again within ~1 minute regardless. A conflict touching any OTHER
(real trade-state) file still aborts and fails loudly, unchanged -
deliberately NOT a blanket "always take theirs" policy.

Tested by firing 2 near-simultaneous simple_st1 dispatches - both
succeeded, but the concurrency group serialized them cleanly (no
actual conflict arose), so the NEW conflict-resolution code path
itself wasn't exercised by this test. Real validation is Monday's
live 1-min cadence during actual market hours - watch for it.

Also found while reviewing cron-job.org's dashboard (same
investigation): a "Threshold Options Trigger (Copy)" - an unrenamed
duplicate of the Threshold trigger, pure redundancy (all 8 needed
strategy values already have their own dedicated job) - flagged to
the user to delete, since a leftover duplicate is exactly the kind of
same-strategy-overlap risk this whole investigation was about. Not
yet confirmed deleted - check at the next opportunity.

SPEED/INSTITUTIONAL-EDGE RESEARCH, 08/09-Aug - user's underlying
motivation behind the earlier latency questions came out explicitly:
wanted a strategy with small-but-fixed, near-guaranteed profit,
suspecting (correctly) that speed-based players genuinely do earn
consistently that way. Researched thoroughly (web search, real 2026
figures) before concluding none of this is a viable direction for
this project right now:

- Institutional vs retail latency: institutional colocation achieves
  <500 microseconds order round-trip; retail broker API is 50-500ms -
  roughly a 1,000x gap, and NSE is moving toward NANOSECOND latency
  (Apr-2026), so the gap is WIDENING, not closing.
- NSE colocation cost: Rs 5-15 lakh/month for a full rack. A cheaper
  "Colocation as a Service" (CaaS, via vendors like Greeksoft/Symphony
  Fintech) exists, but is restricted to registered NSE Trading
  Members only - not accessible to a retail client account.
- Becoming a broker/Trading Member ourselves: technically possible
  but requires Rs 75 lakh-1 crore minimum net worth (F&O segment),
  3-5 months SEBI registration, ongoing compliance burden - and
  STILL wouldn't include colocation for free (CaaS charged on top).
  Concluded not viable - "buying an airline for a window seat."
  User has real VLSI/hardware engineering background (can design
  FPGAs), which removes the TECHNICAL barrier but not the economic/
  regulatory one - confirms the real institutional edge is capital +
  regulatory access, not just engineering skill.
- Why institutional players profit despite ALL having high speed:
  most of it is NOT institution-vs-institution racing - it's market
  makers earning the bid-ask SPREAD from immediacy-seeking
  counterparties (retail market orders, pension-fund rebalancing
  flows) who aren't racing at all, plus better models/capital scale/
  diversification across many tiny edges. This is the SAME mechanism
  category as the already-built oi_footprint/planned theta-selling
  strategies - confirms that direction is sound.
- "Just be faster than OTHER RETAIL" (not institutions) - investigated
  and REJECTED: retail rarely trades time-sensitively against other
  retail; the counterparty on almost every retail order is already an
  institutional market maker (already faster than any retail-
  achievable speed), so a retail speed edge over other humans doesn't
  translate to profit against the actual counterparty.
- Real institutional arbitrage economics (Indian arbitrage mutual
  funds, actual disclosed 2026 returns): ~6-7% annualized net of all
  costs (8-9% in high-volatility months, 3-4% in calm ones) - this
  net-of-cost, "risk-free" return converges to roughly the risk-free
  rate, by definition (if it earned much more, capital would pour in
  until arbitraged away too) - even at institutional scale (Rs 80+
  crore), the PERCENTAGE return isn't special, only the absolute
  rupee amount is (scale, not edge quality).
- Tick-by-tick/millisecond HISTORICAL data: not available from Fyers
  at any price (their API's finest resolution is 1-minute candles);
  true tick data only from NSE directly (institutional pricing) or
  paid vendors (TrueData, Global Datafeeds, ~Rs 2,000-10,000+/month).
  LIVE tick data IS available via Fyers WebSocket (not yet built -
  same infra as the deferred Live-Data Architecture below) - storing
  it ourselves as an archive would be close to free once that's built
  (same connection, just also write to disk), but shouldn't be built
  as a separate project before then.
- Untouched-by-institutions small/micro-cap stocks: a REAL, valid
  space (institutions structurally can't take meaningful positions
  there - fund-size/mandate constraints, not an information gap) but
  requires a completely different skill set (fundamental/business
  analysis, not technical/quant signals) and carries real risks this
  project hasn't dealt with (fraud/pump-and-dump risk from less
  scrutiny, tight circuit filters trapping positions, thin liquidity
  moving price against your own order) - and critically, NO options
  exist on small/micro-caps (F&O only covers large liquid names), so
  the entire 23-book options infrastructure wouldn't apply at all.
  Would be a genuinely new, separate project, not an extension of
  what exists. Not pursued.

DECIDED, 09-Aug: stay focused on the current strategy set (23 books)
and the already-agreed direction (Option Chain/OI-footprint, theta-
selling once designed) - none of the speed/small-cap avenues explored
this session change that plan.

CREDIT-SPREAD (THETA) STRATEGY BUILT + LIVE, 09-Aug - the premium-
selling engine designed 08-Aug, built the next day per the user's
direct request. strategy/fyers_options_credit_spread.py - directional
credit spread (Bull Put / Bear Call, defined-risk, 2 legs: sell one
strike, buy a further one as protection), sold only when India VIX
sits in its own trailing HIGH percentile band (rich premium to sell
into - the OPPOSITE filter from vix_filter.py's "avoid extremes"
rule), direction from RSI (same signal simple_st1/st2/st3 already
use: >=50 -> sell PUT spread, <50 -> sell CALL spread). Short strike
~1.5% OTM, long strike 150 points further out (both rounded to the
index's strike step). Exit at 50% of credit banked (standard credit-
spread practice - don't hold for the riskiest last half), Stop-Loss
at 2x credit received, or square-off at day's close.

Position sizing uses the spread's own worst-case loss (width -
credit) as a conservative stand-in for real margin - Fyers does
expose a span_margin endpoint, but its exact request/response schema
wasn't confirmed from accessible docs, so rather than guess and
risk mis-sizing, this always sizes at or under what a real defined-
risk spread margin would allow. Real margin-API integration is a
future refinement, not a blocker.

Both indices, 25 books total now across the options system. 13 new
tests, 236 project tests passing. 9th cron-job.org trigger set up and
verified live (workflow_dispatch logs confirmed correct
STRATEGY_NAME, no code errors - token was expired since it's Sunday,
full live signal test happens once someone logs in on a trading day).

Known caveat, not yet verified: the user specifically wanted MONTHLY
expiry for both indices; this strategy uses whatever expiry Fyers'
option chain API returns by default (the nearest one, same as every
other strategy here) - untested whether that's monthly for NIFTY
(BANKNIFTY's only expiry is monthly already, discontinued weekly per
22-Jul's regulatory note). Check once real live entries occur.

APP CATCH-UP + REAL BUG CAUGHT, 09-Aug - added credit_spread to the
Options tab and Options Summary (same class of gap as vix_filter/oi_
footprint earlier - new backend strategy, app not updated with it).
While doing this, found a REAL crash-in-waiting: OptionPositionCard/
OptionClosedTradeCard (mobile_app/lib/widgets/common.dart) both
assumed every options position/trade is single-leg (reads Strike/
Entry Premium/Exit Premium directly, `as num` cast with no null
check) - credit_spread's genuinely different 2-leg shape (Short
Strike/Long Strike/Entry Credit, no "Entry Premium" key at all) would
have thrown a null-cast exception the FIRST time a spread position or
closed trade actually rendered in the app - caught before any real
data existed to trigger it. Fixed: both widgets now detect the shape
(presence of "Entry Credit") and render the appropriate fields. APK
rebuilt, not yet reinstalled (phone not connected at build time).

FUTURES SIGNAL BACKTEST - CONCLUSIVE FINDING, 09-Aug - user asked
whether Fyers has futures data (confirmed: NSE:NIFTY26AUGFUT, NSE:
BANKNIFTY26AUGFUT exist, verified against Fyers' own public symbol
master) and whether the RSI-momentum signal itself (used by simple_
st1/st2/st3) is any good, isolated from options-specific costs (theta
decay, IV changes) that have muddied every options-buying result so
far. Built strategy/futures_signal_backtest.py to test exactly this -
the SAME RSI>=50/<50 signal as a linear (futures-style) position
instead of an options premium purchase, so a loss can only mean the
signal itself is wrong, not an options-economics artifact.

CAVEAT: backtests against index SPOT price (not a real stitched
futures contract series - rollover stitching across monthly expiries
isn't built), same honest simplification strategy/momentum_vix_
backtest.py already used for the same reason. Futures track spot
closely (small cost-of-carry basis), so this is a reasonable proxy
for "would this signal have caught the same moves", not a claim of
exact real futures P&L.

RESULT: CONCLUSIVE - the signal loses on BOTH indices (60d, 5m):
  NIFTY:     193 trades, 37.31% win rate, Net PnL -Rs 77,360.39
  BANKNIFTY: 180 trades, 33.89% win rate, Net PnL -Rs 88,158.06
This CONFIRMS the RSI-momentum signal itself lacks real directional
edge - it is NOT just an options-premium/theta problem as might have
been hoped. Consistent with the original 22-Jul finding ("Momentum
(RSI)+VIX had no reliable edge on NIFTY") and now directly re-
confirmed on a completely different, linear instrument.

SAFETY DESIGN, verified working: user explicitly asked that no
strategy be allowed to put the account in a NEGATIVE position (real
risk with futures - unlike options-buying, a fast/gap move can in
theory cost MORE than the capital behind a futures position if the
Stop-Loss doesn't execute in time). Position sizing here is
deliberately NOT margin-based (which would allow far bigger
positions, per the ~12% margin figures already discussed) - it sizes
by a conservative WORST_CASE_MOVE_PCT (10%, matching historically
extreme single-day NIFTY moves) assumed INSTANT adverse move, so
capital can never go negative from one trade even if the Stop-Loss
completely failed. Also intraday-only (forced square-off before
close) - no position is ever held through an overnight gap at all,
the single biggest real source of this risk. Both backtest runs
confirmed "Capital Ever Negative: False" throughout.

New strategy/futures_transaction_costs.py models real F&O futures
costs (STT 0.02% sell-side on full notional, different stamp duty
rate from equity/options) - a third, genuinely different cost model
alongside the existing intraday-equity, delivery-equity, and options-
premium ones. 11 new tests, 247 project tests passing.

DECIDED, 09-Aug: NOT pursuing futures as a live strategy - the
underlying signal itself is now conclusively shown to lack edge on
two different instrument types (options premium AND linear futures/
spot), so switching instrument type wouldn't fix it. The diagnostic
question this was built to answer is answered - futures-as-a-vehicle
isn't the missing piece, a better SIGNAL is.

RSI+ADX>25 COMBO TESTED AT SCALE - NO IMPROVEMENT, 09-Aug - user
asked how to make the weak RSI signal stronger. Identified several
concrete options (RSI extremes instead of the noisy 50-midline, the
already-proven ADX>25 filter, RSI divergence, regime-awareness, the
already-built VIX filter) and tested the cheapest/already-validated
one first: added an optional ADX>25 filter to strategy/futures_
signal_backtest.py and re-ran the same 60d/5m comparison.

RESULT: no real improvement.
  NIFTY:     RSI-only 193 trades/37.31% win/-Rs 77,360 net
             RSI+ADX  136 trades/35.29% win/-Rs 79,377 net (worse)
  BANKNIFTY: RSI-only 180 trades/33.89% win/-Rs 88,158 net
             RSI+ADX  273 trades/35.53% win/-Rs 81,569 net (marginal)
This does NOT reproduce 22-Jul's "45%->83% win rate" ADX finding at
this scale/instrument - that earlier number likely came from a
smaller, more specific sample (already flagged with a caveat at the
time). Capital never went negative in any run (safety design held).

Also found and fixed a wrong test assumption while building this:
trade COUNT is not guaranteed to decrease when an entry filter gets
more selective - a held position blocks new entries, so a filter
that changes WHICH candles trigger entries can also change how long
positions stay open, changing total trade count in either direction
(confirmed on real BANKNIFTY data - MORE trades with the ADX filter
on, not fewer). Corrected the test rather than leaving a false
invariant asserted.

DECIDED, 09-Aug: ADX alone does not rescue the RSI signal. Next real
candidates to strengthen it (not yet tried at this scale): RSI
divergence (a less commonly-followed technique, may have more edge
precisely because it's less crowded), or accept the already-agreed
plan (VIX-filter, Option-Chain/OI-footprint, theta-selling) as the
more promising direction rather than continuing to patch the RSI
signal itself.

RSI DIVERGENCE TESTED - WORSE THAN PLAIN RSI, 09-Aug - the next
candidate from the "how to strengthen RSI" list, after ADX>25 showed
no improvement. Built indicators/divergence.py (is_bearish_divergence/
is_bullish_divergence, pure functions) and strategy/rsi_divergence_
backtest.py - detects when price makes a new swing high/low that RSI
does NOT confirm (reusing indicators/market_structure.py's swing-
point detection, already built for ICT/SMC), same safety design as
futures_signal_backtest.py (worst-case-move position sizing,
intraday-only square-off).

RESULT: WORSE than the plain RSI signal, not better.
  NIFTY:     109 trades, 32.11% win rate, Net PnL -Rs 63,730.30
             (plain RSI was 37.31% win / -Rs 77,360.39)
  BANKNIFTY:  70 trades, 24.29% win rate, Net PnL -Rs 80,402.66
             (plain RSI was 33.89% win / -Rs 88,158.06 - divergence's
             win rate is notably worse here)
Capital never went negative in either run (safety design held, same
as every prior test). 8 new tests, 256 project tests passing.

DECIDED, 09-Aug: RSI-family signals (plain threshold, +ADX filter,
divergence) are now THREE FOR THREE showing no real edge on this
project's real data, across two different instrument framings
(options premium AND linear futures/spot). Stop iterating on RSI
variants specifically - the already-agreed direction (VIX-filter,
Option-Chain/OI-footprint, theta-selling) remains the right place to
keep looking, not further patches to momentum/RSI-based signals.

DECIDED, 09-Aug (final word after the RSI/ADX/Divergence dead ends):
user explicitly confirmed - full focus stays on the 3 already-built,
already-live non-RSI-pattern directions (vix_filter, oi_footprint,
credit_spread/theta-selling - 5 books total) plus the existing 20
books (5 original + 5 threshold) already accumulating data. NO new
strategy experiments until the 14-Aug review point. This session's
RSI/ADX/Divergence detour is closed - documented as a real, useful
negative result (3 variants tested, all failed, ruling out an entire
signal family rather than leaving it an open question), not resumed
further.

==================================================

PCR MOMENTUM + VOLUME-WEIGHTED OI - BUILT, NOT DEPLOYED, 09-Aug -
right after confirming the "stay focused, no new experiments" decision
above, user asked a separate question: what NEW indicator could be
built that's genuinely strong, as R&D running in parallel, NOT a
change to the 14-Aug plan (explicitly confirmed via clarifying
question - this doesn't reopen the "stay focused" decision, it sits
alongside it).

4 candidate ideas were discussed (Chain-Wide PCR Momentum, Dynamic Max
Pain Drift, Volume-Weighted OI Buildup, VIX+OI combo). User asked for
a recommendation on combining them; the pick was PCR Momentum +
Volume-Weighted OI first (closely related, same option-chain data
source, natural pairing), keeping Max Pain Drift as a separate idea
for later, and only layering a VIX filter on top afterward if this
base combo shows promise.

SIGNAL (strategy/fyers_options_pcr_momentum.py): tracks the RATE OF
CHANGE of chain-wide Put-Call OI Ratio (total Put OI / total Call OI,
summed across the WHOLE collected option chain, not just the ATM
strike like oi_footprint.py) between checks, gated by a volume-
confirmation filter (current total chain volume must be at least
1.2x the last check's, so a PCR drift from thin/stale quotes doesn't
count). PCR rising fast + volume confirms -> bullish (CE); PCR
falling fast + volume confirms -> bearish (PE). MIN_PCR_CHANGE_PCT=5%,
MIN_VOLUME_RATIO=1.2, same Rs 1,500 fixed Target/Stop-Loss "get in,
get out" philosophy as oi_footprint.py. 9 new unit tests, all passing
(pure _classify_pcr_momentum() function, same testable-pure-logic
pattern as oi_footprint.py's _classify_buildup()). Full suite: 265
passed.

NOT BACKTESTED - same permanent limitation as oi_footprint.py and
every other OI-based signal in this project: no historical option-
chain OI/Volume dataset exists anywhere (not NSE, not Fyers, not this
project's own options_premium_history.jsonl archive, still too sparse)
to backtest against. Same workaround as oi_footprint took: pure logic
fully unit-tested, no historical backtest attempted.

DECIDED, 09-Aug: build and fully test the code, but do NOT deploy it.
Deliberately NOT added to strategy/options_strategies.py's
ALL_STRATEGIES list (unlike every other strategy in this project,
which gets added there as the final "go live" step) and NO cron-
job.org trigger created - stays fully built-and-tested but
disconnected from live automation until a deployment decision is made
at or after the 14-Aug review point.

==================================================

REAL BUG FOUND + FIXED, 10-Aug - user asked why credit_spread,
vix_filter, and gapfill had zero trades so far; checked live GitHub
Actions job logs directly (not just the portfolio JSON files) rather
than assuming. gapfill was fine - correctly SKIPPED, past its early-
morning gap-fill entry window each check, working as designed.

credit_spread and vix_filter were NOT fine: every single live check
since going live (08/09-Aug) failed with "Unsupported period '10d' -
add it to PERIOD_TO_DAYS" - both strategies call fyers_download(...,
period="10d", ...) for their RSI/VIX lookback (strategy/fyers_
options_vix_filter.py, strategy/fyers_options_credit_spread.py), but
strategy/fyers_data.py's PERIOD_TO_DAYS map never had a "10d" entry.
fyers_multi_strategy_options_run.py's per-strategy try/except silently
swallowed the error each time ("FAILED (continuing)") so it never
surfaced as a workflow failure email - both strategies have never once
evaluated an entry signal since being deployed. Fixed by adding
"10d": 10 to PERIOD_TO_DAYS. One regression test added (asserts the
key exists), full suite 266 passing. Real validation is the next live
check after this deploys - watch for credit_spread/vix_filter to
start producing HOLD/SKIPPED-for-real-reasons log lines instead of
FAILED.

Real validation caught a SECOND real bug in credit_spread, live,
minutes later: vix_filter started producing genuine "SKIPPED (no
RSI+VIX-band qualifying setup)" lines (fix confirmed working), but
credit_spread got past the RSI+VIX entry check and then failed with
"Could not find both spread legs in the option chain" - _fetch_
option_chain's default strike_count=5 (ATM +/- 5 strikes, fine for
every other strategy here since they only need the ATM leg) left both
the short leg (~1.5% OTM, ~7-9 strikes away) and the long leg
(width_points further still) outside the fetched chain. First fix
tried a fixed strike_count=15 - confirmed live moments later: NIFTY
opened its actual first real position ("HOLD (cost to close 2.4,
credit 2.2)"), but BANKNIFTY still failed (short 58400/long 58550 CE -
still out of range even at 15, a wider index needs more strikes for
the same % OTM). Rather than keep bumping a magic number, replaced it
with a dynamic fetch: one cheap call for spot, compute exactly how
many strikes away the long leg sits (new pure _strikes_needed()), and
re-fetch with that count + a small buffer if the default doesn't
already cover it - correct regardless of index, spot level, or width.
3 new tests, 269 passing overall.

==================================================

LIVE MONITORING FINDINGS, 10/11/12-Aug - no code changes these 3 days,
just checking real trading days as they accumulated (user asked
repeatedly which strategies hadn't traded yet + why, and to sanity-
check cron/login health) - two findings worth carrying into the
14-Aug review:

1. THRESHOLD GROUP'S PROFIT-LOCK HELPS ON NIFTY, NOT ON BANKNIFTY -
   checked trade-by-trade dates for simple_st1_threshold/st2_
   threshold/st3_threshold on both indices. On NIFTY, both real
   trading days so far (10-Aug, 11-Aug) show the SAME clean pattern:
   one early winning trade pushes today's profit past the Rs 2,000
   lock, and the strategy correctly stops for the day right after -
   real risk-management value, not a fluke (repeated 2/2 days). On
   BANKNIFTY, the opposite: the underlying RSI signal loses too often
   for cumulative profit to ever reach Rs 2,000 within a day (e.g.
   simple_st1_threshold/BANKNIFTY took 15 trades in ONE day on 10-Aug,
   lock never engaged), so threshold BANKNIFTY ends up trading almost
   as much as non-threshold and losing similarly - the profit-lock
   mechanism only protects gains, it does nothing for a signal that
   rarely wins early. CONCLUSION for 14-Aug: evaluate threshold's
   NIFTY and BANKNIFTY legs SEPARATELY, don't lump them into one
   verdict - and BANKNIFTY specifically needs a LOSS-lock (already on
   the 14-Aug list) or a signal change, not more time with the same
   profit-lock-only gate.

2. TRADE-FREQUENCY VARIES HUGELY BY STRATEGY - so "how many days until
   we can trust the win rate" is not one answer. Back-of-envelope
   rates from real data so far: simple_st1/st2/st3 (~24 trades/trading
   day) already have a large enough sample - their negative verdict is
   already reliable. oi_footprint (~4 trades/trading day) will reach a
   trustworthy ~30-trade sample within a few more days of the 14-Aug
   review, not by 14-Aug itself. vix_filter and credit_spread
   (~0.5-0.7 trades/trading day each - both gated on a rare double-
   condition entry) need roughly 30 MORE trading days (~6 weeks, into
   September) to reach even a rough 20-trade sample - 14-Aug is far
   too early to judge either one; they need their own, later review
   point instead of being bundled into the main 14-Aug decision.

==================================================

LIVE-DATA ARCHITECTURE (VPS + Firebase) - discussed in depth 06/07-
Aug, NOT built yet, deliberately deferred: do this about 1 WEEK
BEFORE starting real-capital trading (once paper-trading results
look good enough to actually proceed to Rs 10,000), not now - it's
real recurring cost and engineering effort with no benefit while
still validating strategies on the current ~1-5 min periodic-check
cadence.

Why: the current cron-based automation only checks Target/Stop-Loss
every ~1-5 min, so a real price crossing gets caught late - this
IS a real, measured problem (today's options trades routinely
overshot their nominal 2%/3%/5% thresholds by several points,
sometimes 2-4x, purely from checking too infrequently, not from
the strategy itself). A true live feed would fix this by checking
on every real price tick instead of on a timer.

Architecture agreed: Fyers WebSocket (live ticks) -> a small always-
on VPS (GitHub Actions can't hold a persistent connection - every
run is short-lived) runs the Target/SL/trailing logic on each tick
-> pushes the result to Firebase Realtime Database (already used in
this project for push notifications, no new account needed) -> the
Flutter app subscribes directly, no more periodic HTTP polling.

Region matters far more than which specific service: put the VPS
AND Firebase project in the SAME region as each other AND close to
Fyers (asia-south1 / Mumbai) - this is the single biggest latency
lever, not which specific messaging service is used.
- Different regions (VPS Mumbai, Firebase default US): ~450-650ms
  end-to-end.
- Same region (VPS + Firebase both asia-south1): ~50-135ms.
- Self-hosted MQTT (Mosquitto) ON the VPS instead of Firebase:
  ~20-75ms (VPS-to-broker hop becomes local/free, only one real
  network hop left) - genuinely faster, but CONCLUSION: not worth
  the extra security/reconnect-handling work (TLS via Let's
  Encrypt, Mosquitto's built-in auth, systemd auto-restart) - once
  the reaction time is already faster than the market's OWN tick
  rate (NIFTY/BANKNIFTY options don't update meaningfully faster
  than roughly every 200-500ms even when liquid), going faster
  still changes nothing about which price tick gets caught. The
  real, large win is "periodic (1-5 min) -> any live push" -
  Firebase already captures that whole win. Chasing Firebase-vs-
  self-hosted-MQTT's last ~50-80ms has ZERO measurable effect on
  real trade outcomes and isn't worth the added complexity.
  Managed MQTT clouds (HiveMQ Cloud, EMQX Cloud) were also
  considered and rejected for the same reason - they have the same
  two-hop topology as Firebase (VPS -> their broker -> app), so
  give Firebase-like latency without Firebase's simplicity
  advantage.

DECISION: Firebase (not self-hosted MQTT, not a managed MQTT
cloud) - same simplicity as what's already wired into this project,
same-region setup gets it fast enough that the last bit of possible
speed genuinely doesn't matter here.

Estimated cost: VPS ~Rs 400-600/month (a small India-region
instance - e.g. AWS Lightsail Mumbai), Firebase likely stays free
at this single-user scale. First real recurring cost this project
will have (everything so far is Rs 0).

Estimated build time: ~15-25 hours of focused work (VPS setup +
TLS/security if self-hosting is ever revisited + rewriting the
options/Swing/Intraday check logic from periodic-poll to event-
driven-on-tick + Flutter-side Firebase listener wiring + end-to-end
testing) - roughly 2-4 focused days, not a quick add-on.

TARGET DATES SET, 15-Aug - the user's own explicit calendar date,
checked against the trade-count gate before accepting it (not a pure
calendar decision made against the data-driven discipline elsewhere
in this doc):
  - VPS (Stage 2) MIGRATION TARGET: 10-Sep-2026. Sanity-checked
    against oi_footprint's real pace: 15-Aug -> 10-Sep is 26 calendar
    days / 19 trading days; at oi_footprint's real ~9 trades/day rate
    that's ~171 more trades on top of today's real 40 (31 NIFTY + 9
    BANKNIFTY) = ~211 by 10-Sep - well past the ~80-100 trade
    trustworthy-sample gate (which the pace alone would clear around
    22-25 Aug). 10-Sep is a genuinely safe date, not a premature one -
    it adds buffer on top of the data gate clearing, doesn't pull the
    decision earlier than the data supports.
  - CODE PREP START: 1-Sep-2026, deliberately BEFORE the VPS itself
    is provisioned. Reasoning: the WebSocket client, the event-driven
    rewrite of each strategy's check logic (paired with the Shared
    Backtest-Live Engine per that section above), and the Firebase
    push logic are all machine-agnostic - none of it needs an actual
    rented VPS to write or test, only to finally host 24/7. Starting
    9 days early (1-Sep) leaves real runway to build and debug before
    the 10-Sep cutover, instead of compressing all of that into a
    rush right at (or after) the target date. The VPS itself only
    gets provisioned at the end, to receive already-tested code, not
    as a prerequisite for writing it.

==================================================

REAL-CAPITAL ROADMAP - 4 STAGES, 13-Aug - user's own staged plan,
agreed after the threshold-group trade-by-trade analysis above
(discussing which strategies show real edge vs small-sample luck).
Each stage is CONDITIONAL on the previous one succeeding, deliberately
no fixed calendar dates attached - matches this whole project's
established "prove it with real data before proceeding" discipline
(same reasoning as the 14-Aug review, the VIX-filter/credit-spread
later-review-point, etc.):

1. CURRENT - 25-book paper trading on the existing periodic-check
   (~1-5 min poll) cadence, to find out which strategies have a real
   edge vs which don't. Review point 14-Aug for the strategies with
   enough sample by then (see the per-strategy trade-count/day
   estimates above); vix_filter/credit_spread need their own later
   point (~September pace).

2. VPS + FIREBASE LIVE-DATA ARCHITECTURE (see above) - build once a
   strategy is close to a trustworthy sample (oi_footprint is
   furthest along - see the trade-count section above), then run
   ONLY the strategies that already proved real edge in Stage 1
   (NOT all 25 books - no reason to re-test already-disproven RSI
   variants like st2/NIFTY, simple_st1/NIFTY, or the BANKNIFTY RSI
   legs) for another ~1 month of paper trading on the new event-driven
   (real-tick, near-zero overshoot) architecture - this re-validates
   whether the improved execution accuracy changes the realized
   Target/Stop-Loss ratios measured under the old polling cadence
   (see the "Overshoot" discussion - NIFTY st2_threshold's realized
   1.7:1 ratio vs its nominal 5%/2% config, for example).

3. REAL ORDER EXECUTION (OMS) + Rs 10,000 LIVE TEST - Stage 2 succeeding
   is the trigger, no fixed date. Real broker order-placement code does
   NOT exist anywhere in this project yet (paper-only so far, see GAPS
   VS A PROFESSIONAL ALGO TRADING SYSTEM above) - this is "genuinely
   months of work, should NOT be rushed" per that same list, needs to
   be built and safety-tested BEFORE any real order goes out. Once
   built, run with real Rs 10,000 for ~1 month as a small-scale live
   validation before committing more capital.

4. Rs 1,00,000 LIVE TRADING - only after Stage 3 succeeds.

Claude never executes a real trade itself at any stage - the final
action is always the user's, even once broker order-placement exists
(per this file's own DEVELOPMENT RULES, unchanged).

==================================================

STATISTICAL ANALYSIS ACROSS ALL 25 BOOKS, 13-Aug - user asked for
formal statistics beyond raw PnL (Expectancy, Sharpe, Max Drawdown,
Wilson Confidence Interval on win rate, and cross-strategy Correlation)
to be computed on real trade data and carried into the 14-Aug review.
No code changes - a one-off analysis script over the existing Closed
Trades data in each portfolio JSON, not wired into any live strategy.

EXPECTANCY (Win% x Avg Win + Loss% x Avg Loss, per trade) - the
fairest single ranking across books with very different trade counts,
since raw total PnL rewards high-frequency books regardless of per-
trade quality. Only 4 of 25 books have positive expectancy with real
trades: simple_st1_threshold/NIFTY (+Rs 2,852/trade, 10 trades),
oi_footprint/NIFTY (+Rs 2,036/trade, 27 trades), oi_footprint/
BANKNIFTY (+Rs 1,321/trade, 9 trades), st2_threshold/NIFTY (+Rs 907/
trade, 31 trades). Every other book with real trades is negative
expectancy.

WILSON SCORE CONFIDENCE INTERVAL (95%, on win rate) - formalizes the
"how many trades until we trust it" question already discussed
informally. simple_st1_threshold/NIFTY's raw 70% win rate has a genuine
95% CI of 40-89% (only 10 trades - still very wide, do not over-trust
the headline number). oi_footprint/NIFTY's CI is a tighter 41-75% (27
trades) - more trustworthy. st2_threshold/NIFTY's CI (29-62%, 31
trades) still straddles 50% - genuinely uncertain whether its edge is
real yet.

SHARPE RATIO (mean daily PnL / std dev of daily PnL, per book) -
oi_footprint/NIFTY has the best risk-adjusted score (2.69) among all
25 books - not just profitable, but SMOOTHLY profitable (low day-to-
day variance relative to its average). simple_st1_threshold/NIFTY and
st2_threshold/NIFTY both score 1.43 - solid but noisier than oi_
footprint/NIFTY. Every RSI-based book without threshold (st1/st2/st3/
st4 non-threshold) scores negative or near-zero Sharpe, consistent
with their already-established lack of edge.

MAX DRAWDOWN (largest peak-to-trough equity decline, trade-sequence
order) - confirms the capital-depletion finding from earlier the same
day in stark numbers: simple_st1/NIFTY, st2/NIFTY, st3/NIFTY (the
proven-weak base RSI books) show max drawdowns of Rs 94,000-114,000 on
a Rs 1,00,000 base - i.e. they lived through a near-total wipeout at
some point in their trade history, matching the near-zero Cash
balances already observed live.

CROSS-STRATEGY CORRELATION (daily PnL, Pearson) - the most actionable
NEW finding, directly answering the deferred "Portfolio-level
Aggregation" architecture question (see ARCHITECTURE PATTERNS above):
computed correlation between BANKNIFTY's RSI-based books' daily PnL.
simple_st1_threshold, st2_threshold, and st3_threshold on BANKNIFTY
are correlated 0.99-1.00 WITH EACH OTHER (essentially moving as one),
and 0.82-0.88 with their own non-threshold counterparts (simple_st1,
st2) - meaning these "3 independent Rs 1,00,000 books" are actually
one concentrated bet wearing 3 names, not real diversification. st3
(non-threshold BANKNIFTY) is the one outlier, correlated only 0.12-
0.18 with the others - its different 5%/5% symmetric exit ratio
genuinely decorrelates its day-to-day PnL pattern from the rest.
CONCLUSION: any future Portfolio-level Aggregation work (already
deferred to post-14-Aug) needs to account for this - several of the
25 "independent" books are not actually independent bets.

==================================================

SECOND STATISTICAL PASS - T-TEST, MONTE CARLO, AUTOCORRELATION,
13-Aug - user asked for a further round beyond the first pass above:
one-sample t-test (is a book's average PnL/trade statistically
distinguishable from zero, not just positive by luck), Monte Carlo
simulation (reshuffle each book's own real trades 5,000 times to see
the FULL range of possible outcomes, not just the one order that
actually happened), and lag-1 autocorrelation (does a loss tend to be
followed by another loss). Same one-off analysis script pattern, no
live-strategy code changes. Books with fewer than 3 trades were
skipped (t-test/Monte Carlo need a minimum sample to mean anything).

T-TEST RESULTS - 3 books are now STATISTICALLY CONFIRMED negative
(p<0.05, not just "looks bad on average" but distinguishable from
zero given their own variance): st2/NIFTY (p=0.008), simple_st1_
threshold/BANKNIFTY (p=0.044), st4/NIFTY (p=0.002, though only 4
trades - weak sample despite the low p-value). simple_st1/NIFTY
(p=0.054) and simple_st1/BANKNIFTY (p=0.057) are borderline-negative,
just short of the formal 0.05 cutoff but pointing the same direction
as their already-large, already-damning sample sizes. Notably,
oi_footprint/NIFTY (p=0.069) - the system's best-performing book - is
ALSO not yet formally significant, because per-trade PnL variance is
naturally large relative to the mean; it needs more trades before its
edge is airtight by this stricter test, even though Sharpe/Expectancy/
CI already look good.

MONTE CARLO "RUIN RISK" - the standout new finding, extending the
Kelly-sizing discussion earlier with actual data instead of 2 hand-
picked example sequences. Reshuffling each book's own real trades
5,000 times (same trades, random order) under the CURRENT ~100%-cash-
per-trade sizing:
  st2/NIFTY:        39.5% of random orderings hit zero/negative capital
  simple_st1/NIFTY: 24.3% of random orderings hit zero/negative capital
  st3/NIFTY:         17.9% of random orderings hit zero/negative capital
  oi_footprint (both) + all promising threshold-NIFTY books: 0.0% -
    capital never wiped out in ANY of the 5,000 reshuffled orderings.
This CONFIRMS the near-empty Cash balances already observed live for
st2/NIFTY (Rs 5,134 left) and simple_st1/NIFTY (Rs 11,033 left) were
not a fluke of the one historical order they happened to trade in - it
is a structural property of their negative win/loss distribution under
the current sizing, regardless of order. Directly strengthens the
"position-sizing tricks can't fix a broken signal, but a real signal
doesn't need aggressive sizing to survive" point already established
in the real-capital roadmap discussion.

AUTOCORRELATION (lag-1, does a loss predict the next trade's outcome)
- mostly weak/near-zero across the system, no strong universal
"losing streaks breed more losses" pattern to justify a one-size-fits-
all loss-lock threshold. Two notable exceptions: oi_footprint/
BANKNIFTY (-0.45) and st3/BANKNIFTY (-0.36) - a loss tends to be
followed by a BETTER outcome, not a worse one, for these two
specifically. If a future loss-lock is built (already on the 14-Aug
list), this suggests it should be tuned per-strategy from each book's
own autocorrelation, not a single blanket rule across all 25.

==================================================

WALK-FORWARD / SPLIT-SAMPLE TEST, 13-Aug - user asked directly whether
this (flagged earlier as a "quick win" methodology, needs ~20+ trades
per book to be meaningful) had actually been run. It hadn't - run now.
Each book with >=10 trades split into first-half vs second-half (by
trade order) and compared for consistency, same one-off script
pattern, no live-strategy changes. Books under 10 trades skipped (12
books qualified).

RESULT - st3_threshold/NIFTY's earlier informal "faded" observation
(100%-win/+15% on 2 trades -> 50%-win/+1% on 26 trades, noted earlier
same day) is now CONFIRMED by the formal split test too: first half
+Rs 154/trade (50% win), second half -Rs 2,025/trade (31.2% win) - a
genuine sign flip, not a stable edge. DECISION: st3_threshold/NIFTY
should be dropped from further consideration, not just "watched
longer" - its apparent edge has already been shown twice now (informal
growing-sample check, formal split-sample check) not to hold up.

A second, more cautionary finding: oi_footprint/NIFTY - the system's
best performer by every other metric (Expectancy, Sharpe, 0% Monte
Carlo ruin risk) - ALSO shows real fade across the split: first half
+Rs 3,803/trade at 69.2% win, second half +Rs 396/trade at exactly
50.0% win. Still consistent-positive in both halves (unlike st3_
threshold/NIFTY), so not a red flag on its own, but a clear signal to
keep watching closely rather than treat it as settled - "best
performer so far" is not the same as "edge confirmed durable."

Books that held up well across the split (second half as good as or
better than the first, not just "still positive"): simple_st1_
threshold/NIFTY (+Rs 3,441 -> +Rs 2,264/trade) and st2_threshold/NIFTY
(+Rs 462 -> +Rs 1,324/trade) - genuinely the most trustworthy positive
books in the system by this test. st2/BANKNIFTY flipped from negative
to barely positive (-Rs 469 -> +Rs 57/trade) - too close to zero to
call an improvement yet. Every other book tested negative in BOTH
halves - already-known verdicts, reconfirmed, no surprises.

==================================================

THIRD STATISTICAL PASS - INSTITUTIONAL-STYLE METRICS, 13-Aug - user
asked what "extremely accurate" formulas big hedge funds/institutions
use. Answered honestly first: no formula predicts markets accurately -
institutional tools are about RISK MANAGEMENT and PORTFOLIO
CONSTRUCTION, not prediction (consistent with this whole project's
repeated finding that pattern-prediction signals don't hold up).
Computed the genuinely applicable ones on real data: VaR/CVaR, Calmar
Ratio, Risk-Parity (inverse-volatility) position weights, and a rough
holding-duration proxy for options Greeks (true Delta/Theta/Vega
decomposition is NOT possible from current data - Closed Trades store
Entry Spot but not Exit Spot, and no implied volatility is stored, so
premium change can't be split into direction-driven vs time-driven
components; flagged as a future data-collection improvement, not
attempted with unsupported assumptions).

CALMAR RATIO (total return % / max drawdown %) - oi_footprint/
BANKNIFTY (5.23) and oi_footprint/NIFTY (4.46) are far ahead of
everything else, consistent with their already-strong Sharpe/
Expectancy standing. Every RSI-based book without a proven edge scores
negative.

VaR 95% / CVaR 95% (worst ~5% of trading days, daily PnL) - oi_
footprint (both) and the promising threshold-NIFTY books show
POSITIVE VaR95 (Rs +2,000 to +7,700) - i.e. even their bad days were
historically often still profitable. Every proven-weak book shows
large negative VaR95 (Rs -19,000 to -52,000 on a bad day). CAVEAT:
daily sample sizes are still small enough that VaR95 and CVaR95 came
out numerically identical for most books (the "5th percentile" calc
just lands on the single worst day recorded) - this will sharpen once
more trading days accumulate, not yet a fully robust institutional-
grade VaR.

RISK-PARITY WEIGHTS (inverse daily-volatility, illustrative only - NOT
implemented in any live strategy) - shows what capital allocation
would look like if sized by each book's own risk instead of the
current flat Rs 1,00,000 each: oi_footprint/BANKNIFTY would get the
most (15.6% of a pooled Rs 25L), st3_threshold/NIFTY the least (2.3%,
both because of its high volatility and its already-confirmed faded
edge). Directly illustrates the already-flagged "Capital allocation"
gap vs a professional system (see GAPS VS A PROFESSIONAL ALGO TRADING
SYSTEM above) - not built, just quantified for future reference.

HOLDING DURATION (win vs loss average, rough theta-decay proxy) - no
clean universal pattern found (some books show losses held LONGER
than wins - consistent with a time-decay drag; others show the
opposite) - genuinely inconclusive with current data, do not over-
read this proxy. A real answer needs Exit Spot + implied volatility
stored per trade going forward.

==================================================

EXIT SPOT + IV/GREEKS INFRASTRUCTURE, 13-Aug - direct follow-up to the
holding-duration proxy's honest limitation above: user asked to start
actually collecting what a real Delta/Theta decomposition needs.

1. EXIT SPOT now saved on every closed trade, across all 7 strategy
   engines (generic/simple_st1-st3, st4, gapfill, vix_filter, oi_
   footprint, credit_spread, pcr_momentum) - alongside the already-
   stored Entry Spot. 4 engines already fetched the underlying's spot
   at check time for their own Target/SL logic and just needed it
   threaded through to _close_position(); oi_footprint, credit_spread,
   and pcr_momentum needed one new quote call added. 269 tests still
   passing. This data only starts accumulating from this commit
   forward - trades before 13-Aug won't have it.

2. IMPLIED VOLATILITY SOLVER + GREEKS built (indicators/black_
   scholes.py, extending the existing black_scholes_price() from
   03-Aug's options backtest work rather than duplicating it) -
   confirmed first that Fyers' option-chain API does NOT return IV
   directly (Fyers' own community forum has open, unanswered requests
   for this), so implied_volatility() backs it out from a real traded
   premium via bisection search on black_scholes_price(), and black_
   scholes_greeks() computes Delta/Theta/Vega at that IV. Pure,
   fully-tested (round-trip IV recovery for both CE/PE, boundary cases,
   Greeks sign checks) - 9 new tests, 278 passing overall.

NOT YET WIRED INTO LIVE ANALYSIS - computing a real trade's Theta/
Delta split needs its time-to-expiry, which isn't stored anywhere yet.
Fyers option symbols encode expiry in TWO different formats (weekly:
numeric YY+M+DD, e.g. NIFTY2681124600PE; monthly: YY+3-letter-month,
e.g. BANKNIFTY26AUG58000CE, since BANKNIFTY dropped weekly expiries in
2023) - parsing this reliably is real, separate work, deliberately not
rushed with unverified assumptions. Next step once Exit Spot data has
accumulated: build the expiry parser, then a one-off analysis script
(same pattern as the statistical passes above) to actually compute
each closed trade's Theta contribution.

EXPIRY PARSER BUILT SAME DAY - strategy/fyers_data.py now has parse_
option_expiry() (handles both formats above, confirmed against real
observed trade symbols, not guessed) and time_to_expiry_years(). The
monthly-format branch computes the LAST TUESDAY of the given month -
verified NSE moved monthly index-derivatives expiry from Thursday to
Tuesday effective 01-Sep-2025 (current convention, not the older
Thursday one). 8 new tests (including real symbols like NSE:NIFTY2681
124600PE -> 2026-08-11, NSE:BANKNIFTY26AUG57200CE -> 2026-08-25, and
the O/N/D month-code edge case for Oct/Nov/Dec), 286 passing overall.

REMAINING GAP - all 3 pieces (Exit Spot storage, IV solver/Greeks,
expiry parser) now exist, but Exit Spot only started accumulating from
the commit that added it (13-Aug) - trades before that have no Exit
Spot, so a real Theta/Delta analysis needs to wait for enough NEW
trades to build up first (same "wait for real data" discipline as
everything else in this project). Next step once there's a reasonable
number: a one-off analysis script (same pattern as the statistical
passes above) combining Exit Spot + parse_option_expiry() + implied_
volatility() to actually compute each closed trade's real Theta
contribution.

==================================================

DYNAMIC MAX PAIN DRIFT BUILT + NOT DEPLOYED, 13-Aug - the 4th and
last of the novel-indicator ideas from 09-Aug (see pcr_momentum.py's
module docstring for the shared background), built now on the user's
request. strategy/fyers_options_max_pain_drift.py:

MAX PAIN - the strike where option WRITERS (mostly institutions) owe
the least aggregate payout at expiry (i.e. where the most combined
CE+PE OI would expire worthless). The debated theory: as expiry
nears, large sellers' own hedging tends to pull the underlying toward
this strike. Rather than trade toward the CURRENT Max Pain level (a
static read), this tracks how the Max Pain strike itself DRIFTS
between checks - same "watch the change, not the snapshot"
philosophy already validated by oi_footprint (OI buildup direction)
and pcr_momentum (PCR rate of change): drifting up -> CE, down -> PE.

EXPIRY-PROXIMITY GATE - the user's own explicit refinement, raised
directly ("expiry day लाच जास्त फायदा होतो का"): the pull-toward-Max-
Pain effect, if real at all, should be strongest right before
settlement and weakest far from it. Rather than trust the drift
signal every day, it only fires within MAX_DAYS_TO_EXPIRY (2 days) of
the option's own expiry - made possible by the SAME-DAY expiry parser
(strategy/fyers_data.py's parse_option_expiry()/time_to_expiry_years())
built earlier for the Theta/Delta work above. A nice example of one
piece of infrastructure (built for one purpose) immediately enabling
a second, unrelated feature.

Same "built, not deployed" precedent as pcr_momentum.py: pure, fully
unit-tested logic (13 new tests, 299 passing overall) - no historical
backtest possible (no historical option-chain OI dataset exists
anywhere, the same permanent limitation this project keeps running
into). Deliberately NOT added to options_strategies.py's
ALL_STRATEGIES and no cron-job.org trigger created - stays fully
built-and-tested but disconnected from live automation until a
deployment decision at/after the 14-Aug review point, same as pcr_
momentum.

With this, all 4 of 09-Aug's novel-indicator ideas are now either live
(oi_footprint - the strongest performer in the whole system) or built-
and-waiting (pcr_momentum, max_pain_drift). Volume-Weighted OI
Buildup, the 4th idea, was folded into pcr_momentum's design at the
time (see pcr_momentum.py's docstring) rather than built separately.

==================================================

PCR_MOMENTUM + MAX_PAIN_DRIFT DEPLOYED, 13-Aug - both went live the
same day they were built, on the user's direct request: their earlier
"built, not deployed, pending 14-Aug" holding pattern only made sense
if deploying carried some cost or contamination risk. Since this is
paper trading (zero real-money risk) and each is its own separate
book, neither touches the other 25 books' ongoing comparison - the
user pointed out there's no real reason to wait on the calendar when
waiting costs nothing and the sooner they trade, the sooner there's
real data.

books count: 25 -> 29 (options_strategies.py's ALL_STRATEGIES). No
threshold variant for either - same reasoning as oi_footprint/vix_
filter/credit_spread (already a small, quick fixed-Rs-1,500-Target/
Stop-Loss design, a daily profit-lock on top wasn't judged necessary,
confirmed with the user directly before proceeding).

Also wired into the mobile app (Options tab + Options Summary),
.gitignore (portfolio-file allow-rules), and the GitHub Actions
workflow (strategy input description + git add lines) - same catch-up
checklist every new strategy has needed this whole project. 301 tests
passing (2 new, for the book-count/standalone-list changes).

STILL NEEDED: 2 new cron-job.org triggers (STRATEGY_NAME=pcr_momentum,
STRATEGY_NAME=max_pain_drift) - can't be created via API (no access),
needs the user's own manual step (clone an existing job, same as every
prior strategy's trigger setup) before either actually starts firing.

==================================================

PCR_VIX_COMBO BUILT + DEPLOYED SAME DAY, 13-Aug - the 4th and last of
09-Aug's novel-indicator ideas (VIX+OI combo), built AND deployed
same-day rather than held back, on the user's own reasoning: no
benefit to waiting for pcr_momentum's own review before also
collecting real data on this combo in parallel - paper trading carries
zero real-money risk, and it's its own separate book that doesn't
touch anything else's comparison.

strategy/fyers_options_pcr_vix_combo.py reuses pcr_momentum's chain-
reading/classification logic UNCHANGED (imported, not duplicated) and
adds ONE more condition: only trust the PCR-momentum drift signal when
India VIX sits inside its own trailing [30th,70th] percentile band -
the exact same validated condition fyers_options_vix_filter.py uses
for RSI-momentum, applied here to an OI-based signal instead.

Wired into ALL_STRATEGIES (books: 29 -> 31), mobile app, .gitignore,
GitHub Actions workflow - same checklist as every prior strategy. 3
new tests (config-maker only, matching vix_filter's own precedent of
not unit-testing network-dependent entry logic), 305 passing overall.

With this, all 4 of 09-Aug's novel-indicator ideas are now live:
oi_footprint (proven, strongest performer), pcr_momentum, max_pain_
drift, and pcr_vix_combo (all 3 just deployed 13-Aug, real data still
to come). Still needs its own cron-job.org trigger (STRATEGY_NAME=
pcr_vix_combo) - the user's own manual step, can't be created via API.

==================================================

FOURTH STATISTICAL PASS - MARKET-DIRECTION BIAS, SORTINO, ULCER INDEX,
PROFIT FACTOR, ANNUALIZED SHARPE, 13-Aug - user asked what "extremely
accurate" institutional formulas exist beyond the first 3 passes; this
round specifically targets a question none of the earlier passes
answered: is a book's good result really independent signal skill, or
a hidden directional bet that happened to ride a favorable market move?

MARKET-DIRECTION BIAS (correlation between each book's daily PnL and
its own index's daily % return, using real NIFTY/BANKNIFTY daily
closes) - the standout finding: oi_footprint/BANKNIFTY (Rs +11,891,
previously this system's 2nd-best book) is 0.82 correlated with
BANKNIFTY's own daily direction - a real caution that a meaningful
part of its result may be "BANKNIFTY happened to trend favorably this
week" rather than pure OI-signal skill. By contrast oi_footprint/
NIFTY (-0.16) and simple_st1_threshold/NIFTY (0.02) show near-zero
market correlation - genuinely direction-independent, more trustworthy
by this specific test. CONCLUSION: oi_footprint/BANKNIFTY needs to be
watched specifically for whether it still performs if/when BANKNIFTY's
own trend reverses, not just judged on total PnL - not disqualifying,
but a real asterisk on an otherwise-strong book.

SORTINO RATIO (downside-deviation-only risk) - the 4 already-known-good
books (oi_footprint both, simple_st1_threshold/NIFTY, st2_threshold/
NIFTY) are literally undefined (n/a) because NONE of their trading
days have been net-negative yet - a genuinely strong signal in its own
right, though a small-sample one. Every proven-weak book scores
consistently negative (-0.29 to -0.76).

ULCER INDEX (drawdown depth AND duration, not just the single worst
point like Max Drawdown) - same 4 good books score 1.15-8.41 (low/
good), every weak book scores 19-52 (high/bad) - a wide, clean
separation, reconfirming the same grouping via a genuinely different
lens (sustained pain, not just the worst single moment).

PROFIT FACTOR (gross profit / gross loss) - the 4 good books score
1.41-3.01 (all >1, profitable), every weak book scores 0.47-0.89 (all
<1, structurally losing) - clean, simple confirmation.

ANNUALIZED SHARPE (daily Sharpe x sqrt(252)) - the 4 good books show
14-43, the weak books -4 to -16. CAVEAT stated explicitly: these are
annualized from only ~4-5 real trading days of daily-PnL history, so
the sqrt(252) scaling amplifies noise heavily - the DIRECTION (good
books positive and high, weak books negative) is meaningful, but the
exact magnitude (e.g. "42") should not be read as literally comparable
to real fund Sharpe ratios yet - needs many more trading days before
the annualized number itself is trustworthy.

==================================================

HOW ALL THESE STATISTICAL TOOLS GET USED GOING FORWARD - user asked
directly, since by this point ~15 different formulas/tests have been
computed across 4 analysis passes. Organized by actual project
decision point (not just "we ran the numbers once"):

1. SCREENING / RANKING books (ongoing, re-run periodically e.g. at
   14-Aug and later review points) - Expectancy, Profit Factor, Sharpe/
   Sortino/Calmar together form the primary "is this book good"
   scorecard. A book needs to look good across MULTIPLE of these, not
   just one, before being trusted (oi_footprint/BANKNIFTY looking good
   on Sharpe/Ulcer/Profit-Factor but flagged on market-correlation is
   exactly why - one strong metric alone isn't enough).

2. STATISTICAL CONFIDENCE GATING (deciding when a sample is big enough
   to act on, e.g. before Stage 2 VPS migration or Stage 3 real
   capital) - Wilson 95% Confidence Interval on win rate + the one-
   sample t-test on Expectancy formalize "how many trades is enough"
   instead of a rule-of-thumb "30-50 trades".

3. POSITION SIZING / RISK LIMITS (once a book is trusted enough to
   size real capital into - Stage 3/4 of the real-capital roadmap) -
   Kelly Criterion (Half-Kelly in practice) for per-trade sizing, VaR/
   CVaR for a formal daily loss limit, Risk-Parity weights for how to
   split capital ACROSS multiple trusted books instead of flat equal
   amounts.

4. ONGOING ROBUSTNESS MONITORING (catching decay/curve-fit EARLY,
   re-run periodically on every book with a growing sample) - Walk-
   Forward (first-half vs second-half) split testing is what actually
   caught st3_threshold/NIFTY's fade - this needs to be re-run
   periodically on every book, not just once, since any book's edge
   could fade the same way as more trades accumulate. Monte Carlo
   reshuffling re-checked periodically to track ruin risk as the trade
   count grows. Autocorrelation used specifically to tune a future
   Loss-lock's parameters per-strategy (already on the 14-Aug list).

5. PORTFOLIO-LEVEL RISK (across books, not within one - feeds directly
   into the deferred Portfolio-level Aggregation architecture
   decision) - the Correlation matrix between books' daily PnL (found
   several BANKNIFTY threshold books 0.99-1.00 correlated - not real
   diversification).

6. MARKET-DIRECTION BIAS CHECK (new this pass) - re-run periodically
   alongside the other robustness checks, since a book could develop a
   hidden directional bias over time even if it started unbiased -
   distinguishes genuine mechanism-based skill from "got lucky riding
   a trend", directly informs how much to trust a book's headline PnL
   number at face value.

None of this is a one-time exercise - the plan is to re-run this same
battery of tests at each future review point (14-Aug and beyond) as
each book's sample grows, not just report today's snapshot once and
move on.

==================================================

THETA-FILTER IDEA RETROSPECTIVELY TESTED - REJECTED, 13-Aug - after
discussing a real-time per-trade filter idea (skip an entry if Theta
decay is too severe relative to the option's remaining time, using
the same-day implied_volatility()/black_scholes_greeks() work), the
user explicitly asked NOT to apply it directly to the currently-
working oi_footprint - backtest first. Good instinct, confirmed by
the data.

METHOD: a genuine retrospective test WAS possible here (unlike the
project's usual "no historical option-chain data exists" blocker) -
oi_footprint's own already-closed trades already store Entry Time,
Entry Premium, Entry Spot, Strike, and Symbol (which parse_option_
expiry() turns into an expiry date), which is exactly what implied_
volatility() + black_scholes_greeks() need. Computed each closed
trade's OWN implied Theta at its own entry moment, no assumptions
needed.

RESULT: REJECTED. For oi_footprint/NIFTY (27 trades), the 12 trades
taken 0.24-0.49 days from expiry (same/next-day) showed extreme
Theta (96-203% of premium per day, as expected right before
settlement) - but these were NOT the bad trades: they contributed
Rs +35,970 of the book's total Rs +54,982 (65% of all profit) at a
66.7% win rate, both BETTER than the 15 trades taken further from
expiry. A Theta-based filter at any tested threshold (5-20%) would
have REMOVED the strategy's BEST trades, not its worst ones - likely
because near-expiry ATM options also carry sharper Delta, and a
correct directional call's gain outweighs the faster Theta decay when
the signal is right. For oi_footprint/BANKNIFTY (9 trades, all 13-15
days from expiry since BANKNIFTY is monthly-only), the filter would
have changed nothing either way - too far from expiry for Theta to
matter at any tested threshold.

DECISION: do NOT add this filter to oi_footprint. The general Theta-
awareness idea isn't necessarily wrong for every strategy, but this
specific retrospective test showed it would have hurt oi_footprint's
real results - a genuine negative finding, same "test before touching
a working strategy" discipline that already caught st3_threshold/
NIFTY's fade and the RSI-family's lack of edge.

==================================================

IV vs REALIZED VOLATILITY RETROSPECTIVELY TESTED - PROMISING FOR
oi_footprint ONLY, NOT GENERAL, 13-Aug - same "backtest before
touching a working strategy" method as the Theta test above, applied
to a different idea: is a currently-priced option "expensive" (its
own implied_volatility() at entry, from stored Entry Premium/Spot/
Strike/Symbol) relative to what the underlying has ACTUALLY been
doing (a trailing 10-day realized/historical volatility computed from
real NIFTY/BANKNIFTY daily closes)? Tested as an IV/RV ratio filter -
skip a trade if the option looks overpriced relative to recent real
movement.

oi_footprint/NIFTY (27 trades) - GENUINELY PROMISING. At an IV/RV >
1.5 threshold, the 5 trades that would have been filtered out
contributed almost nothing (Rs +730 total, 40% win rate) while the 22
kept trades captured 98.7% of all profit (Rs +54,252) at a BETTER win
rate (63.6%) than the filtered-out group - a close to "free" filter,
removing weak trades without sacrificing the strategy's real edge.
oi_footprint/BANKNIFTY (9 trades, smaller sample) pointed the same
direction at IV/RV > 1.2 (the 2 filtered trades were net NEGATIVE,
the 7 kept trades' total PnL was actually HIGHER than the book's
current unfiltered total).

DOES NOT GENERALIZE - tested the same IV/RV filter across all 6
threshold-group books with a usable sample (simple_st1_threshold,
st2_threshold, st3_threshold x NIFTY/BANKNIFTY). Already-weak
BANKNIFTY-threshold books stayed weak regardless of filtering (no
rescue). More importantly, on the 3 currently-GOOD NIFTY-threshold
books (simple_st1_threshold, st2_threshold, st3_threshold), the
filter ran BACKWARDS at every tested threshold - the trades it would
have removed were consistently the BEST-performing ones (66.7%-100%
win rate), while the trades it would have kept had a WORSE win rate.
Applying this filter to the RSI-momentum family would have actively
hurt them, the opposite of oi_footprint's result.

INTERPRETATION: IV/RV "option looks cheap/expensive" reasoning appears
to be specifically meaningful for oi_footprint's own OI-based
institutional-positioning signal, not a universal "good trade
detector" - makes some intuitive sense, since RSI-momentum entries
aren't reasoning about options pricing efficiency the same way OI-
buildup entries implicitly might be. Reinforces the same lesson as
the Theta test: a filter idea has to be validated PER STRATEGY, not
assumed to transfer.

DECISION: this IV/RV idea is promising enough to keep as a documented
candidate for oi_footprint specifically (NOT the RSI-family), but NOT
implemented live yet - same small-sample caution as everything else
in this project (27 and 9 trades respectively). Revisit once more real
oi_footprint trades accumulate.

==================================================

CPR (SUPPORT/RESISTANCE DISTANCE) RETROSPECTIVELY TESTED - REJECTED,
MIXED/INCONSISTENT, 13-Aug - user asked for another idea to refine
the RSI-threshold family specifically, after the IV/RV filter turned
out to only work for oi_footprint. Used indicators/cpr.py's Central
Pivot Range calculation (Pivot/TC/BC/R1-3/S1-3 from the previous day's
OHLC) - an existing, already-built but previously UNUSED indicator in
this codebase - to test whether entries taken too close to a
resistance (for CE) or support (for PE) level perform worse, using
the same backtest-before-touching-a-working-strategy method as the
Theta and IV/RV tests.

RESULT: NO clean, consistent pattern - genuinely mixed, book by book:
  - st2_threshold/NIFTY (currently good): filter HELPS - removing
    entries within 0.3% of a CPR level leaves a smaller, better set
    (53.8% win rate vs 38.9%, keeping 75% of total profit in fewer
    trades).
  - simple_st1_threshold/NIFTY (currently good) and oi_footprint/
    NIFTY (this project's best book): filter runs BACKWARDS - the
    "too close to a CPR level" trades it would remove were actually
    the BEST-performing ones (100% and 73.7% win rate respectively,
    contributing MORE than the book's current total profit in oi_
    footprint/NIFTY's case) - applying it would hurt both.
  - The 3 already-weak BANKNIFTY-threshold books: filtering reduces
    total losses substantially (e.g. simple_st1_threshold/BANKNIFTY
    -Rs 41,814 -> -Rs 2,095 on the kept set) but doesn't make any of
    them profitable - a real effect, but not a rescue.
Also a methodology note: the 1.0% distance threshold filtered nearly
ALL trades on every book (NIFTY/BANKNIFTY's CPR levels are dense
enough that almost every entry lands within 1% of some level) -
not a usable threshold, only 0.3%/0.5% gave meaningful splits.

DECISION: REJECT as a general filter - no reliable, book-independent
signal the way IV/RV showed for oi_footprint. Helping one currently-
good book (st2_threshold/NIFTY) while actively hurting two others
(simple_st1_threshold/NIFTY, oi_footprint/NIFTY) is not a basis for
adding this to any live strategy. Not implemented anywhere.

==================================================

LOSS-LOCK BACKTESTED AND DEPLOYED SELECTIVELY, 13-Aug - the user asked
to backtest loss-lock (the mirror of the already-live daily profit-
lock: stop opening new trades for the day after N consecutive Stop-
Losses) before deciding, same discipline as the 3 rejected filters
above. Two variants simulated on each threshold book's own real
closed trades: consecutive-loss-lock (stop after 2 or 3 losses in a
row) and cumulative-loss-lock (stop once today's running loss hits a
fixed Rs threshold).

RESULT: a genuinely clean, consistent, book-quality-dependent pattern
(unlike Theta/IV-RV/CPR's mixed results) - CONSECUTIVE-loss-lock at
k=2 was the strongest variant:
  - Already-weak books: simple_st1_threshold/BANKNIFTY -Rs 41,814 ->
    -Rs 4,520; st2_threshold/BANKNIFTY -Rs 35,158 -> +Rs 2,780 (flips
    positive); st3_threshold/BANKNIFTY -Rs 37,700 -> -Rs 9,717; st3_
    threshold/NIFTY (already faded, see the walk-forward entry above)
    -Rs 29,939 -> +Rs 10,626 (flips positive).
  - Already-strong books: simple_st1_threshold/NIFTY +Rs 28,524 ->
    Rs 17,205 (worse); st2_threshold/NIFTY +Rs 28,115 -> Rs 15,391
    (worse) - the lock cuts off legitimate same-day recovery on these,
    not just further losses.
INTERPRETATION: loss-lock is pure risk-reduction, not edge-creation -
helps a book with no real edge avoid digging deeper into losses, but
costs a book WITH real edge some of its upside by locking out before
a same-day recovery. Book-dependent, not universal.

IMPLEMENTED: strategy/fyers_options_engine.py gained daily_loss_lock
(mirroring daily_profit_lock's existing pattern) and MAX_CONSECUTIVE_
LOSSES=2 / _today_consecutive_losses(). Applied SELECTIVELY in
strategy/options_strategies.py - ONLY simple_st1_threshold/BANKNIFTY,
st2_threshold/BANKNIFTY, st3_threshold/BANKNIFTY, and st3_threshold/
NIFTY get daily_loss_lock=True; simple_st1_threshold/NIFTY and st2_
threshold/NIFTY are deliberately left untouched. 7 new tests.

==================================================

oi_iv_combo BUILT + DEPLOYED, 13-Aug - a new, 33rd/34th book acting on
the promising (oi_footprint-specific) half of the IV/RV finding above:
reuses oi_footprint's OI-buildup signal completely unchanged (imported
from fyers_options_oi_footprint.py, not duplicated - per this repo's
own rule of never modifying a working module), and adds ONE more
condition before opening: the candidate leg's own implied_volatility()
(solved live from its real premium via indicators/black_scholes.py)
must not exceed MAX_IV_RV_RATIO (1.5x) the underlying's own trailing
10-day realized volatility (computed live from real daily closes,
same method as the retrospective backtest). Built as its own separate
book rather than folding into oi_footprint itself, since the same
filter runs backwards on the RSI-threshold family - keeping it
separate avoids ever contaminating the proven oi_footprint signal.

Deployed same day as built (paper trading, zero real-money risk, own
separate book - same reasoning already applied to pcr_momentum/max_
pain_drift/pcr_vix_combo). Wired into ALL_STRATEGIES (31 -> 33 total
books with this and loss-lock combined), mobile app, .gitignore,
GitHub Actions workflow. 3 new tests, 316 passing overall.

==================================================

oi_iv_combo TRIGGER VERIFIED + APK REBUILT, 13-Aug - the user manually
cloned a cron-job.org job (STRATEGY_NAME=oi_iv_combo, same pattern as
the other 3 new strategies today); verified via the GitHub Actions API
that it fires correctly on both NIFTY and BANKNIFTY with no errors and
its first portfolio files committed clean. All 4 strategies added
today (pcr_momentum, max_pain_drift, pcr_vix_combo, oi_iv_combo) are
now confirmed live end-to-end - trigger firing, no errors, both
indices evaluated.

The Android APK installed on the user's phone predated the loss-lock +
oi_iv_combo commit, so even though the mobile app's source already had
oi_iv_combo wired into both the Multi-Strategy and Summary screens, the
actual on-phone build didn't. Rebuilt (`flutter build apk --release`)
and reinstalled via `adb install -r`. Verified on-device: Summary tab
shows "Total Profit/Loss (33 books)" with oi_iv_combo's NIFTY and
BANKNIFTY rows both present. Precise bottom-nav-bar tap coordinates
needed `adb shell uiautomator dump` (reads the real accessibility-tree
bounds) after a couple of pixel-estimate mis-taps - one landed on an
unrelated app's floating PIP video overlay that was covering the
Options/Threshold/Summary tabs until the user closed it, another
landed on a stock card instead of the tab bar. Eyeballing coordinates
from a screenshot isn't reliable for this app's bottom nav; uiautomator
bounds are exact and should be reached for first next time.

==================================================

MINIMUM CAPITAL RETROSPECTIVE REPLAY, 14-Aug - the user asked what each
profitable book's real closed-trade history would have looked like
starting from Rs 10,000 instead of Rs 1,00,000, using the exact same
lot-sizing formula the live engines use (lots = Cash // (entry_premium
x lot_size), or the credit-spread variant using max_loss_per_lot) and
the real transaction-cost model (strategy/options_transaction_costs.py)
- same retrospective-replay approach as the Theta/IV-RV/CPR backtests
above, just replaying against a different starting capital instead of
a different entry rule.

Two findings:

1. Every single BANKNIFTY book could not have executed ANY trade at
   Rs 10,000 - BANKNIFTY's lot size (30) combined with its typical
   premium routinely exceeds Rs 10,000 for even 1 lot, so 100% of
   real historical trades were skipped in the replay. Rs 10,000 is
   not a usable starting capital for any BANKNIFTY book, regardless
   of that book's underlying edge.

2. On NIFTY, results don't scale linearly - fixed per-order brokerage
   (Rs 40 round-trip, independent of lot count) eats a much bigger
   share of a smaller trade. st2_threshold/NIFTY actually flips sign:
   +Rs 28,115 (28.1%) at Rs 1,00,000 starting capital becomes -Rs 861
   (-8.6%) at Rs 10,000 - a real reversal, not just a smaller number.

Followed up by finding each book's own minimum starting capital where
NO real historical trade would have been skipped for insufficient
cash (binary-swept per book): the 4 currently-profitable books need
surprisingly little - oi_footprint/NIFTY Rs 11,000 (still +22.4% ROI
at that level), simple_st1_threshold/NIFTY Rs 11,000 (+18.0%),
st2_threshold/NIFTY Rs 11,500 (+14.4%), oi_footprint/BANKNIFTY
Rs 23,000 (+7.7%). The currently-losing books need far more capital
just to stop skipping trades (Rs 18,500-93,500) and remain net-
negative even then - more capital does not fix a book with no real
edge, it just lets it lose money without missing trades.

==================================================

STAGED CAPITAL PLAN - TIMELINE CONFIRMED, 14-Aug - the user set an
explicit 2-month timeline on top of the existing performance-gated
Stage 2/3 plan: Month 1 = current local/GitHub-Actions paper trading
(already running); Month 2 = repeat paper trading on the Vultr Mumbai
VPS + Firebase (Stage 2 build) to prove out reliability/latency in
the real deployment environment, not just locally; only after both
months does Stage 3 (real capital) begin. This is a fixed-time floor
on top of the existing performance gate (oi_footprint reaching a
trustworthy ~80-100 trade sample) - both conditions need to hold
before Stage 3, not just one.

If the currently-strongest 2-3 books (oi_footprint/NIFTY, simple_st1_
threshold/NIFTY, st2_threshold/NIFTY) hold up through both months,
Stage 3 would start ONLY those proven books with real capital, sized
per the minimum-capital finding above (~Rs 11,000-15,000 each, ~Rs
25,000-35,000 combined) - not the full 33-book portfolio. The rest
keep running as paper trading.

Re-confirmed the same day: the "Claude never executes a real trade"
rule (see Development Rules below) governs Claude's own actions in
any session, not what the deployed, unattended TURION automation is
eventually allowed to do once Live Trading is proven - the documented
Algorithmic Trading milestone (fully autonomous, user-supervised) is
still the intended final stage, reached only after Live Trading
(user-approved per-order) has itself run on real capital first. No
change to the milestone sequence, just confirming Claude's role stays
build/improve/backtest/analyze throughout, on both sides of that line.

==================================================

CIRCUIT-BREAKER PROTECTION IDEAS - NOT YET BACKTESTED, 14-Aug -
researched after the user asked what actually protects an open
position if NSE's circuit breakers halt trading (index-level 10%/
15%/20% moves) while a position is open. Circuit breakers are a net
positive for market stability (prevent an uncontrolled crash, and
rule out the earlier "millisecond mega-spike" scenario as basically
impossible - see below), but a real negative for an open position:
the SL/Target can't fire during a halt, and price can gap further by
the time trading resumes. Five candidate mitigations discussed,
priority order, NONE implemented or backtested yet - explicitly
deferred to a future session at the user's request ("he backtest
karu" - next time):

1. HIGHEST PRIORITY - place the Stop-Loss as a real broker-side order
   (Fyers GTT / SL-M), not just software-side polling. Today's engines
   are pure polling (check every ~1 min, decide, then call the close
   API) - if the VPS/script has any hiccup, or a halt happens between
   checks, nothing protects the position. A broker-side GTT order sits
   with the exchange and fires the instant trading resumes, independent
   of whether the script is even running. Should be part of the Stage 2
   VPS build, not bolted on later.

2. VPS's own continuous loop (not GitHub Actions' cron-job.org-
   throttled ~1-min external trigger) - a real always-on loop can check
   every few seconds instead, shrinking the reaction-time gap before a
   circuit level is reached. Already the reason Stage 2 exists; this is
   an additional concrete reason it matters specifically for circuit
   risk, not just uptime/reliability in general.

3. A proactive square-off filter - NSE's daily circuit band is known in
   advance (computed off the previous close); a filter could force-exit
   a position once the underlying gets within ~2-3% of its own band,
   instead of waiting for the normal SL/Target check. Same shape as the
   existing VIX-band filter. NOT built or backtested yet.

4. Avoid holding through known high-risk event windows (Budget day, RBI
   policy, election results, major macro announcements) - square off or
   skip new entries on these specific days, since they're disproportion-
   ately likely to trigger circuit-level moves.

5. Position sizing discipline (already established practice) - never
   risk enough on one trade that a single circuit-trapped position could
   meaningfully damage total capital.

Also clarified the same conversation: a "millisecond flash-spike turns
Rs 1 lakh into Rs 10 crore" scenario is not realistic. Real historical
flash events (Feb-2018 Volmageddon, Mar-2020 COVID crash) produced deep-
OTM option moves in the 50x-500x range at the extreme, not anywhere
close to 10,000x, and three structural reasons cap it further: NSE's
own circuit breakers halt trading before a move can go unbounded,
liquidity vanishes near the peak of a real panic (a "paper" gain often
can't actually be executed), and this project's own periodic (not
tick-by-tick) checking would likely miss the exact peak millisecond
even if such a move occurred. For option BUYING (this project's
strategies), max loss is capped at the premium paid either way - the
account can go to Rs 0 in a bad case, but not negative.

==================================================

GITHUB_PAT REBUILD REGRESSION - RECURRED + FIXED, 14-Aug - the
morning's oi_iv_combo APK rebuild (`flutter build apk --release`,
earlier today) omitted `--dart-define=GITHUB_PAT=...`, so the Login-
to-Fyers screen showed "App was built without a GITHUB_PAT - the
trigger cannot be sent" once installed. This is the EXACT same class
of bug first hit and fixed 07-Aug (see doc/07aug26_SESSION_LOG.md) -
`--dart-define=GITHUB_PAT` is required at BUILD TIME (mobile_app/lib/
screens/fyers_login_screen.dart reads it via String.fromEnvironment,
baked in at compile time, not runtime) and is silently dropped by any
plain `flutter build apk --release` that doesn't pass it explicitly.

Fixed by loading GITHUB_PAT from the repo-root `.env` (local,
gitignored, never printed/logged) and rebuilding with `flutter build
apk --release --dart-define=GITHUB_PAT="$GITHUB_PAT"`, then
reinstalling via `adb install -r`. Verified live: the user logged in
again through the app and the resulting fyers_trigger.yml workflow
run (08:53 IST, 14-Aug) completed successfully on GitHub Actions.

LESSON (recurring now for the 2nd time) - every future `flutter build
apk` for this app MUST include `--dart-define=GITHUB_PAT="$GITHUB_PAT"`
(read from local `.env`, never hardcoded) or the Fyers login button
silently breaks. Worth checking before/after any release build, not
just when the user reports the error again.

==================================================

oi_footprint EXIT-MECHANISM DEEP DIVE, 14-Aug - triggered by a real bad
trading day (see below) - the user asked to review why oi_footprint had
a big loss day, which surfaced a much bigger structural finding than
"was today's OI-buildup call right or wrong."

BACKGROUND: oi_footprint's Target/Stop-Loss (TARGET_RUPEES = STOP_
LOSS_RUPEES = Rs 1,500, fyers_options_oi_footprint.py) are checked only
periodically (~1 min, external cron-job.org trigger), not continuously.
Real trades routinely OVERSHOOT this band by 2x-10x in both directions
- e.g. 14-Aug alone: one Target closed at +Rs 7,216 (not +1,500), one
Stop Loss closed at -Rs 14,851 (not -1,500). This isn't a bug in the
signal logic, it's a byproduct of the checking cadence: by the time the
next check runs, price has often moved well past the threshold.

RETROSPECTIVE FINDING 1 - capping BOTH sides at exactly +-1,500 (i.e.
"what if checking were instant/continuous") would have made LESS money
historically, not more: oi_footprint/NIFTY's real 31-trade total is
+Rs 41,479; capped tightly at +-1,500 it would only be +Rs 7,500.
BANKNIFTY: real +Rs 11,891 vs capped +Rs 4,500. The profit-side
overshoot has been a net POSITIVE accident historically (winners run
further before the slow check catches them), not something to fix.

RETROSPECTIVE FINDING 2 - the real fix is ASYMMETRIC: cap ONLY the
Stop-Loss side at Rs 2,000 (letting Target/profit exits stay exactly as
they are today, uncapped/loose), replayed against all 40 real trades:
NIFTY +Rs 75,032 (vs actual +Rs 41,479, an 81% improvement), BANKNIFTY
+Rs 12,267 (vs actual +Rs 11,891). Every single improvement came from
capping the worst overshot losses (14-Aug's -Rs 14,851 and -Rs 8,815
both would have stopped at -Rs 2,000) while every winning trade stayed
untouched. RECOMMENDED NEXT STEP (not yet implemented): a real broker-
side Fyers SL-M/GTT order placed at position-open time, calculated to
trigger at the premium level equivalent to ~-Rs 2,000 net loss - fires
instantly at the exchange, independent of the ~1-min script cadence.
Leave Target/profit-taking exactly as-is (do NOT add a symmetric
broker-side target order - that would remove the beneficial overshoot
Finding 1 just proved).

RETROSPECTIVE FINDING 3 - ATR-scaled dynamic version of the same -2,000
SL cap (dynamic_cap = 2,000 x (that day's real NIFTY/BANKNIFTY ATR14 /
average ATR14 over the trade sample), real ATR14 fetched via yfinance)
performed statistically indistinguishable from the flat -2,000 cap:
NIFTY Rs 74,920 vs Rs 75,032 flat, BANKNIFTY Rs 12,302 vs Rs 12,267
flat. Root cause: only 5 trading days in the sample (10-14 Aug), and
real ATR14 barely moved across them (scale factor stayed within 0.926x-
1.048x) - nowhere near enough volatility spread to show whether ATR-
scaling adds value over the simpler flat cap. NOT adopted over the flat
version - added complexity with no demonstrated benefit yet. Revisit
once the sample naturally spans a genuinely high-volatility day (a
policy/results/event day), which the existing 2-month paper-trading
plan should surface on its own without extra effort.

DATA-AVAILABILITY FINDINGS (why the other 3 candidate exit mechanisms -
Trailing Stop, Breakeven Stop, Laddered/Multiple Targets, Indicator-
based Exit - can't be properly backtested yet):

- oi_footprint's real trades are extremely short (0.6-8.9 min, mostly
  1-2 min). The finest existing local data, reports/options_premium_
  history.jsonl (a periodic Fyers quote logger, ~5-min snapshot
  cadence), only had at least one snapshot falling WITHIN a trade's
  entry-to-exit window for 12 of 40 real trades (30%), each with just
  1-2 data points, not a real path.
- CONFIRMED (partial live test, 14-Aug): Fyers' History API DOES
  support option symbols through the same generic strategy/fyers_data.
  py fyers_download() used for indices - a local test against a stale
  cached token failed on AUTH ("Could not authenticate the user"), not
  on the option symbol being rejected, which is the relevant signal.
  This means real 1-minute OHLC candles for past option contracts
  should be fetchable retroactively (not just going forward) once
  tested with a fresh token - a materially better source than the
  5-min snapshot log for any future re-attempt at this backtest.
- On the 12/40 trades that DID have a real intra-trade snapshot: 4
  showed clear "give-back" evidence (price was better mid-trade than
  at actual exit - e.g. one 11-Aug BANKNIFTY Stop-Loss trade was at
  ~breakeven mid-trade, Rs +1.80, but the actual exit was -Rs 2,275),
  which is genuine anecdotal support for Trailing/Breakeven-stop ideas.
  But other trades in the SAME small sample showed the opposite (price
  kept improving after the snapshot, e.g. one 12-Aug trade was Rs
  4,532 at the snapshot but closed at +Rs 13,463) - too small and
  mixed a sample (12 trades, 1 point each) to call either way yet.
  Laddered/Multiple-Targets and Indicator-based Exit could not be
  tested even partially - both need an ordered multi-point path, which
  a single snapshot per trade cannot provide.

PRIORITY FOR NEXT SESSION: implement the broker-side Stop-Loss-only cap
(Finding 2) - it has the strongest, cleanest evidence of any exit-
mechanism idea tested this session. Everything else (ATR-scaling,
Trailing/Breakeven/Laddered/Indicator exits) stays in the "promising,
not enough data yet" bucket, expected to resolve naturally as the
already-planned 2-month paper-trading window accumulates more (and
more varied) real trades.

==================================================

BROKER-SIDE STOP-LOSS ORDER - BUILT, NOT WIRED IN, 14-Aug - the code
side of Finding 2 above, at the user's explicit request ("save karun
thev, nantar karu" - build it and hold, use it later; same code-ready-
not-deployed pattern already used for pcr_momentum earlier this week).
New module strategy/fyers_order_execution.py:

- compute_stop_loss_trigger_price(entry_premium, lots, lot_size,
  max_loss_rupees=2000) - pure function, bisection search (same
  pattern as indicators/black_scholes.py's implied_volatility()) for
  the exit premium at which closing the position realizes
  approximately -Rs 2,000 net, using the SAME real cost model
  (strategy/options_transaction_costs.py) the paper-trading engines
  already use. No network call - fully unit-tested (5 tests in tests/
  test_fyers_order_execution.py, including one checking the real
  14-Aug oi_footprint overshoot trade: entry 109.05/19 lots, the
  computed trigger sits well above the real overshot exit of 98.85).

- place_stop_loss_order(symbol, quantity, trigger_price, product_type)
  - places a REAL Fyers SL-M (Stop Market) SELL order via their v3
  orders/sync endpoint. UNTESTED against the real API (only checked
  against Fyers' documented order schema) - the first real call to
  this should be treated as a live-money action needing the user's
  explicit go-ahead, not assumed to work first time.

NOT WIRED INTO ANYTHING - no strategy module imports or calls either
function; nothing in any workflow/trigger touches this file. Per this
repo's standing rule (Claude never executes a real trade), this is
pure prep work for the eventual Stage 3 Live Trading milestone, not an
activation. Wiring it into a real position (and testing
place_stop_loss_order() for real, starting with a tiny position) is a
separate, later, explicitly-approved decision. 321 tests passing
overall (316 + this file's 5).

==================================================

CIRCUIT-BAND PROXIMITY FILTER - BUILT + RETROSPECTIVELY CHECKED,
14-Aug - candidate #3 from the earlier "CIRCUIT-BREAKER PROTECTION
IDEAS" list (a proactive square-off gate that exits BEFORE the
underlying reaches NSE's index-level circuit band, since a position
can't be closed at all once actually halted). New indicators/circuit_
band.py: compute_circuit_levels(previous_close, tier_pct) - the two
index levels that would trip a given circuit tier (10%/15%/20%,
NSE's real market-wide thresholds); distance_to_circuit_pct() - how
far spot currently is from the nearer band, as a %; is_near_circuit_
band() - the actual gate (default 2% proximity threshold). All 3 pure,
no network call, 8 new tests (329 total passing).

Retrospectively checked against all 40 real oi_footprint trades (using
each trade's real Entry Spot and that day's real previous close, both
already available - no new data needed): the gate would have fired
ZERO times, and the closest any real trade ever came to a 10% circuit
band was 9.12% away (i.e. nowhere close - the threshold is 2%). This
is the expected result, not a disappointing one: index-level circuit
halts are genuinely rare tail events (matches the earlier flash-spike-
realism finding), so a 5-calm-day sample SHOULD show zero triggers.
The useful confirmation here is the negative case - the filter never
would have caused a false-positive early exit on a normal trading day,
so wiring it in later carries no known downside on ordinary days. Its
real value only shows up on a genuine extreme day, which this sample
doesn't and can't contain. Same "built, not wired in, verify later"
status as the broker-side Stop-Loss order above - not activated in any
strategy yet.

==================================================

HIGH-RISK EVENT-DAY CALENDAR - BUILT, NOT WIRED IN, 14-Aug - candidate
#4 from the circuit-breaker ideas list (avoid holding through/opening
on Budget day, RBI MPC announcements, election results, major macro
announcements - these days are disproportionately likely to produce a
large sudden move). New indicators/high_risk_event_calendar.py, 8 new
tests (337 total passing).

Different in kind from this session's other 2 new filters (circuit_
band.py, the SL trigger-price solver) - those are pure math over
already-known numbers; this one depends on a real-world CALENDAR that
needs manual upkeep. Split into two pieces on purpose:

1. is_budget_day() - the one genuinely fixed, programmatically
   computable date (01-Feb every year) - no external list needed.
2. HIGH_RISK_EVENT_DATES - a manually-maintained set for everything
   else (RBI MPC dates, election results, major scheduled macro
   announcements). Shipped EMPTY on purpose, not seeded with guessed
   2026 dates - RBI publishes its MPC calendar on rbi.org.in, election
   dates come from the Election Commission; a wrong hardcoded date is
   worse than none (it would either miss the real risk day or block a
   normal trading day for no reason). Needs periodic manual updates
   against the real published calendars before this filter is useful
   for anything beyond Budget day.

NOT WIRED INTO ANY STRATEGY - same status as the other 2 circuit-
breaker candidates built today. Before this is worth activating, the
HIGH_RISK_EVENT_DATES set needs real dates added by hand.

==================================================

FRACTIONAL POSITION SIZING - RETROSPECTIVELY TESTED, 14-Aug - candidate
#5 from the circuit-breaker ideas list. First had to correct an earlier
assumption in this same conversation: oi_footprint's real per-trade
sizing (lots = Cash // (entry_premium x lot_size), fyers_options_
oi_footprint.py) deploys FULL available Cash on its one open position,
not a %-of-equity cap - the confidence-scaled 1-2%-risk sizing that
exists in this repo (19-Jul, strategy/paper_trading.py) only applies to
the yfinance equity Swing engine, not the options books.

Replayed all real oi_footprint trades at 5 cash-fraction levels
(100%/50%/30%/20%/10% of available Cash per trade, sequential replay so
each trade's lot count still depends on the running Cash balance):

  NIFTY (31 trades)          Total Profit   Worst Single Trade   Max Capital/Trade
  100% (today's real rule)   +Rs 41,479     -Rs 14,851            Rs 1,58,100
  50%                        +Rs 18,668     -Rs 5,501             Rs 61,200
  30%                        +Rs 9,644      -Rs 3,164             Rs 33,645
  20%                        +Rs 5,871      -Rs 1,605             Rs 21,015
  10%                        +Rs 2,657      -Rs 826               Rs 10,200

  BANKNIFTY (9 trades) shows the same pattern, down to Rs 0 profit at
  10% (trades become unaffordable at that small a fraction of Rs
  1,00,000 - consistent with the earlier minimum-capital finding).

FINDING: this is NOT a free-lunch risk reduction - profit and worst-
case loss shrink together, roughly proportionally to the fraction
chosen. Smaller position sizing does not improve risk-ADJUSTED return
here (single-signal book, no diversification benefit within itself);
it is a straightforward ceiling on how much capital can ever be
exposed in one trade. Real value: it directly bounds the circuit-halt
worst case - at 100% up to Rs 1,58,100 could be trapped in one NIFTY
position, at 20% only up to Rs 21,015. Recommended framing for later:
choose a fraction based on how much of a single book's capital is
acceptable to lose in a worst-case trapped-position scenario, not by
looking for a return-improving number - there isn't one. Less relevant
at the small real-capital sizes already planned for Stage 3
(Rs 11,000-15,000 per book), more relevant if capital per book ever
scales toward Rs 1,00,000+.

NOT IMPLEMENTED - retrospective analysis only, no code changed in any
strategy module.

==================================================

EXIT-MECHANISM / CIRCUIT-BREAKER IDEAS - FINAL PRIORITY RANKING,
14-Aug - all 8 ideas from today's session (the 5 circuit-breaker
candidates + Trailing/Breakeven/Laddered/Indicator-based exits tried
earlier the same day), ranked by strength of evidence, not just
build order:

1. HIGHEST PRIORITY - Broker-side Stop-Loss cap (-Rs 2,000). Built
   (strategy/fyers_order_execution.py). Strongest evidence of anything
   tested this session - 81% NIFTY improvement across the FULL 40-trade
   real sample, not a partial/anecdotal one.
2. MEDIUM - Circuit-band proximity filter. Built (indicators/circuit_
   band.py). Sound protection logic, but the current 5-day sample never
   came close to triggering it (closest real trade was 9.12% from the
   band) - it's insurance against a rare event, not something today's
   data can show a return benefit for.
3. MEDIUM - Fractional position sizing. Analysis only, not implemented.
   A genuine risk ceiling (bounds worst-case exposure per trade), but
   NOT a free-lunch return improvement - profit shrinks alongside risk.
   More relevant once real capital per book grows past the current
   Rs 11,000-15,000 Stage 3 plan.
4. TIED TO STAGE 2 - VPS's own continuous check loop. No separate code
   needed - already the reason Stage 2 exists, just reinforced here as
   mattering for exit-overshoot specifically, not only uptime.
5. LOW (until populated) - High-risk event-day calendar. Built
   (indicators/high_risk_event_calendar.py). Only Budget day works out
   of the box; RBI MPC/election/macro dates need manual entry from real
   published calendars before this filter does anything beyond 01-Feb.
6. LOW - ATR-scaled dynamic Stop-Loss cap. Tested, NOT adopted -
   statistically indistinguishable from the simpler flat -Rs 2,000 cap
   in the current 5-day sample (not enough real volatility spread yet).
7. LOW (needs more data) - Trailing-Stop / Breakeven-Stop. Only 12 of
   40 real trades had ANY intra-trade price data (a 5-min snapshot log,
   too coarse for oi_footprint's 1-2 min trades) - mixed, inconclusive
   signal on that partial sample.
8. NOT PURSUED - Laddered/Multiple Targets (already rejected 30-Jul for
   the equity engine, same reasoning applies) and Indicator-based Exit
   (could not be tested at all - no data fine-grained enough exists).

RECOMMENDED NEXT CONCRETE STEP: once Stage 2 (VPS) is live, test #1
(the broker-side SL order) for real with a single small position before
relying on it for anything bigger - place_stop_loss_order() has never
been called against Fyers' real order endpoint.

==================================================

MAJOR CORRECTION - THE SL-OVERSHOOT FIX ALSO REVIVES SEVERAL "DEAD"
RSI-FAMILY BOOKS, 14-Aug - during the 14-Aug review itself, the initial
verdict (below) was to stop pursuing simple_st1/st2/st3 entirely (large
samples, deeply negative, all sharing the exact same RSI>=50 entry
signal with only Target/SL % varying - already swept 3 combos, all
failed). Applying the SAME Stop-Loss-only -Rs 2,000 cap that worked for
oi_footprint (see the exit-mechanism deep-dive entry above) to these
"dead" books, retrospectively, changes that verdict substantially:

  Strategy               Actual PnL    SL -Rs2,000 capped   Flips to profit?
  simple_st1/NIFTY       -Rs 91,799    +Rs 50,957           YES
  st3/NIFTY               -Rs 78,163   +Rs 1,19,227         YES
  st2/BANKNIFTY           -Rs 50,157   +Rs 13,709           YES
  st3/BANKNIFTY           -Rs 46,101   +Rs 19,897           YES
  st3_threshold/NIFTY     -Rs 21,097   +Rs 53,171           YES
  st2/NIFTY                -Rs 97,263  -Rs 30,741           No, but 68% smaller loss
  simple_st1/BANKNIFTY    -Rs 61,370   -Rs 2,113            No, but near breakeven
  st2_threshold/BANKNIFTY -Rs 40,519   -Rs 20,261           No, but 50% smaller loss

REVISED CONCLUSION: the earlier "RSI entry signal has no edge on
BANKNIFTY / non-threshold NIFTY" verdict was likely measuring the SAME
exit-overshoot problem found in oi_footprint, just far more damaging
here because these books trade much more often (87-128 trades vs
oi_footprint's 31) - every overshot Stop-Loss compounds the damage many
more times. The entry signal may have had a real, if modest, edge all
along that the execution problem was masking. Do NOT retire these
books' real-capital candidacy purely on the original numbers - re-
evaluate after the broker-side SL order (already built, not yet live-
tested) is actually running.

SWEPT the SL-cap level itself (Rs 50 to Rs 10,000) on these same 5
books to look for an optimum - found a suspicious MONOTONIC pattern
(tighter cap = more profit, all the way down to Rs 50, never
reversing). This is a red flag, not a stronger result - flagged and
NOT trusted below roughly Rs 1,000-1,500, for two concrete reasons:
(1) real bid-ask spread/slippage on these option premiums likely
exceeds a Rs 50-500 rupee band on its own, making an exact exit at
that level physically impossible in live trading; (2) this retrospective
method only re-caps the ALREADY-RECORDED trades - it does not re-
simulate the much higher trade frequency a genuinely tighter Stop-Loss
would cause in reality (constant whipsaw in/out), which would look
very different from just capping today's trade list. Rs 1,500-2,000
is the recommended range - still shows large, credible improvement
(Rs 50,000-1,90,000+ across these 5 books) without the unrealistic
tail. Analysis only, nothing implemented differently from the SL
order already built.

==================================================

FLAT-RUPEE vs %-OF-DEPLOYED-CAPITAL STOP-LOSS CAP, 14-Aug - the user
asked whether the flat-Rs SL cap (Rs 1,500-2,000 as tested above) is
even the right shape, or whether the cap should instead scale with how
much capital is actually deployed in each specific trade (since lots =
Cash // (entry_premium x lot_size) means position size grows as a book
compounds). Tested properly this time - a full SEQUENTIAL replay (cash
carried trade-to-trade, lots recomputed fresh at each step, not reusing
the historical Lots value from the real 1L-capital run, which an
earlier same-day pass on this exact question got wrong by mixing scales)
- across the 8 books from the "MAJOR CORRECTION" entry above, at 12
capital tiers (Rs 15,000 to Rs 10,00,000), comparing a flat-Rs cap
(2% of STARTING capital, fixed for that book's whole run) against a
%-of-deployed-capital cap (2% of THAT TRADE's actual position size,
recalculated every trade):

  Aggregate (8 books) - Flat wins at every tier, by a growing margin:
  Rs 15,000: Flat 2,53,702 vs Pct 2,33,819 (close)
  Rs 1,00,000: Flat 43,62,019 vs Pct 23,23,604 (~2x)
  Rs 10,00,000: Flat 4,75,42,661 vs Pct 2,43,84,522 (~2x)

  Root cause: under the %-of-deployed rule, every win makes the account
  bigger, which makes the NEXT trade's position bigger, which makes
  the NEXT loss cap bigger too - risk compounds upward exactly when a
  book is succeeding. The flat-Rs cap stays fixed regardless of how
  large the account grows, so it becomes progressively SMALLER as a
  fraction of the (growing) account - more disciplined, and the
  backtest shows meaningfully more profitable as a result.

  PER-BOOK NUANCE (this matters for the actual near-term plan): the
  aggregate hides a real small-vs-large-capital reversal. At Rs 15,000-
  50,000 specifically - the exact range already planned for Stage 3 -
  the %-of-deployed method wins or ties for MOST of the 8 books
  (simple_st1/NIFTY, st2/NIFTY, st3_threshold/NIFTY, simple_st1/
  BANKNIFTY, st2/BANKNIFTY, st3/BANKNIFTY all favor Pct at Rs 15,000).
  Flat only pulls decisively ahead from roughly Rs 1,00,000 onward, and
  the gap widens the larger capital gets. RECOMMENDATION: %-of-deployed
  is the more defensible choice for the actual Stage 3 capital range
  (Rs 11,000-15,000); switching to a flat-Rs cap becomes worth
  revisiting only if/when capital per book scales toward Rs 1,00,000+
  (Stage 4 territory).

  st2_threshold/BANKNIFTY is negative under BOTH cap methods at EVERY
  capital tier tested - the only book of the 8 that neither fix
  rescues. Reinforces that its problem is likely the entry signal
  itself, not exit-overshoot - it should stay excluded from real-
  capital consideration regardless of which SL-cap design is chosen.

Analysis only - no code changed. When the new SL-capped strategy
variants are actually built (separate books alongside the originals,
per this repo's "never modify a working module" rule and the user's
own explicit choice to build-new-not-modify), they should use
%-of-deployed-capital sizing for the Stage 3 capital range, not the
flat-Rs design that wins only at larger capital.

==================================================

HYBRID SL CAP - min(flat, %-of-deployed) BEATS BOTH PURE VERSIONS,
14-Aug - the user asked if flat-Rs and %-of-deployed could be
combined rather than picking one. Tested min(flat_cap, pct_cap) - at
each Stop-Loss trade, compute both caps and use whichever is SMALLER
(more protective) - against the same 8 books x 6 capital tiers as the
entry above:

  Capital       Flat            Pct             Hybrid(min)
  Rs 15,000     2,53,702        2,33,819        3,82,629   <- best
  Rs 50,000     18,93,391       10,72,738       19,35,940  <- best
  Rs 1,00,000   43,62,019       23,23,604       43,87,240  <- best
  Rs 2,00,000   91,23,311       47,88,659       91,44,880  <- best
  Rs 5,00,000   2,35,26,553     1,21,44,487     2,35,59,032 <- best
  Rs 10,00,000  4,75,42,661     2,43,84,522     4,75,96,020 <- best

The hybrid wins (or ties) at EVERY tier tested, never worse than
either pure version - makes sense structurally: at small capital/small
positions the %-cap is naturally the tighter one and gets picked
(capturing %'s small-capital advantage from the entry above); as the
account/position grows the %-cap grows past the flat-cap and the flat
one gets picked instead (capturing flat's large-capital discipline).
min() always selects whichever discipline is currently more
conservative - it cannot be worse than the better of the two inputs.
REVISED FINAL RECOMMENDATION: use this hybrid, not either pure form,
when the SL-capped strategy variants are actually built.

HOW THIS MAPS TO THE ALREADY-BUILT BROKER ORDER CODE - the user asked
how a formula (not a single number) gets enforced by a real broker
order, which only accepts one fixed trigger price. Answer: the hybrid
logic runs entirely in OUR code, once, at position-open time - the
broker never needs to know a formula was involved. Concretely, using
the two functions already built in strategy/fyers_order_execution.py:

  flat_cap = starting_capital * 0.02
  pct_cap = (entry_premium * lots * lot_size) * 0.02
  final_cap = min(flat_cap, pct_cap)
  trigger_price = compute_stop_loss_trigger_price(entry_premium, lots, lot_size, max_loss_rupees=final_cap)
  place_stop_loss_order(symbol, quantity, trigger_price)

compute_stop_loss_trigger_price() already accepts an arbitrary
max_loss_rupees - no new function needed, just pass the hybrid-
computed value instead of a fixed 2,000 when wiring this into a real
strategy later.

==================================================

_slcap BOOKS BUILT + DEPLOYED (PAPER TRADING), 14-Aug - the hybrid SL
cap (min of flat-2%-of-initial-capital and 2%-of-that-trade's-
deployed-capital - see the two entries above) implemented as 8 new
paper-trading books, alongside (not replacing) the 8 originals that
the "MAJOR CORRECTION" finding was based on, per this repo's own
"never modify a working module" rule and the user's explicit choice to
build new rather than change the originals.

strategy/fyers_options_engine.py gained hybrid_sl_cap_pct (new optional
make_strategy() parameter, default None = original behavior
unchanged) and a new pure helper _hybrid_stop_loss_cap(cfg,
capital_deployed) that returns min(flat_cap, pct_cap) - _check_position
uses it INSTEAD of the plain stop_loss_pct check whenever
hybrid_sl_cap_pct is set on a config; Target/profit-taking is
untouched either way. 5 new tests (pure function, no network needed).

8 new books in strategy/options_strategies.py, same entry/Target as
each original, hybrid_sl_cap_pct=2.0:
  NIFTY: simple_st1_slcap, st2_slcap, st3_slcap, st3_threshold_slcap
  BANKNIFTY: simple_st1_slcap, st2_slcap, st3_slcap, st2_threshold_slcap
(st2_threshold/BANKNIFTY was the one book that stayed negative under
every cap tried in testing - deliberately NOT given an _slcap variant).
ALL_STRATEGIES grew 33 -> 41. Wired into the mobile app (3 screens:
main Options tab gets the 3 non-threshold _slcap books, Threshold
Options tab gets the 2 threshold-group _slcap books with their
NIFTY/BANKNIFTY-only index restriction, Summary tab lists all 8),
.gitignore, and the GitHub Actions workflow's git-add list, following
the same pattern as every other same-day-deployed strategy this month.
344 tests passing overall. Deployed same day as built (paper trading,
zero real-money risk) - the 2 parallel book-sets (original vs _slcap)
will make the hybrid-cap hypothesis directly comparable on real future
trades, not just the retrospective replay it's based on so far.

==================================================

oi_footprint EXIT-MECHANISM VARIANTS BUILT + DEPLOYED (42nd-53rd
books), 14-Aug - the 5 profit-booking-filter ideas from the "oi_
footprint EXIT-MECHANISM DEEP DIVE" entry (Trailing-Stop, ATR-scaling,
Breakeven, Laddered, Indicator-based) could NOT be retrospectively
backtested - oi_footprint's real trades are too short (0.6-8.9 min)
for any available historical price data to reconstruct an internal
path. Built as 6 LIVE paper-trading variants instead (the data gap is
a HISTORICAL problem, not a live-checking one - going forward each
variant's own real-time checks see real prices as they happen).

New strategy/fyers_options_oi_footprint_variants.py - reuses oi_
footprint's OI-buildup entry signal unchanged (imported, not
duplicated - strategy/fyers_options_oi_footprint.py itself is
untouched, per this repo's rule) and the same _hybrid_stop_loss_cap()
built for the _slcap books. All 6 share the hybrid SL cap; each adds
exactly ONE further idea on top (never combined with each other, to
keep every variant a clean, isolated test):

  oi_hybrid_sl             - hybrid SL cap only (baseline for this
                              group), Target left exactly as-is
                              (letting profit overshoot naturally,
                              per the earlier "MAJOR CORRECTION"
                              finding that this has been net-
                              beneficial).
  oi_hybrid_sl_trailing    - + once Target (Rs 1,500) is first
                              reached, don't exit immediately - trail
                              at 30% below the peak profit seen
                              instead (TRAIL_PCT).
  oi_hybrid_sl_atr         - + the hybrid cap itself is scaled by
                              today's real ATR14 vs. a rolling ~1-
                              month average (live version of the
                              retrospective ATR test).
  oi_hybrid_sl_breakeven   - + once profit ever reaches Rs 750
                              (BREAKEVEN_TRIGGER_RUPEES), the position
                              can never close at a net loss again.
  oi_hybrid_sl_laddered    - + books HALF the position once profit
                              reaches 50% of Target, letting the other
                              half continue independently toward the
                              full Target/hybrid-SL.
  oi_hybrid_sl_indicator   - + exits early ("Indicator Exit") if the
                              underlying's RSI crosses back through 50
                              against the position's direction, ahead
                              of Target/Stop-Loss.

7 new tests (config shape + the pure parts of partial-close/close-
position logic - _check_position itself needs live network quotes,
same untestable-without-mocking status as every other engine's
_check_position in this repo). 12 new books (6 variants x 2 indices),
wired into ALL_STRATEGIES (41 -> 53), .gitignore, and the GitHub
Actions workflow - so these 12 books DO run and persist state, and
DO get committed to the repo. 353 tests passing overall. Deployed
same day as built (paper trading, zero real-money risk).

BACKEND ONLY, NOT YET IN THE MOBILE APP - the user explicitly asked
not to wire this batch into the app UI yet ("app madhe add karu
nakos, ajun khup kam aahe" - more work still coming, don't touch the
app for every increment). The 3 option-tab screens were briefly
edited to add these 12 books, then that edit was reverted before
committing - the app still only shows the same 15 strategies as
before this entry. App wiring is a deliberate separate, later step
once this round of oi_footprint-variant work settles, not an
oversight.

==================================================

REMAINING THRESHOLD BOOKS GIVEN THE HYBRID SL CAP (54th-59th books),
14-Aug - after the first 8 _slcap books, the user asked to
retrospectively test the hybrid cap on every threshold book NOT yet
covered: st3_threshold/BANKNIFTY, simple_st1_threshold (both indices),
st2_threshold/NIFTY, and st4_threshold (both indices).

FINDINGS:
- st3_threshold/BANKNIFTY: -Rs 48,962 (actual) -> +Rs 21,488 (hybrid
  cap, Rs 1,00,000) - flips to profit, same pattern as the first 8.
- simple_st1_threshold/BANKNIFTY: -Rs 49,342 -> +Rs 7,593 - flips too.
- st2_threshold/NIFTY: already profitable (+Rs 38,546 actual) -> +Rs
  1,01,053 with the hybrid cap - roughly 2.6x better, confirming the
  hybrid cap helps ALREADY-GOOD books too, not just failing ones.
- simple_st1_threshold/NIFTY: already profitable (+Rs 35,348) -> +Rs
  46,581 with the hybrid cap - ~32% better.
- st4_threshold/NIFTY: -Rs 16,685 -> -Rs 5,752 - improves but does NOT
  flip to profit (small 3-trade sample).
- st4_threshold/BANKNIFTY: -Rs 805 -> -Rs 805, NO CHANGE - its 3-trade
  sample never actually hit a Stop-Loss, so no cap ever bound.
- st2_threshold/BANKNIFTY (already had a _slcap variant from the first
  8) was re-confirmed: stays negative under flat, pct, AND hybrid caps
  at every capital tier from Rs 15,000 to Rs 10,00,000 - the only
  threshold book where the hybrid cap genuinely does not help. Its
  problem is almost certainly the entry signal itself, not exit-
  overshoot - correctly left without a second attempt.

DEPLOYED (backend only, same as the 12 oi_footprint variants above -
mobile app wiring deferred): 6 new threshold _slcap books added at the
user's explicit instruction to cover every threshold book that was
actually tested ("warate je apan check kelya tya sarvana"), including
st4_threshold despite its weaker retrospective result - simple_st1_
threshold_slcap (both indices), st2_threshold_slcap/NIFTY (its
BANKNIFTY sibling already existed), st3_threshold_slcap/BANKNIFTY (its
NIFTY sibling already existed), and st4_threshold_slcap (both indices,
new hybrid_sl_cap_pct parameter added to fyers_options_st4.py's make_
st4_config() - only replaces the INITIAL Stop-Loss phase before st4's
own spot-based trailing stop activates, which is untouched). 3 new
tests (fyers_options_st4.py's hybrid_sl_cap_pct config shape). 355
tests passing overall. ALL_STRATEGIES 53 -> 59 - every threshold book
retrospectively tested this session now has hybrid-cap coverage except
st2_threshold/BANKNIFTY, deliberately, per the finding above.

==================================================

MOBILE APP - GROUPED OVERVIEW + PER-TRADE COST BREAKDOWN, 14-Aug - a
flat tab-per-strategy list stopped being usable once ALL_STRATEGIES
grew from 33 to 59 today, and the user asked for two things: (1) every
book grouped into 4 buckets instead of one long tab row, (2) tapping
any trade (live or historical) shows full detail including the REAL
trading costs (not personal income tax, which depends on the user's
total annual income and can't be computed in-app - explicitly
excluded per the user's own clarification).

NEW SCREEN - FyersOptionsGroupedScreen (mobile_app/lib/screens/fyers_
options_grouped_screen.dart), added as a 10th bottom-nav tab
("Grouped"). Fetches all 59 books' real Cash + Closed Trades count on
every load and classifies LIVE (not a hardcoded list, since which book
is "profitable" changes day to day - several flipped sign today alone):
  New (SL-cap)  - name ends "_slcap" or starts "oi_hybrid_sl" (26
                  books) - shown regardless of its own PnL sign, since
                  the point is tracking the fix's own cohort, not
                  today's result.
  Profitable    - everything else with Cash > initial capital.
  Loss-making   - everything else with Cash < initial capital.
  No data yet   - everything else with zero closed trades.
Tapping a book row opens a new FyersOptionsBookDetailScreen (fyers_
options_book_detail_screen.dart) - the same open-position/closed-
trades content the per-strategy tabs already show, for exactly that
one (name, index) pair.

PER-TRADE COST BREAKDOWN - new options_transaction_costs.dart mirrors
strategy/options_transaction_costs.py's formula exactly (brokerage/
STT/exchange charges/stamp duty/SEBI charges/GST), computed CLIENT-
SIDE from fields every trade record already has (Entry/Exit Premium,
Lots) plus the known lot size per index - no backend change needed,
works for historical trades too. showOptionTradeDetails() (widgets/
common.dart) - tapping any OptionPositionCard (live) or
OptionClosedTradeCard (history) now opens a detail sheet: Lots, Units,
Entry/Exit Time, Entry/Exit Premium, Exit Reason, Held-for duration,
then the itemized cost breakdown, then Net PnL, then an explicit note
that this is trading costs only, not personal income tax. Credit-
spread trades (2-leg) get the other fields but no cost breakdown - the
live credit_spread engine itself never applies this cost model, so
computing one here would invent a number the backend doesn't use.
"View Chart" (unchanged underlying-chart navigation) becomes a button
inside this sheet rather than the tap target itself - both card
widgets' `onTap` param renamed to `onViewChart` to reflect this.

VERIFIED LIVE on the user's phone (APK rebuilt with --dart-define=
GITHUB_PAT, adb install -r, per the established GITHUB_PAT-flag
lesson): Grouped screen correctly showed "New (SL-cap) (26)" with real
Rs 0 (no trades yet - Saturday, market closed) plus real Profitable/
Loss-making sections with correct real PnL figures; tapping into st4/
NIFTY's real -Rs 4,321.06 Stop-Loss trade showed the full cost
breakdown, and the displayed Net PnL (after costs) matched the
backend's real recorded Net PnL EXACTLY - confirms the Dart cost
calculation is byte-for-byte consistent with the live Python engine's.
`flutter analyze` clean across the whole app.

==================================================

TICK-BY-TICK DATA STORAGE - VPS LIMITS, CLOUD-VS-PHYSICAL COST,
COMPRESSION OPTIONS (15-Aug, discussion only, no code built) -
follow-up to the earlier tick-data-usefulness discussion above.
Answers three concrete questions the user asked, for future
reference when Stage 2 (VPS) or the narrow position-window tick-
capture idea (see LIVE-DATA ARCHITECTURE section) is actually built.

1. VPS'S OWN LIMIT (before any external storage): the ~Rs 400-600/
   month small India-region VPS already planned for Stage 2 (1 vCPU,
   1-2GB RAM, 40-60GB SSD, ~2TB/month transfer) is NOT bottlenecked
   by CPU or bandwidth at 100-300 ticks/sec combined (a single vCPU
   parses/writes that volume trivially; even 300 ticks/sec stays
   well under the 2TB transfer cap). The real bottleneck is the LOCAL
   DISK: at full 228-instrument capture the ~30-40GB free disk fills
   in 1-5 days depending on rate (100-300 ticks/sec). Practical
   VPS-only limit: ~100 ticks/sec AND a narrow ~20-30 instrument scope
   (only the ATM strikes actually traded, not the full chain) - that
   keeps a full month's data within the VPS's own disk with no
   external storage needed.

2. WITH EXTERNAL CLOUD STORAGE ADDED (upload nightly, keep only a
   1-2 day rolling buffer on the VPS itself): disk stops being the
   constraint. Compared three options:
     - Cloud OBJECT storage (Backblaze B2 / S3): ~Rs 500/TB/month -
       cheapest, no filesystem-mount needed, VPS just uploads daily
       files.
     - Cloud BLOCK storage (AWS EBS / Lightsail extra disk): ~Rs
       800-900/TB/month - ~1.5-2x pricier than object storage, only
       worth it if the VPS needs to query the data directly as a
       live filesystem (not needed for tick archival).
     - Physical SSD (one-time purchase, Rs 4,000-11,000 for 1-2TB):
       CANNOT be plugged into a cloud VPS directly - only usable if
       kept at the user's own home, which reintroduces the exact
       problem the VPS was solving (needs a second machine on 24/7,
       own electricity cost, own internet/power reliability, no
       built-in redundancy if the drive fails). Breaks even vs cloud
       object storage at ~10 months of 1TB retention, but only if
       the home-reliability/electricity costs are ignored. RECOMMEND
       cloud object storage (B2) over physical SSD given this
       project's system is meant to run unattended on the VPS.
   Cost at B2 rates, by scope x tick-rate (recurring, GB generated
   PER MONTH, not cumulative):
     - Narrow scope (~25 instruments actually traded):
       100/sec -> Rs 15-20/mo | 200/sec -> Rs 30-35/mo |
       300/sec -> Rs 45-50/mo
     - Full scope (228 instruments, whole chain + both indices'
       constituents):
       100/sec -> Rs 125-150/mo | 200/sec -> Rs 250-300/mo |
       300/sec -> Rs 375-450/mo
   New real limit once storage is cheap: VPS CPU (1 vCPU) caps out
   around ~300-500 ticks/sec combined across instruments - going
   higher needs a bigger VPS, not more storage. Also worth noting:
   a single liquid option contract rarely ticks faster than ~2-5/sec
   in reality - 200-300 ticks/sec only makes sense as a TOTAL across
   many instruments, never per contract.

3. IF NEVER DELETED (data kept forever, growing every month) vs
   ROLLING WINDOW (old data deleted, constant monthly footprint) -
   this matters a lot for a 1-year total:
     - Full scope, 300/sec, kept forever: bill grows monthly (Rs 450
       -> Rs 900 -> ... -> Rs 5,400 by month 12) - YEAR 1 TOTAL ~Rs
       35,100, and by year-end storage sits at 10.8TB with the
       monthly bill still climbing into year 2.
     - Full scope, 300/sec, rolling/rotated: flat Rs 450/month x 12
       = Rs 5,400/year, never grows.
     - Narrow scope, 100/sec, kept forever: YEAR 1 TOTAL ~Rs 1,050.
     - Narrow scope, 100/sec, rolling: flat Rs 15/month x 12 = Rs
       180/year.
   RECOMMEND rolling/rotated retention (delete data older than the
   analysis window actually needs) over "keep everything forever" -
   ~200x cheaper at the narrow-scope end, and the cost otherwise
   never stops climbing.

4. COMPRESSION OPTIONS BEYOND PLAIN GZIP (~22 bytes/tick baseline
   used in the above estimates), and which are safe (lossless) vs
   need care:
     LOSSLESS (mathematically guaranteed, no data lost, use freely):
     - Binary format instead of JSON (no repeated field-name text) -
       ~3-5x smaller before compression.
     - Delta encoding (store the change from the previous tick, not
       the absolute value) - smaller numbers compress better, fully
       reversible.
     - zstd instead of gzip - better ratio, faster, still 100%
       lossless (same category as gzip, not lossy like JPEG/MP3).
     NEEDS CARE (genuinely lossy if implemented naively):
     - Skip ticks where nothing changed ("heartbeat" ticks) - SAFE
       only if price, volume, AND open interest are all checked for
       no-change before skipping; checking price alone risks
       silently dropping real volume/OI updates that occurred at an
       unchanged price.
     - Store Open Interest at a lower frequency than price/volume -
       SAFE only down to the exchange's own real OI-refresh rate
       (OI doesn't update every tick at the source anyway); sampling
       slower than that genuinely loses real OI data points.
   Combined effect estimate: Rs 450/month (full scope, 300/sec)
   could realistically drop to ~Rs 90-100/month (~5x) with binary +
   delta + zstd + careful unchanged-tick skipping - at the cost of
   meaningfully more implementation/maintenance complexity than
   plain JSON+gzip. Recommended to start simple (JSON+gzip) and only
   add these once real usage confirms the cost is worth optimizing.

==================================================

SLIPPAGE & EXECUTION-DELAY DISCUSSION + THEORETICAL STRESS-TEST
(15-Aug) - equity Swing/Intraday review surfaced the user's "is the
whole direction wasted if real trading doesn't work" concern, which
led into a slippage/execution-delay explainer and then a concrete
what-if analysis. No code built - analysis + a saved finding only.

EXECUTION DELAY vs SLIPPAGE - two different problems, only one fixed
by the planned Stage 2 VPS:
  - Execution delay (our own reaction time - the cron-based 1-5 min
    check cadence, same root cause as the oi_footprint SL-overshoot
    finding above) - a low-latency same-region VPS + live WebSocket
    genuinely fixes this, already the Stage 2 plan.
  - Slippage (bid-ask spread + limited order-book depth at the
    moment an order lands) - NOT a speed problem, a liquidity
    problem. A faster VPS does not change how much quantity is
    resting in the order book at the best price - this needs its
    own mitigations (trade liquid ATM strikes, size orders to
    available depth, avoid open/close minutes and high-risk event
    windows, consider limit vs market orders) once real order
    placement is ever turned on.

THEORETICAL SLIPPAGE STRESS-TEST (rough estimate, NOT a real
backtest - explicitly caveated as such to the user): we have never
captured historical bid/ask depth, only LTP, so a true measured
slippage backtest is impossible with current data (same root cause
as the oi_footprint exit-mechanism variants that couldn't be
retrospectively backtested either). As a stand-in, applied an
assumed round-trip spread cost (spread% x (Entry+Exit Premium) x
Lots x lot_size, i.e. crossing the spread on both legs) to all 40
real closed oi_footprint trades (31 NIFTY @ lot_size 75, 9 BANKNIFTY
@ lot_size 30; original recorded Net PnL, real transaction costs
already included, no slippage: +Rs 53,370.27):
  - 0.5% spread assumption: -Rs 24,633 slippage -> new total +Rs
    28,738 (46% of the paper profit eaten), 0 trades flip sign.
  - 1.0% spread assumption: -Rs 49,265 -> new total +Rs 4,105 (92%
    eaten, barely profitable), 0 trades flip sign.
  - 2.0% spread assumption: -Rs 98,530 -> new total -Rs 45,160
    (flips net NEGATIVE), 6 individual trades flip from winning to
    losing.
Side finding while building this: oi_footprint sizes every trade
using nearly all available cash (lots = cash // (entry_premium x
lot_size), no cap) - real lots ranged 4 to 118 across the 40 trades
as capital compounded. Slippage cost scales linearly with position
size, so this all-in sizing directly amplifies slippage sensitivity
as capital grows - flagged as a candidate to revisit (a position-
size cap) specifically for when real capital trading begins, NOT
changing anything for paper trading now.

CONCLUSION: not acted on, filed for the Stage 3 (real capital)
planning window - (1) a genuine future need is capturing at least
best-bid/best-ask (ideally full depth) going forward so a REAL
slippage figure can be measured instead of assumed, (2) a position-
size cap is worth reconsidering once real orders are placed, purely
because of its slippage-amplification effect, not because paper
performance itself is in question.

==================================================

POSITION-SIZE-CAP "SLIPPAGE PROTECTION" RETROSPECTIVE BACKTEST
(15-Aug) - direct follow-up to the theoretical slippage stress-test
above, testing the position-size-cap idea it flagged. Still no code
built (paper-trading strategies untouched) - a one-off retrospective
replay script only (matches this project's established sequential-
replay convention: lots recomputed fresh from simulated cash at each
step, each index's cash pool kept separate, real historical Entry/
Exit Premium used, calculate_options_round_trip_cost() reused for
consistency with the live cost model).

Swept MAX_CASH_PCT (how much of available cash one trade may use;
100% = today's real uncapped behaviour) x assumed round-trip spread
(0/0.5/1/2%), across all 40 real oi_footprint trades:

  Cash cap | 0% spread | 0.5% spread | 1% spread | 2% spread
  100% (today) | +Rs 53,370 | +Rs 28,806 | +Rs 7,018  | -Rs 27,990
  75%          | +Rs 37,783 | +Rs 20,760 | +Rs 5,498  | -Rs 22,039
  50%          | +Rs 23,674 | +Rs 13,528 | +Rs 3,712  | -Rs 13,489
  25%          | +Rs 8,465  | +Rs 4,641  | +Rs 222    | -Rs 6,137

FINDING (important nuance, not a simple "cap = safer" story): the
cap does NOT change the breakeven spread% (stays ~1-1.3% across
every cap level, since profit and slippage cost both scale linearly
with position size together) - what it DOES change is the absolute
RUPEE size of the worst case: at 2% spread, uncapped loses -Rs
27,990 vs -Rs 6,137 at a 25% cap (~4-5x smaller worst-case loss).
The same scaling cuts the upside proportionally too (0% spread
best case: +Rs 53,370 uncapped vs only +Rs 8,465 at 25% cap) - a
genuine risk-vs-reward tradeoff, not free protection.

CONCLUSION: not deployed, not changing paper trading now (real
spread still unmeasured, same reasoning as above). Recommendation
filed for Stage 3 real-capital planning: start with a meaningfully
lower cash-per-trade cap (e.g. 50% or less) rather than today's
100%-of-cash sizing, specifically as a risk-magnitude control until
real slippage is measured, not because paper performance is in
doubt.

==================================================

PORTFOLIO-LEVEL AGGREGATION - FIRST CUT, VIEW-ONLY (15-Aug) - the
user's explicit choice of the 3 options discussed: build the
combined PnL/risk view first (safe, read-only), defer correlation-
adjusted allocation and the shared Backtest-Live Engine. BACKEND
ONLY per direct instruction - not wired into the mobile app yet.

NEW strategy/portfolio_aggregation.py - pure, read-only functions,
never writes to any portfolio file, never touches any strategy's
live logic:
  - load_daily_pnl(portfolio_file) - real Net PnL per calendar day
    from a book's Closed Trades (sums same-day exits, nothing
    interpolated for quiet days).
  - load_all_books_daily_pnl() - the above for every book in
    options_strategies.ALL_STRATEGIES.
  - compute_correlation_matrix(daily_pnl_by_book, min_overlapping_
    days=5) - pandas correlation, but books with fewer than 5 real
    data points are dropped first (a 2-day-old book "correlating
    1.00" with anything is noise, not a finding) - returned
    separately as "insufficient data", not silently included.
  - cluster_correlated_books(correlation_matrix, threshold=0.9) -
    union-find grouping of books correlated >=0.9 with each other
    (transitively) - matches the 0.9 bar used in 14-Aug's original
    manual BANKNIFTY-correlation finding.
  - compute_portfolio_summary() - combined Cash/PnL across all 59
    books (plain addition, correlation doesn't change this part)
    plus the "independent bet count" (cluster count + insufficient-
    data-count) - the number plain addition can't tell you.
8 new tests (tests/test_portfolio_aggregation.py, tmp_path-based,
no dependency on real report files), 363 passing overall.

RUN AGAINST REAL DATA, 15-Aug: 59 books, only 22 have any real
data yet (37 too new - includes all the just-triggered 26 hybrid-
SL-cap/oi_footprint-variant books). Combined: Cash Rs 53,71,739.94
vs Rs 59,00,000 deployed (59 x Rs 1,00,000) = TOTAL PnL -Rs
5,28,260.06. Only 13 books have enough data (>=5 days) to even
attempt correlation; of those, found 2 real clusters:
  - simple_st1_threshold_banknifty + st2_threshold_banknifty +
    st3_threshold_banknifty (one cluster - CONFIRMS and extends
    14-Aug's manual "BANKNIFTY RSI books 0.99-1.00 correlated"
    finding, now reproducible in code instead of eyeballed).
  - simple_st1_nifty + st3_nifty (a second, smaller cluster not
    previously flagged).
  Everything else in the 13 (including oi_footprint_nifty) came
  back independent. INDEPENDENT BET COUNT: 56 of 59 - a small
  reduction today only because most books (including the entire
  26-book batch that just started) are still too new to correlate
  meaningfully; expected to firm up as more books accumulate >=5
  days of real trades.

NOT DONE YET (deliberately, per the user's own sequencing):
correlation-adjusted capital allocation (option "ब" from the
original 3-way choice), and no mobile app screen - stays a backend-
only analysis module until the user asks for either.

==================================================

SHARED BACKTEST-LIVE ENGINE - FRAMEWORK BUILT, NOT APPLIED (15-Aug)
- item #6 from 08-Aug's "GAPS VS A PROFESSIONAL ALGO TRADING SYSTEM"
list, deferred back then, built now at the user's explicit request
("engine badun ghe") after a detailed explanation of why it exists:
a real divergence already happened once (nifty_options_backtest.py's
Black-Scholes-estimated sweep showed +69%/57 days; the separately
hand-written live module showed a large real loss on real premiums -
two independently hand-written copies of "the same" logic drifted
apart).

NEW strategy/backtest_live_engine.py - deliberately minimal, generic
(not options-specific): run_backtest(decide_fn, cfg, historical_data_
points, initial_capital) replays a list of data points through a
caller-supplied decide_fn; run_live_check(decide_fn, cfg, portfolio,
live_data_point) feeds exactly one live data point through the
IDENTICAL internal _step() function. decide_fn is a pure function
the caller supplies once - (cfg, position, data_point) -> (action,
new_position, trade_record) - so there is no second hand-written
copy to diverge, by construction. 4 new tests (tests/test_backtest_
live_engine.py), including one that proves run_backtest() fed a
whole list and run_live_check() fed the same points one-at-a-time
(as a real cron-triggered strategy would experience) produce BYTE-
IDENTICAL final portfolios - the actual guarantee this module exists
to provide. 367 tests passing overall.

DELIBERATELY NOT APPLIED to anything yet, confirmed with the user
step by step:
  - NOT retrofitted onto the 59 already-running books (same 08-Aug
    reasoning: they're mid-way through accumulating real trade data
    for validation, touching their code now risks a silent behaviour
    change right when continuity matters most).
  - NOT retrofitted onto today's 26 newly-triggered books either -
    user asked this directly ("aaj tayar kelya strategy shift
    karuyat ka") and was talked out of it: those 26 have ZERO real
    trades yet (cron triggers only just got fixed today), so
    "created today" is if anything a stronger reason to leave them
    alone, not a weaker one - the same "don't touch a book that's
    establishing its real-data baseline" rule applies regardless of
    a book's age.
  - PLANNED connection to Stage 2 (VPS): the VPS migration already
    requires rewriting every strategy's check logic from periodic-
    poll to event-driven-on-tick (per the existing LIVE-DATA
    ARCHITECTURE plan above) - since that rewrite is happening
    anyway at that point, doing it THROUGH this engine's decide_fn
    shape avoids rewriting each strategy's logic twice (once for
    event-driven, once later for the shared engine). Real per-
    strategy verification (replay each book's real historical trades
    through its new decide_fn, confirm the output matches to the
    rupee) is still required at that point - this framework doesn't
    remove that need, it only avoids doing the rewrite itself twice.
  - CURRENT practical use: none yet, by design - this is
    infrastructure built ahead of need, ready for the next genuinely
    NEW strategy idea (not a variant of an existing one) whenever
    one comes up. Confirmed directly with the user rather than
    inventing a use for it today.

==================================================

DESKTOP APP - ANDROID PARITY, FULL BUILD (15-Aug) - the last of the
14-Aug plan's 5 items. Was deferred earlier the same session pending
scope, then scoped after the user confirmed desktop usage is "जवळपास
नाहीच" (almost never) - real work only used because it turned out
cheap (a few hours) once actually scoped step by step, not because
desktop usage grew.

BEFORE: desktop_app.py (PySide6) had 4 tabs (Market Overview, Chart,
Watchlist, Paper Trading) - all yfinance-only, ZERO visibility into
Fyers, options, or the 59-book options ecosystem that's now the bulk
of this project's real activity.

BUILT, 6 planned steps + 2 gaps found afterward + 1 follow-up fix,
all against real data, all with the original 4 tabs left completely
untouched:

1. Options Grouped tab - ported FyersOptionsGroupedScreen's 4-group
   classification (New SL-cap / Profitable / Loss-making / No data
   yet), reading options_strategies.ALL_STRATEGIES directly instead
   of mobile's hand-maintained _allBooks copy (can't go stale the way
   mobile's list already has twice). TradeDetailDialog reuses
   strategy/options_transaction_costs.py's real cost function
   directly - no Dart-style port needed, this already runs in Python.
   Verified against real data: 26/4/18/11 = 59, matches mobile
   exactly.
2. Options Summary tab - flat sortable table, all 59 books, same
   ALL_STRATEGIES-direct approach. Totals cross-checked against
   Portfolio Aggregation's own number (-Rs 5,28,260.06) - matched
   exactly.
3. Options + Threshold Options tabs - one shared build_strategy_
   picker_tab() builder (strategy+index dropdowns instead of mobile's
   nested TabBars) instantiated twice, matching mobile's own re-use
   of FyersMultiStrategyOptionsScreen with different params. Ported
   both strategy-description dicts verbatim (English, not Marathi -
   the rest of this file's comments are English). Same index-override
   exceptions as mobile (vix_filter BANKNIFTY-only, st3_threshold_
   slcap NIFTY-only, st2_threshold_slcap BANKNIFTY-only) - verified
   these fire correctly against real data. Also added the strategy
   description into TradeDetailDialog (user's explicit request, so
   Options Grouped's detail view gets the same context without a
   separate screen).
4. History + News tabs - History intentionally overlaps the existing
   Paper Trading tab's Swing content (user chose to keep it, matching
   mobile's own screen structure, over consolidating) but the real
   gap it fills is Intraday (Best Trade) - reports/best_trade_
   portfolio.json had NO view anywhere on desktop before this. News
   ports reports/best_trade_shortlist.json's Market Headlines with
   sentiment coloring - genuinely new, no overlap anywhere.
5. Packaging - PyInstaller rebuild (TURION_Desktop.spec, unchanged),
   ~104MB .exe, actually launched and confirmed it stays running (not
   just that it builds) both before and after every later change in
   this entry.
6. TWO GAPS found after declaring parity "done" and asked directly
   ("sagala app zala ka?") - honest answer was no:
   - "Fyers (Test)" tab - the Fyers-SOURCED Swing+Intraday test
     engines (reports/fyers_test_portfolio.json, reports/fyers_best_
     trade_portfolio.json) had zero desktop visibility, completely
     separate from the yfinance-sourced History/Paper Trading tabs.
   - "Best Trade Shortlist" tab - mirrors mobile's BestTradeScreen:
     today's locked pick + reason + full ranked shortlist (reports/
     best_trade_pick.json) - the "why" behind today's entry decision,
     genuinely different content from History's closed-trade outcomes.
   Building these caught and fixed a real bug: the shared _fill_
   history_section() helper only read trade["PnL"], never falling
   back from/to "Net PnL" - correct for yfinance trades (which never
   carry a Net PnL field) but WRONG for the new Fyers-sourced trades
   (which do, and where PnL is the pre-cost gross figure) - fixed to
   prefer Net PnL when present, verified the fix changes nothing for
   the pre-existing yfinance History tab and fixes the new Fyers Test
   tab's numbers to match its real recorded Net PnL.

FOLLOW-UP, same day - "मला कशे बघू शकतो" (how do I even see this)
led to a real UX question: "is this app online, does it auto-
refresh?" - answered honestly that the 8 new tabs only re-read the
LOCAL git checkout, which does not update itself; asked "काय
करायला पाहिजे" (what would it take) to fix that properly:
  - REJECTED: an in-app `git pull` on a timer - this repo has other
    sessions committing/pushing to it regularly (this very session
    included), and an app-triggered pull firing automatically risks
    a real lock conflict with that unrelated git activity.
  - BUILT: every one of the 8 new tabs (plus TradeDetailDialog and
    the strategy pickers) now fetches its report JSON straight from
    GitHub's raw-content URL (same https://raw.githubusercontent.com/
    TuRaing/TURION_AI_Trader/main base mobile_app/lib/api.dart
    already uses, same cache-busting-with-timestamp trick) instead of
    a local file - new fetch_github_json() helper + a generic
    JsonFetchWorker(QThread) reused across History/News/Fyers Test/
    Best Trade Shortlist/strategy pickers (Options Grouped/Summary
    keep their own existing worker classes, just swapped their
    internal open() for the same helper). No git operations from the
    app at all - zero conflict risk. The original 4 tabs are
    UNCHANGED: Market Overview/Chart/Watchlist were already genuinely
    live (yfinance), Paper Trading still reads strategy.paper_
    trading.load_portfolio() untouched, per this repo's "never modify
    a working module" rule.
  Verified end-to-end against the real GitHub repo: every one of the
  8 tabs' numbers came back byte-identical to the earlier local-file
  test run, confirming the HTTP path is correct, not just that it
  doesn't crash. Rebuilt and relaunched the .exe again after this
  change (had to ask the user to close their already-open instance
  first - two copies were running from the earlier build).

FINAL STATE: 12 tabs total (4 original + 8 new), 367 tests passing
throughout every step. Real Android-app parity achieved, plus the 8
new tabs are now genuinely live (no manual sync step), which the
mobile app itself needed a whole separate architecture decision
(api.dart's raw-content-URL approach) to first solve.

==================================================

MOBILE APP VISUAL REDESIGN - PHASE 1 (15-Aug) - user's direct
feedback that the app "doesn't feel like a professional trading app -
boring and complicated." Explored via mockup BEFORE touching any
screen code (artifact-design skill, two rounds: a soft pastel-
Catppuccin direction, then a fluorescent/neon direction the user
actually wanted - "colour fluorescent type, app new असूदे" - plus a
6-option background comparison the user picked from, choosing option
E, a colorful 4-blob mesh gradient).

BUILT (foundation only, applies app-wide since it lives in shared
files):
  - theme.dart: full palette swap to fluorescent/neon (near-black
    #08060F base, electric violet #A855FF + cyan #00E5FF brand pair,
    neon success/danger/warning), same semantic token NAMES kept
    (bgColor/surfaceColor/accentColor/etc.) so no screen file needed
    changes just to keep compiling. New glowShadow() helper and
    meshBlobs constant (the 4 corner colors/positions from the
    approved mockup).
  - NEW widgets/mesh_background.dart: wraps a screen's body in the
    4-blob RadialGradient mesh over a solid bg base - applied ONCE in
    main.dart around the IndexedStack, so it's live behind all 10
    screens simultaneously without editing each one.
  - widgets/common.dart: HeroStat and StatPill redesigned to match
    the mockup - HeroStat's value now carries glowShadow(), StatPill
    got rounded corners + a subtle border + uppercase micro-labels.
  `flutter analyze` clean. Built (--dart-define=GITHUB_PAT, per the
  standing lesson) and VERIFIED LIVE on the phone: mesh background
  visible, HeroStat's PnL number showing the glow, active bottom-nav
  tab glowing cyan - confirmed via a real on-device screenshot, not
  just "it compiled."

NOT DONE YET (separate, bigger follow-up phases, explicitly scoped
but not built): Options Grouped's progressive-disclosure redesign
(show 2-3 per group + "+N more" instead of every book), bottom nav
10 tabs -> 5 + "More", and the mockup's new combined "Home" screen
(doesn't exist yet - a genuinely new screen, not a reskin).

==================================================

PNL ACCURACY FIX + CAPITAL TOP-UP (15-Aug) - triggered by a real,
sensible request: two heavily-losing books (simple_st1/NIFTY, Cash
down to Rs 8,200.51; st2/NIFTY, down to Rs 2,736.81) were close to
too capital-depleted to size a new trade at all (lots = cash //
(premium x lot_size) heading toward 0), which would silently stop
those books from generating any further real paper-trading evidence.

THE REAL RISK CAUGHT BEFORE ACTING: every PnL display built today
(Portfolio Aggregation, desktop Options Grouped/Summary, and the
mobile app's own Options Grouped/Summary screens) computed PnL as
"Cash minus Rs 1,00,000 initial capital" - a shortcut that is only
correct if Cash was NEVER touched except by real trades. Simply
topping up Cash to let a book keep trading would have made that
shortcut silently understate (or hide entirely) the book's real
historical loss the moment it started trading again from the new,
higher Cash baseline.

FIX: PnL is now computed as the SUM of every real Closed Trade's
"Net PnL" (falling back to "PnL" for older trade records without the
cost-model columns) - a number that lives entirely in the trade log,
completely unaffected by what Cash happens to be. Applied in 3
places that had all independently used the old Cash-minus-initial
shortcut:
  - strategy/portfolio_aggregation.py - new realized_pnl_from_trades()
    helper, used in compute_portfolio_summary(). 4 new tests,
    including one that asserts the same trade log gives identical PnL
    whether Cash is 8,200 or 1,00,000 - the actual guarantee this fix
    exists to provide.
  - desktop_app.py - GroupedRefreshWorker, SummaryRefreshWorker, and
    on_options_summary_refresh_done()'s total now import and reuse
    the same Python function directly (no duplicate logic).
  - mobile_app/lib/api.dart - new realizedPnlFromTrades() (same
    contract, Dart mirror), used by fyers_options_grouped_screen.dart
    and fyers_options_summary_screen.dart (including their page
    totals, which had the same Cash-minus-initial bug at the
    aggregate level).
Verified the fix is a true no-op for every untouched book: total
portfolio PnL before and after = -Rs 5,28,260.01 (5-cent rounding
diff from float summation order, not a real discrepancy) - matches
the earlier Portfolio Aggregation figure to the rupee.

THEN, safely: topped up both depleted books' Cash back to Rs
1,00,000 (Closed Trades left completely untouched - only the Cash
field changed). Re-verified total PnL after the top-up: still -Rs
5,28,260.01, unchanged to the cent - confirms the fix actually
delivers what it was built for.

`flutter analyze` clean, 371 Python tests passing (4 new). Rebuilt
and reinstalled the APK with both this fix and the Phase-1 redesign
together.

==================================================

PER-BOOK PASSBOOK TAB (15-Aug) - user's direct request, mobile_app/
lib/screens/fyers_options_summary_screen.dart: a bank-passbook-style
date-wise ledger, added as a second tab alongside the existing flat
Summary table. First cut computed one COMBINED ledger across all 59
books - user immediately corrected that ("मला total चं passbook नको
आहे, मला प्रत्येक strategy चं passbook पाहिजे" - not a total, a
passbook per individual strategy) - rebuilt as a dropdown-selected
per-book ledger instead.

Built entirely from data the Summary tab already fetches (no new
backend endpoint, no second network round-trip on dropdown change):
for every book, its own Closed Trades are grouped by Exit Time's
date, summed per day, and turned into a running-balance ledger
starting from that ONE book's own Rs 1,00,000 (not the combined
Rs 59,00,000) - stored alongside each row's existing current/profit
fields. The Passbook tab shows a book dropdown ("simple_st1 ·
NIFTY", etc.) followed by that book's own Date / Day's P&L / Balance
table, matching a real bank passbook's format.

`flutter analyze` clean. Built, installed, and VISUALLY CONFIRMED
correct on the phone by the user directly (on-device screenshotting
was blocked by a device-level restriction this session hit
repeatedly while verifying the redesign work above - not an app bug,
confirmed by checking the app had real window focus while capture
still silently failed).

==================================================

DESKTOP APP VISUAL REDESIGN - SAME FLUORESCENT DIRECTION (15-Aug) -
correction of a real mix-up: when the user first asked for the "not
professional, boring and complicated" redesign, they meant the
Desktop App (PySide6), not mobile - the mockup was built phone-
shaped and the user didn't catch the mismatch until AFTER the mobile
Phase 1 redesign had already shipped ("actullay mala desktop app
changala karayacha hota, tu mobile app kelas"). Applied the exact
same approved direction (near-black base, electric violet #A855FF +
cyan #00E5FF brand pair, neon success/danger/warning, 4-blob mesh
background, glow on hero numbers) to desktop_app.py, with explicit
instruction not to make it boring and to match the Android app.

KEY DIFFERENCE FROM THE MOBILE IMPLEMENTATION: Qt stylesheets (QSS)
can't stack multiple radial gradients the way CSS can (only one
gradient per background property), so the mesh is a REAL painted
background rather than a stylesheet trick - new MeshBackground(QWidget)
overrides paintEvent() to draw the same 4 QRadialGradient blobs at the
same relative positions/colors as widgets/mesh_background.dart's
meshBlobs, used as MainWindow's central widget so every tab sits on
top of it automatically. QGroupBox/QTableWidget/QTabBar all kept
their own opaque "surface" color (#12101d) in the rewritten
DARK_STYLESHEET so they read as cards over the mesh, same visual
language as the mobile cards. Glow itself uses QGraphicsDropShadow
Effect (apply_glow() helper) instead of CSS text-shadow - applied to
TradeDetailDialog's per-trade Net PnL label and the two most
prominent "hero" totals (Options Grouped's and Options Summary's
combined PnL labels).

GREEN/RED/YELLOW color constants updated to the same neon values as
mobile's successColor/dangerColor/warningColor - this alone flows the
new palette through every existing table cell/status color across all
12 tabs without touching each tab's own code, same "shared foundation,
minimal invasive changes" approach as the mobile Phase 1 work.

Verified: syntax clean, full offscreen smoke test (all 8 HTTP-backed
tabs) still returns byte-identical real data to every prior check
this session, rebuilt .exe launches and stays running. On-device
screenshot automation failed here too (captured the wrong window,
a tooling limitation not an app issue) - user visually confirmed the
redesign directly ("thik disla") before this was documented.

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

v0.0.42

Next Version

v0.0.43

==================================================

END OF DOCUMENT
