# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260723-001

--------------------------------------------------

Date

23-Jul-2026

--------------------------------------------------

Version

v0.0.12 (no version bump - analysis-only script change,
no live-system changes)

==================================================

Today's Achievements

✅ Checked real trading results across both engines:
   Watchlist Paper Trading closed 2 more trades, both
   Stop Loss (INDUSINDBK -Rs 40.31, ADANIPORTS -Rs
   58.53) - portfolio still net +Rs 522.96 overall
   thanks to the 22-Jul BAJAJ-AUTO win. Best Trade Engine
   took BAJAJ-AUTO twice today (Rs 128.58 win via Target,
   Rs 10.50 win via Intraday Square-Off) - now net
   positive overall for the first time (+Rs 79.89 across
   7 real trades).

✅ Investigated why the Best Trade Engine re-entered
   BAJAJ-AUTO twice same-day - confirmed this is
   intentional design (documented in daily_best_trade.py):
   an early close (before the 14:15 IST entry cutoff)
   leaves the door open for the very next scan to find a
   new entry, even on the same symbol, if its 15m/5m/1m
   alignment still holds.

✅ Investigated why HCLTECH (80% shortlist confidence,
   the day's highest) wasn't picked instead of BAJAJ-AUTO
   (70%) - reconstructed the exact historical moment
   (no look-ahead) and found HCLTECH's 15m trend Bias was
   Neutral at that scan time, failing the live Multi-
   Timeframe Engine's alignment rule (trend must be
   non-Neutral) even though its shorter timeframes (5m,
   1m) were already Bullish - correct behavior, not a bug.

✅ At the user's suggestion, researched adding a 4th
   alignment layer to the 15m(trend)/5m(entry) backtest -
   also requiring the Daily timeframe's Bias to agree,
   since Daily is the only timeframe with a proven edge.
   Added require_daily_alignment as an optional parameter
   to strategy/multi_timeframe_backtest.py (backward
   compatible, off by default).

✅ Found and fixed a real bug while adding this: yfinance
   returns daily candles as timezone-naive while intraday
   candles are timezone-aware (Asia/Kolkata) - merge_asof
   was raising a dtype MergeError until the daily index
   was localized to match.

✅ Tested the Daily-alignment filter on NIFTY using the
   previously-best combo (0.5x SL/1.5x Target ATR, from
   the 19-Jul tuning sweep): trades dropped 67->20 over
   60 days, win rate improved 35.82%->45.0%, max drawdown
   dropped 118.21->43.29, and the net-of-transaction-cost
   loss shrank roughly 4x (-Rs 1,950 -> -Rs 547 at an
   estimated Rs 30/trade). Still net-negative, so not
   tradeable as-is, but a genuine, measurable improvement
   - a useful contrast with the same day's earlier
   Candlestick-confirmation experiment (22-Jul), which
   hurt every strategy it was tested on. Confirms that
   "add more filters" isn't universally good or bad - it
   depends on whether the added filter carries real
   signal for that specific strategy type.

==================================================

Bugs Fixed

• strategy/multi_timeframe_backtest.py - tz-naive vs
  tz-aware datetime mismatch between yfinance's daily and
  intraday data broke pd.merge_asof. Fixed by localizing
  the daily index to the intraday data's timezone before
  merging.

==================================================

Strategy Findings

• Daily-timeframe alignment, added as a 4th filter to the
  15m/5m/(1m) Multi-Timeframe alignment core: IMPROVES
  trade quality (higher win rate, much lower drawdown,
  smaller net-of-cost loss) versus the 15m/5m-only
  version, though still not net-profitable at the combo
  tested so far. Worth further tuning (more SL/Target
  combos) before the 26-Jul review's next-steps decision.

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

1. Let the scheduled review (26-Jul 09:00 IST) run as
   planned - review real Daily-strategy + Best Trade
   Engine results (both now producing genuinely useful
   data, including Best Trade Engine's first net-positive
   day).

2. If pursuing the intraday candidate further: sweep more
   SL/Target combos with require_daily_alignment=True
   (only one combo tested so far) - see if a net-positive
   combo exists, and try combining with the BANKNIFTY
   Momentum+VIX options finding.

3. Resume the FCM push-notification feature (paused
   21-Jul, not started) - get google-services.json +
   Firebase service-account key from the user first.

4. Commit Desktop App (PySide6), package as .exe (carried
   over).

5. Fix TATAMOTORS / LTIM ticker symbols (carried over).

6. Supertrend and CPR indicators (from the 22-Jul
   external strategy list) not yet built - not started,
   user chose to stop.

==================================================

END OF SESSION
