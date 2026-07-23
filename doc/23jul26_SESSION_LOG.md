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

Session Continued (same day, 23-Jul, second part)

Today's Achievements (part 2)

✅ User asked whether option "averaging" applies after
   fully closing a profitable trade and re-buying the same
   contract at a higher price - researched India's FIFO
   (First-In-First-Out) trade-matching rule (Income Tax
   Act 1961) and confirmed: no, once a position is fully
   closed, FIFO permanently matches that buy/sell pair -
   any later loss belongs only to the new, separate trade.
   Averaging only applies to a position that was partially
   (not fully) closed before re-entering.

✅ Researched SEBI's Feb-2025 algo trading circular at the
   user's request - the key retail-relevant rule is an
   Orders-Per-Second (OPS) threshold: under 10 orders/sec
   via API needs no formal algo registration, above it
   does. Confirmed this project (and any future Broker
   Integration) would stay well under that threshold
   (at most a handful of orders per day, not per second),
   so this regulatory framework doesn't apply to us.
   Also confirmed no specific registration fee is publicly
   documented for those who do cross the threshold, and
   it's moot for our use case regardless.

✅ Discussed a proposed 1-second-candle "cross the previous
   candle's close, hold a few seconds, take profit" options
   scalping idea - explained why this fails independent of
   the cost-per-trade question: bid-ask spread (especially
   wide on options), broker API execution latency
   (100-1000ms, incompatible with a few-second hold), a
   weak/noisy entry signal (crossing the previous candle's
   Close, unlike crossing its High, triggers very often),
   and the SEBI OPS threshold risk if fully automated at
   that frequency.

✅ MAJOR CORRECTION: user pointed out that a large
   (~Rs 10 lakh) trade's transaction costs would be a much
   smaller fraction of a few-thousand-rupee profit than
   the flat ~Rs 30/trade guess implied for small trades -
   researched Zerodha's actual published intraday equity
   charges and confirmed the user was right: real costs
   are almost entirely percentage-of-turnover (brokerage
   capped at Rs 20/order, STT 0.025% sell-only, exchange
   charges ~0.003%, stamp duty 0.003% buy-only, 18% GST),
   not a flat rupee number.

✅ Built strategy/transaction_costs.py implementing this
   real cost model and wired it into every 22-Jul backtest
   module (orb_vwap_backtest.py, vwap_pullback_backtest.py,
   ema_volume_breakout_backtest.py, multi_timeframe_
   backtest.py), replacing the flat-cost parameter
   entirely. Verified the model against hand-calculated
   examples (a ~Rs 11,000 trade, a Rs 10 lakh trade) before
   trusting it.

✅ Re-ran all of 22-Jul's key backtests with the corrected
   model. Losses shrank dramatically for cheap stock
   trades - e.g. ICICIBANK's ORB backtest: -Rs 6,583.76 ->
   -Rs 298.95 (roughly 22x smaller loss), HDFCBANK's ORB
   backtest landed near break-even at -Rs 144.20. VWAP
   Pullback losses similarly shrank (-Rs 1,200/-3,900 ->
   -Rs 46/-886 range). The Daily-aligned 15m/5m NIFTY combo
   barely changed (-Rs 547 -> -Rs 461) since an index-level
   "1 unit" position (~Rs 24,000+) makes percentage-based
   cost land close to the old flat guess anyway - the flat
   guess had mostly hidden the problem on cheap stocks, not
   index-level trades. No strategy flipped to net-positive,
   but the earlier "conclusively rejected" framing was more
   pessimistic than the real numbers warrant.

==================================================

Bugs Fixed (part 2)

• Every 22-Jul backtest module used a flat Rs 30/trade
  cost guess instead of the real percentage-based Indian
  equity transaction cost structure - not a code bug per
  se, but a materially wrong assumption baked into the
  Net PnL figures reported that day. Fixed by building
  strategy/transaction_costs.py and wiring it into all
  four affected modules.

==================================================

Next Session (updated)

1. Let the scheduled review (26-Jul 09:00 IST) run as
   planned.

2. Apply the same real transaction-cost model
   (strategy/transaction_costs.py) to the Watchlist and
   Best Trade Engine's own live evaluations, not just the
   22-Jul intraday-candidate backtests - carried over from
   the 21-Jul transaction-cost note, now with a proper
   model to use instead of a flat guess.

3. If pursuing the Daily-alignment intraday candidate
   further: sweep more SL/Target combos with the corrected
   cost model, and try combining with the BANKNIFTY
   Momentum+VIX options finding.

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
