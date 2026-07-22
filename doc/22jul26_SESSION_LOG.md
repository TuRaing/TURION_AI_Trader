# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260722-001

--------------------------------------------------

Date

22-Jul-2026

--------------------------------------------------

Version

v0.0.12 (no version bump - analysis-only scripts,
no live-system changes)

==================================================

Today's Achievements

✅ Checked real trading results across both engines:
   Watchlist Paper Trading got its first winning trade
   (BAJAJ-AUTO, Target hit, +Rs 643.92 - portfolio now
   +Rs 621.80 net of the earlier HDFCBANK loss). Best
   Trade Engine took 3 more real trades (ITC -Rs 0.81,
   DIVISLAB -Rs 16.44, BAJAJ-AUTO +Rs 23.50 via its
   first-ever Intraday Square-Off exit) - 5 total real
   outcomes now, net -Rs 59.19.

✅ Confirmed the Daily-timeframe strategy opens new
   positions in bursts (16 entries across only 5 of 9
   trading days since 11-Jul, days with zero new entries
   in between) - expected behavior for a daily-candle
   signal, not a monitoring gap.

✅ Built and ran the ORB+VWAP+Volume-spike backtest for
   stocks (strategy/orb_vwap_backtest.py,
   orb_vwap_backtest.py CLI) - the candidate researched
   21-Jul for the Best Trade Engine. Found ^NSEI (NIFTY
   index) has zero volume in yfinance (indices aren't
   traded instruments), so VWAP is undefined there -
   re-ran on individual stocks instead. Ran on 6 NIFTY 50
   stocks (60d, 5m candles): gross PnL roughly break-even
   but 189-252 trades per stock made real transaction
   costs (~Rs 30/trade) dominate - net PnL -Rs 5,500 to
   -Rs 7,750 per stock even at default parameters.

✅ Swept 48 parameter combinations (4 volume-spike
   thresholds x 6 ATR SL/Target ratios x 2 Opening-Range
   lengths) across the same 6 stocks - every single combo
   was net-negative after costs (-Rs 8,669 best case to
   -Rs 41,645 worst). Conclusively rejected this
   combination for stocks - the entry frequency is
   structurally too high for its tiny gross edge to
   survive real costs, not a tunable problem.

✅ Built and ran the Momentum(RSI)+India VIX backtest for
   options (strategy/momentum_vix_backtest.py,
   momentum_vix_backtest.py CLI) - the options candidate
   researched 21-Jul. No free option-premium history
   exists, so this measures directional accuracy on the
   underlying only (BUY CE when RSI>60 momentum + VIX in
   a percentile band, BUY PE on the mirror condition),
   explicitly caveated in the code and report as not a
   real rupee backtest.

✅ Found a real divergence between the two indices: on
   NIFTY, only 9/42 swept combos (VIX band x SL/Target)
   were positive - no reliable edge, rejected. On
   BANKNIFTY, 38/42 combos (90%) were positive - a
   consistent, not cherry-picked, result. Best combo
   (VIX 30th-70th percentile, 1.5x SL/4.0x Target ATR):
   38 trades, 42.11% win rate, +3,775.53 underlying
   points over 60 days (~+6.6% of BANKNIFTY's spot
   level).

✅ Refactored both new backtest modules to split data
   download from the core backtest loop
   (_run_on_data()), so the parameter sweeps could
   download each symbol once and re-run many
   combinations against it instead of re-fetching per
   combination - kept both original CLI scripts working
   identically (verified via a quick re-run matching the
   pre-refactor numbers) before running the sweeps.

==================================================

Bugs Fixed

(None - today was backtesting/research work on new,
analysis-only scripts, not live-system changes.)

==================================================

Strategy Findings

• Stocks intraday (ORB+VWAP+Volume): CONCLUSIVELY
  REJECTED. No parameter combination survives real
  transaction costs - entry frequency is structurally
  too high for the edge size. Do not revisit without a
  fundamentally different entry filter (much stricter,
  far fewer trades) or instrument choice.

• NIFTY options (Momentum+VIX): REJECTED. Only 21% of
  swept combos showed a positive directional edge on the
  underlying - not reliable.

• BANKNIFTY options (Momentum+VIX): PROMISING, not yet
  tradeable. 90% of swept combos positive - a real,
  consistent directional edge on the underlying. Still
  needs a real option-premium/theta-decay cost model
  before trusting this as profitable in practice
  (directional accuracy alone is necessary but not
  sufficient), and a net-of-costs check like the
  Watchlist/Best Trade engines are now held to.

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
   Engine results now that both are producing real data
   reliably.

2. If BANKNIFTY options gets pursued further: build a
   rough option-premium/theta-decay cost model (India
   doesn't have free historical option-chain data, so
   this will need an estimate/approximation, not real
   premiums) before considering it anywhere near live
   paper trading.

3. Resume the FCM push-notification feature (paused
   21-Jul, not started) - get google-services.json +
   Firebase service-account key from the user first.

4. Commit Desktop App (PySide6), package as .exe (carried
   over).

5. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

Session Continued (same day, 22-Jul, second part)

Today's Achievements (part 2)

✅ User shared a strategy list from another AI assistant
   (ChatGPT) claiming win rates like "VWAP Pullback:
   60-75%", "ORB: 55-70%" - reviewed critically rather
   than adopting it. Flagged that our own same-day
   backtest of a similar ORB+VWAP+Volume combination
   showed only 35-41% win rate and was net-unprofitable,
   directly contradicting the unsourced generic numbers -
   reinforced why we backtest on our own data instead of
   trusting claimed statistics.

✅ Built and tested 3 more candidates from that list, all
   REJECTED:
   - Plain ORB (no VWAP/Volume filter): worse than the
     combined approach (320-416 trades/stock, -Rs 9,500
     to -Rs 12,500 net loss).
   - VWAP Pullback (new entry style - bounce off VWAP in
     an established trend, vs the ORB breakout): 9-combo
     sweep across the same 6 stocks, every combo
     gross-negative.
   - 50 EMA + Volume Breakout (swing, daily candles):
     small sample (2-9 trades/instrument, 2y), mostly
     negative, underperforms the existing Daily strategy
     (which uses 6 combined engines via the AI Decision
     Engine, not just EMA+Volume) - confirms the
     multi-engine weighted-scoring design is what makes
     the Daily strategy work, not any single rule.

✅ Tested adding Candlestick-pattern confirmation
   (already part of the proven Daily strategy, but not
   used in any of today's new intraday backtests) to ORB,
   VWAP Pullback, and BANKNIFTY Momentum+VIX - hypothesis
   was it would strengthen the signal like it does for
   the Daily strategy. It didn't: no improvement on ORB
   or VWAP Pullback, and it measurably HURT the BANKNIFTY
   result (best combo dropped from +3,775.53 to +179.48
   points). Reasoned why: candlestick patterns are
   reversal signals, logically mismatched with
   continuation/momentum-style entries - a good example
   of a hypothesis that made sense but didn't pan out,
   reported honestly rather than forced.

✅ Confirmed the SL=1.5x/Target=4.0x, VIX 30-70 percentile
   band combo (BANKNIFTY, no candlestick) as today's best
   result: 38 trades, 42.11% win rate, +3,775.53
   underlying points - re-verified directly (not just
   from the sweep) at the user's request.

✅ Researched current (2024-2026) SEBI/NSE F&O rules at
   the user's request - found a regulatory change directly
   relevant to the BANKNIFTY finding: NSE discontinued
   BANKNIFTY's weekly options expiry (Nov-2024), now only
   one benchmark index per exchange keeps weekly expiry
   (NIFTY, not BANKNIFTY) - BANKNIFTY options are monthly-
   expiry only now. This changes the theta-decay
   assumptions any future option-premium cost model for
   this strategy must use. Also noted NIFTY/BANKNIFTY lot
   sizes increased substantially (NIFTY 25->75, BANKNIFTY
   15->30), raising real capital requirements.

✅ Explained FIFO (First-In-First-Out) trade matching to
   the user - clarified their question about "averaging"
   after buying an option, fully selling it for a profit,
   then re-buying the same contract at a higher price:
   confirmed no real averaging occurs once a position is
   FULLY closed (FIFO matches the original buy/sell pair
   permanently) - any later loss belongs only to the new,
   separate trade. Averaging only applies if the earlier
   position was partially (not fully) closed before
   re-entering.

==================================================

Next Session (updated)

1. Let the scheduled review (26-Jul 09:00 IST) run as
   planned.

2. If BANKNIFTY options gets pursued further: build an
   option-premium/theta-decay cost model that accounts
   for its now-monthly (not weekly) expiry cycle - see
   the regulatory note above. No free option-chain
   history exists, so this will need an estimate, not
   real premiums.

3. Resume the FCM push-notification feature (paused
   21-Jul, not started) - get google-services.json +
   Firebase service-account key from the user first.

4. Commit Desktop App (PySide6), package as .exe (carried
   over).

5. Fix TATAMOTORS / LTIM ticker symbols (carried over).

6. Supertrend and CPR indicators (from the same external
   strategy list) not yet built - would need ~2-2.5 hours
   for both indicators + backtests + tuning. Not started
   this session - user chose to stop for today.

==================================================

END OF SESSION
