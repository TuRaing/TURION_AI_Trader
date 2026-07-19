# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260719-001

--------------------------------------------------

Date

19-Jul-2026

--------------------------------------------------

Version

v0.0.9 → v0.0.10

==================================================

Today's Achievements

✅ Verified the 17-Jul work from a separate parallel
   session (News/Option Chain/Options Decision/Best
   Trade engines, Multi-Timeframe Engine, Best Trade
   Paper Trading, 3 new GitHub Actions workflows) -
   pulled, read every changed file, ran the full test
   suite (107 passed), confirmed the options-logic-
   stays-separate rule was respected, confirmed the
   found-and-fixed git-add bug (`|| true` for a file
   that legitimately may not exist yet) was correct.

✅ Checked accumulated real Watchlist Paper Trading
   results - 14 open positions, 0 closed trades.
   Verified this is NOT a monitoring bug: fetched
   live prices for the 5 oldest positions and
   confirmed all are still genuinely inside their
   Stop-Loss/Target range (-0.65% to +3.63% move).

✅ Re-ran the Daily-timeframe backtest to confirm the
   core swing strategy is unchanged and still
   profitable (2y, 1d: 21 trades, 33.3% win rate,
   +894.05 PnL) after the other session's additions.

✅ Exhaustive 15m-timeframe tuning sweep (15 SL/Target
   combos, filters on) - confirmed conclusively that
   15m cannot be fixed by parameter tuning; every
   combo net-negative, best only -259.67.

✅ Built strategy/multi_timeframe_backtest.py +
   mtf_backtest.py - backtests the 15m(trend)/5m
   (entry) alignment core of the live Multi-Timeframe
   Engine (1m confirmation can't be backtested, Yahoo
   only keeps ~7 days of 1m history). Explicitly
   analysis-only per the user's request - not wired
   into any paper trading.

✅ Swept SL/Target (fixed % and ATR-based) for the
   15m/5m alignment approach - best found (0.5x SL /
   1.5x Target ATR) is roughly break-even (+4.00 PnL,
   72 trades) on NIFTY - concluded there is no
   evidence to drop the live engine's 1m confirmation
   requirement.

✅ Added confidence-based position sizing (risk 1-2%
   of current equity per new Daily-strategy entry,
   scaled by AI Decision confidence 60-100%) and a
   MAX_CONCURRENT_POSITIONS=15 portfolio-risk cap to
   strategy/paper_trading.py. Backward compatible -
   only affects new entries, not the 14 already open.

✅ 6 new unit tests for position sizing + the
   concurrent-position cap (116 total passing).

==================================================

Bugs Fixed

(None new today - yesterday's git-add bug from the
parallel session was verified, not re-fixed.)

==================================================

Strategy Findings (see doc/PROJECT_STATUS.md ->
Known Issues for the full writeup)

• Daily (1d) timeframe: the only timeframe with a
  real backtest edge. Keep building on this one.

• 15m standalone: conclusively unprofitable, cannot
  be tuned into profitability. Context/analysis only,
  never a standalone signal.

• 15m/5m alignment (Multi-Timeframe core, no 1m):
  roughly break-even at best - no real edge, and no
  reason to loosen the live engine by dropping 1m.

• Live Best Trade Engine (15m/5m/1m): still has zero
  real trade outcomes to evaluate - needs more real
  time before drawing conclusions.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data.
Report Engine displays. Excel Engine stores history.
Options logic kept fully separate from normal
NIFTY/stock trading logic.

Claude never executes a real trade - final action is
always the user's.

==================================================

Next Session

1. Keep observing Watchlist Paper Trading and Best
   Trade Engine for real closed-trade outcomes -
   still the top priority before any further tuning

2. Fix TATAMOTORS / LTIM ticker symbols

3. Commit Desktop App (PySide6) + Android App
   (Flutter, mobile_app/), package Desktop as .exe

4. Select broker (Upstox / Angel One) → Broker
   Integration

5. Once enough real Daily-strategy trades have
   closed, consider a proper Opening-Range-Breakout
   or VWAP-based approach for intraday instead of
   reusing the EMA/RSI swing logic - the user was
   told this is a bigger (2-3 hour) task, not started
   yet

==================================================

END OF SESSION
