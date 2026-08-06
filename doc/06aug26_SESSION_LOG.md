# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260806-001 (cloud session - claude.ai/code)

--------------------------------------------------

Date

06-Aug-2026

--------------------------------------------------

Version

v0.0.15 (no version bump - findings/investigation session,
no new shipped feature)

==================================================

Today's Achievements

✅ SESSION START: per CLAUDE.md's rule, fetched origin and
   fast-forwarded ~6 automated "[skip ci]" portfolio-update
   commits (paper trading / best trade portfolio auto-commits
   from the live GitHub Actions workflows) - no other-session
   branches found, no conflicts.

✅ Reviewed the Fyers Options portfolio's current live state
   at the user's request (reports/fyers_options_portfolio.json):
   Cash ₹1,25,982.63 (up from ₹1,00,000 initial), no open
   position, 3 closed trades. Also checked reports/fyers_test_
   portfolio.json (Swing: 15 open positions, ₹1,00,000 cash,
   nothing closed yet) and confirmed reports/fyers_best_trade_
   portfolio.json still does not exist (no Fyers Intraday
   position has ever opened).

⚠️ TESTING ARTIFACT IDENTIFIED: the big +₹26,472.24 (+26.47%)
   "Target" win driving that Cash increase is NOT a trustworthy
   live result - its Entry Time (05-Aug 00:14:54 IST) falls
   outside NSE market hours, a side effect of this session's
   own overnight manual fyers_trigger_run.py test runs while
   debugging login/automation. Documented in PROJECT_STATUS.md's
   Known Issues so this doesn't get mistaken for a validated
   strategy result later - only trades opened during real market
   hours by the scheduled workflows (not manual triggers) should
   count as evidence.

🔍 INVESTIGATED (not yet resolved): user reported the app's
   "yfinance" and "History" tabs show a blank/white screen while
   "Fyers"/"Options" load fine. Checked reports/paper_portfolio.
   json, reports/best_trade_portfolio.json, reports/candles.json
   for JSON validity and missing/null fields (PnL, Entry Price,
   Exit Price on every Closed Trade; required keys on every Open
   Position) - all structurally clean, no obvious cause found.
   Read history_screen.dart in full against that data shape - no
   mismatch spotted. portfolio_screen.dart (the actual "yfinance"
   tab) not yet read. Asked the user for a screenshot - confirmed
   "पूर्ण पांढ" (completely white) but no image received yet.
   REMAINS OPEN - see Next Session Priorities.

✅ Full-capital, real-rupee backtest completed: NIFTY 50 +
   Bank Nifty (^NSEBANK), ₹1,00,000 deployed independently per
   symbol (not shared across the watchlist, per the user's
   explicit request), 2 years real Fyers daily data, the
   existing "proven" Daily-timeframe combo (1.5x SL/3x Target
   ATR, filters on, strategy/transaction_costs.py's real cost
   model applied per trade). Result: 477 trades across 49/51
   symbols (TATAMOTORS.NS/LTIM.NS still have no valid Fyers
   symbol), 31.03% win rate, TOTAL NET PnL -₹1,28,490.80. Only
   18/49 symbols individually profitable. Bank Nifty on its own:
   10 trades, 20% win rate, -₹5,417.21. See PROJECT_STATUS.md's
   Known Issues for the full winner/loser breakdown. This
   confirms, in real rupee terms, 05-Aug's raw-points finding
   that the long-standing "proven" Swing strategy is actually
   net-negative at real sample size - a direct contradiction of
   this project's own repeated "proven" framing that still needs
   root-cause follow-up (smaller/luckier original sample? fewer
   symbols? different exact parameters? yfinance-vs-Fyers data
   difference?). STCG tax (~20%) is intentionally NOT yet in this
   figure - user asked for it as a separate after-tax column
   alongside pre-tax; strategy/transaction_costs.py only models
   broker/exchange charges today, tax modeling not yet built.

🔄 Intraday (Best Trade core) full-50-symbol, 1-year backtest:
   hit Fyers' midnight daily-token expiry a SECOND time
   overnight (first hit documented 05-Aug) - the resume attempt
   itself failed entirely (all 45 remaining symbols errored
   "Could not authenticate the user" since the token had already
   expired before that script started). Resumed again this
   morning after a fresh login, reusing the 5 already-completed
   results; IN PROGRESS as of this log (13/50 done: RELIANCE,
   TCS, HDFCBANK, ICICIBANK, INFY, HINDUNILVR, ITC, SBIN,
   BHARTIARTL, KOTAKBANK, LT, AXISBANK, BAJFINANCE) - all 13
   net-negative so far, consistent with the Swing finding above.

✅ Updated doc/PROJECT_STATUS.md with all of the above (full-
   capital Swing+BankNifty finding, Intraday resume status, the
   testing-artifact trade caveat, the white-screen bug as an
   open item).

==================================================

Next Session Priorities

1. Diagnose the "yfinance"/"History" blank-screen bug - read
   portfolio_screen.dart (not yet checked), get a screenshot
   from the user if still reproducible, consider whether this
   is a transient app-cache issue vs. a real code bug.

2. Let the Intraday full-50-symbol backtest finish (currently
   13/50) and record the final aggregate in PROJECT_STATUS.md.

3. Follow up on WHY the Daily-timeframe Swing strategy's
   original "proven" claim differs so much from today's large-
   sample real-rupee finding (-₹1,28,490.80 across 49 symbols,
   only 18 profitable) - not yet investigated.

4. Build the STCG (~20%) after-tax column the user asked for,
   alongside the existing pre-tax transaction-cost model, and
   re-show the full-capital results as pre-tax vs. after-tax.

5. Decide next strategy research direction now that the
   "proven" baseline is in question: a futures-based approach
   (cont_flag=1 gives real multi-year continuous data, unlike
   options) or a symbol-selective approach based on which of
   the 18 profitable symbols actually showed a real edge,
   instead of treating the watchlist as one uniform strategy.

6. Carried over: apply strategy/transaction_costs.py's real
   cost model to the live Watchlist/Best Trade Engine's own
   ongoing evaluations (not just the new backtests).

7. Carried over: Commit Desktop App (PySide6), package as .exe.

8. Carried over: Fix TATAMOTORS / LTIM ticker symbols (still no
   valid Fyers symbol either, same root problem as yfinance).

==================================================

END OF SESSION
