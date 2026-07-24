# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260724-001

--------------------------------------------------

Date

24-Jul-2026

--------------------------------------------------

Version

v0.0.12 (no version bump - analysis-only script change,
no live-system changes)

==================================================

Today's Achievements

✅ Built an optional trailing Stop-Loss for the Daily-
   aligned 15m/5m NIFTY backtest (strategy/multi_
   timeframe_backtest.py, use_trailing_stop=True,
   trailing_atr_mult) - replaces the fixed ATR-multiple
   Target with a Stop-Loss that ratchets up as the trade
   makes new highs (never down), researched at the user's
   suggestion from 23-Jul.

✅ Tested three trail distances on the best-known combo
   (0.5x initial Stop-Loss, Daily-aligned, NIFTY, 60d):
   - 0.5x ATR trail (same as initial SL): hurt results -
     all 24 trades exited via whipsaw, gross PnL flipped
     negative (-Rs 20.37 vs the fixed-target's +Rs 42.03).
   - 1.0x ATR trail: best result found all week - gross
     +Rs 62.58, net -Rs 450.95 (beats the fixed-target
     approach on both gross and net PnL).
   - 1.5x ATR trail: worse than 1.0x (gives back more
     profit before exiting).

✅ Confirmed trail distance is its own tunable parameter,
   independent of the initial Stop-Loss distance - a
   naive "same distance as SL" assumption actively hurt
   results here, one more example (like Candlestick
   confirmation on 22-Jul) of a reasonable-sounding
   hypothesis that needed testing rather than trusting.

==================================================

Bugs Fixed

(None - analysis-only backtest extension, no live-system
changes.)

==================================================

Strategy Findings

• Trailing Stop-Loss (1.0x ATR trail distance) on the
  Daily-aligned 15m/5m NIFTY combo is the best intraday
  result found to date this week - still net-negative
  after real transaction costs, but closer to break-even
  than any other combo tested (ORB+VWAP+Volume, VWAP
  Pullback, plain 15m/5m, Momentum+VIX on NIFTY). Worth
  sweeping more trail-distance values and other starting
  SL combos before the 26-Jul review's next-steps decision.

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
   Engine results.

2. If pursuing the intraday candidate further: sweep more
   trail-distance values (e.g. 0.75x, 1.25x) and other
   initial SL starting points with the trailing-stop
   feature, and consider combining with the BANKNIFTY
   Momentum+VIX options finding.

3. Apply the real transaction-cost model
   (strategy/transaction_costs.py) to the Watchlist and
   Best Trade Engine's own live evaluations (carried over
   from 23-Jul).

4. Resume the FCM push-notification feature (paused
   21-Jul, not started) - get google-services.json +
   Firebase service-account key from the user first.

5. Commit Desktop App (PySide6), package as .exe (carried
   over).

6. Fix TATAMOTORS / LTIM ticker symbols (carried over).

7. Supertrend and CPR indicators (from the 22-Jul
   external strategy list) not yet built - not started.

==================================================

END OF SESSION
