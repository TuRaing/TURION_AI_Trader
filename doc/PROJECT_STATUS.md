# TURION AI Trader

PROJECT STATUS

==================================================

Project

TURION AI Trader

--------------------------------------------------

Version

v0.0.8

--------------------------------------------------

Build Status

🟢 Stable

--------------------------------------------------

Project Started

01-Jul-2026

--------------------------------------------------

Last Updated

17-Jul-2026

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

✅ Best Trade Engine + daily_best_trade.py +
   GitHub Actions workflow (10:00 IST daily) -
   ranks Nifty 50 stocks + NIFTY/BANKNIFTY
   options + news sentiment on one scale and
   locks the single highest-probability
   intraday pick, with a top-5 shortlist as
   backup context. Recommendation only - same
   "Claude never executes a real trade" rule
   applies.

✅ Best Trade Paper Trading - if the locked
   pick is an equity trade, it opens a real
   intraday paper position (own portfolio file,
   separate from the swing-style watchlist
   paper trading) and force-closes by 15:15 IST
   via square_off_best_trade.py + a second
   GitHub Actions workflow, so it never silently
   carries over like a swing trade. Index option
   picks stay recommendation-only (no live
   premium feed to mark P&L against).

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

Watchlist Scan (stocks + indices)
+ News Engine (RSS sentiment)
+ Option Chain Engine → Options Decision Engine
  (NIFTY / BANKNIFTY CE / PE)

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

• Best Trade Report       → every ~30 min, ~09:35-14:05
                           IST, Mon-Fri (daily_best_trade.py)
                           - skips the scan once today's
                           pick is already open, and stops
                           opening new ones after 14:45 IST

• Best Trade Square-Off   → 15:15 IST, Mon-Fri
                           (square_off_best_trade.py)

• Portfolio state auto-committed back to repo

• All alerts delivered to Telegram (now logs
  success/failure in the Action run output)

• CONFIRMED WORKING 13-Jul: both workflows fired
  automatically on schedule and opened 7 real paper
  positions (HDFCBANK, ICICIBANK, BAJFINANCE,
  SUNPHARMA, TITAN, BAJAJ-AUTO, TECHM)

==================================================

KNOWN ISSUES

• Option Chain / OI still blocked from datacenter
  IPs (NSE 403) on GitHub Actions - the new engine
  detects this and returns "Available: False"
  instead of crashing, but the Best Trade Engine
  will only get real PCR/Max Pain confirmation
  when run from a non-blocked (e.g. home) network.

• News Engine's RSS feeds (Moneycontrol/ET) were
  blocked by this dev sandbox's outbound proxy
  during testing (403) - unconfirmed whether
  GitHub Actions' runners can reach them; watch
  the first scheduled run's output for "Headlines
  fetched: 0" to check.

• TATAMOTORS.NS / LTIM.NS - no Yahoo data,
  need correct symbols.

• 15m strategy still weak (needs tuning).

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

Run automated Paper Trading + new Daily Best
Trade Report 1-2 weeks, review Telegram +
Excel ("Best Trade" sheet) results - confirm
whether GitHub Actions can reach the RSS news
feeds and whether NSE still blocks the option
chain from that network

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

v0.0.8

Next Version

v0.0.9

==================================================

END OF DOCUMENT
