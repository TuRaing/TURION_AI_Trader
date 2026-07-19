# TURION AI Trader

PROJECT STATUS

==================================================

Project

TURION AI Trader

--------------------------------------------------

Version

v0.0.10

--------------------------------------------------

Build Status

🟢 Stable

--------------------------------------------------

Project Started

01-Jul-2026

--------------------------------------------------

Last Updated

19-Jul-2026

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

🟡 Android App                (Flutter APK built, installed on phone,
                               reads live Portfolio from GitHub - not
                               committed to repo yet)

⬜ Algorithmic Trading        (needs broker)

⬜ TURION AI Trader v1.0

--------------------------------------------------

Progress: 23 / 29 milestones done (~79%), 2 more in-progress
(Desktop + Android both working locally, pending commit)

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
                           08:37-16:22 IST, Mon-Fri

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
                           every run regardless of time

• Best Trade Square-Off   → 14:45 IST, Mon-Fri (45 min
                           before NSE's 15:30 close)
                           (square_off_best_trade.py)

• Portfolio state auto-committed back to repo

• All alerts delivered to Telegram (now logs
  success/failure in the Action run output)

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

• Desktop App + Android App verified working
  locally, but not yet committed to the repo.

• A separate Claude session (branch
  claude/tula-repocha-actress-hob5j0) fixed the
  Telegram/cron issue in parallel - merged as PR #1.
  Watch for multiple sessions editing the same repo
  at once going forward.

==================================================

NEXT DEVELOPMENT PLAN

Priority 1

Run automated Paper Trading + the three Best
Trade workflows for real over 1-2 weeks, review
Telegram + Excel ("Best Trade" sheet) results -
manual workflow_dispatch runs already confirmed
each workflow individually (RSS/option chain
reachable, git-add bug fixed), but real entries/
exits on live intraday data and concurrent-cron
behavior across all three still need observing

--------------------------------------------------

Priority 2

Commit Desktop App (PySide6) + Android App
(Flutter, mobile_app/) to the repo,
package Desktop as .exe (PyInstaller)

--------------------------------------------------

Priority 3

Fix TATAMOTORS / LTIM ticker symbols

--------------------------------------------------

Priority 4

Select Broker (Upstox / Angel One - free API)
→ Broker Integration (also unlocks a paid/
reliable Option Chain data source as an
alternative to the free NSE scrape)

--------------------------------------------------

Priority 5

Tune the News Engine's keyword lexicon and
Best Trade Engine's weighting once 1-2 weeks
of real daily picks can be compared against
outcomes

--------------------------------------------------

Priority 6

Algorithmic Trading (after broker, user-supervised)

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

v0.0.10

Next Version

v0.0.11

==================================================

END OF DOCUMENT
