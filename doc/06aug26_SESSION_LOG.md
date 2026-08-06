# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260806-001 (cloud session - claude.ai/code) then
S20260806-002 (local machine session - Claude Code Desktop,
D:\TURION_AI_Trader) same day, once a Flutter build + adb
install was needed to actually fix the reported app bug.

--------------------------------------------------

Date

06-Aug-2026

--------------------------------------------------

Version

v0.0.15 (no version bump - a real bug fix + backtest findings
shipped, but not milestone-numbered)

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

✅ FIXED: the app's "yfinance"/"History" blank-white-screen bug.
   Data-level checks (JSON validity, missing/null fields) had found
   nothing because the bug wasn't in the data - a screenshot from
   the user (a flat gray box, no spinner/error/text) revealed it as
   Flutter's default release-mode crash screen instead. Root cause:
   portfolio_screen.dart / history_screen.dart / fyers_portfolio_
   screen.dart / fyers_options_screen.dart all called `_buildBody()`
   EAGERLY as a constructor argument to RefreshIndicator, before the
   loading/hasData check that's meant to gate it - so `_portfolio!`
   null-check-crashed on the first frame (or after any failed
   fetch), every time. Fixed by guarding the call so _buildBody()
   only runs once _portfolio is non-null, in all 4 screens; also
   added a 15s timeout to api.dart's fetchJson so a stalled request
   fails into a Retry button instead of hanging forever. flutter
   analyze clean. Switched to a local machine session to actually
   build + adb-install the fix (phone connected + authorized live
   this session) - VERIFIED the new APK installs and the fetch/
   timeout logic behaves as expected.

✅ FIXED: strategy/fyers_options_paper_trading.py had no entry-time
   gate (unlike the equity Best Trade engine's 10:00-14:15 IST
   window) - found while answering the user's "is the options data
   real?" question about a day with 10 real trades. Confirmed via
   the real GitHub Actions run history (public API, 129 runs,
   every ~1 min, zero gaps, all success) that the automation itself
   was running exactly as designed - the outsized first trade
   (+24.03% "Target" in under 6 min) traced instead to its Entry
   Time being 09:11:51 IST, before NSE's 09:15 market open, meaning
   it traded on pre-open auction quotes rather than real continuous-
   market prices. Added MARKET_OPEN_TIME = (9, 15) - check_or_open()
   now skips opening a new position before then (an already-open
   position still gets checked/closed normally). 3 existing unit
   tests still pass.

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

✅ Intraday (Best Trade core) full-50-symbol, 1-year backtest
   COMPLETED (after hitting Fyers' midnight daily-token expiry
   TWICE overnight - first hit documented 05-Aug, second hit and
   resumed earlier today - see above). Final result: 48/50 symbols
   (TATAMOTORS.NS/LTIM.NS still have no valid Fyers symbol),
   7,680 total trades, 29.48% win rate, TOTAL NET PnL -31,200.17
   (raw points, not rupee-normalized). ZERO of 48 symbols
   profitable - even worse than the Swing finding above (18/49
   profitable). Worst 5: MARUTI.NS (-3,815), BAJAJ-AUTO.NS
   (-3,206), EICHERMOT.NS (-2,335), APOLLOHOSP.NS (-2,027),
   DIVISLAB.NS (-1,936). Combined with the Swing result, this is
   now strong, large-sample evidence that BOTH of this project's
   core engines - not just one - are net-negative on real Fyers
   data at real scale, not just an isolated bad-window result.

✅ Reset reports/fyers_options_portfolio.json back to a fresh
   ₹1,00,000/no-trades state (the earlier testing-artifact trades
   were cluttering the record) once the automation was confirmed
   live and running properly on real market hours.

✅ Reviewed Fyers Swing/Intraday status mid-session at the user's
   request: Swing still 15 open positions, ₹1,00,000 cash, nothing
   closed yet; Intraday still has never opened a position.

✅ ROOT CAUSE FOUND AND FIXED: why Intraday has never opened a
   position, and why Swing's 15 open positions weren't getting
   fresh checks. Two compounding bugs, found by actually digging
   into the real GitHub Actions run history instead of assuming
   the code was the problem:

   1. The "Fyers Scheduled Check Trigger" cron-job.org job (meant
      to hit fyers_scheduled_check.yml every ~5 min, running
      Swing + Intraday together) had simply never been created -
      the cron-job.org dashboard showed only 4 Fyers/yfinance jobs
      plus one unrelated inactive leftover ("Best Trade Entry Scan
      Trigger (Copy)"), no Scheduled Check job at all. Confirmed
      via the workflow's real run history: only 3 runs total ever
      (vs. Options Watch's 129 runs that same morning alone).
      FIXED: user repurposed the inactive leftover job - renamed
      it, pointed its URL at fyers_scheduled_check.yml/dispatches,
      set the Mon-Fri/~5-min/market-hours schedule, enabled it,
      matching the working jobs' header/body pattern. Verified via
      Test Run - landed on GitHub Actions successfully.

   2. A second, more insidious bug: even the runs that DID fire
      correctly weren't actually saving their results. Manually
      triggered the workflow to check "is everything correct" -
      it reported "success" and printed real output ("0 Swing
      event(s)", "No aligned BUY candidates"), but reports/fyers_
      test_portfolio.json's Last Checked timestamps stayed stuck
      on 05-Aug. Pulled the actual run log (GitHub API) and found
      why: all 3 Fyers workflows retried a rejected git push by
      `git fetch` + `git reset --hard origin/main` - which
      DISCARDS the just-computed results entirely (confirmed live:
      "[main 70bf4e7] Update Fyers state... 2 files changed" then
      "Push rejected" then "HEAD is now at 9e88c4e" - that commit,
      and the real Swing/Intraday check it represented, gone).
      This kept happening because fyers_options_watch.yml pushes
      to the same branch every ~1 min, making a push conflict
      likely on almost every 5-min Scheduled Check run. FIXED in
      all 3 workflows (fyers_scheduled_check.yml, fyers_options_
      watch.yml, fyers_trigger.yml): commit once up front, then on
      a push conflict, rebase that commit onto the latest origin
      and retry - never discard it. VERIFIED live: re-triggered
      after the fix, Last Checked timestamps advanced to today's
      real time for the first time.

✅ FIXED a second real bug the same investigation surfaced: once
   the cron job + git-race fixes above were live, the day's first-
   ever real Fyers Intraday position (SBIN, opened 14:07 IST once
   converted from the raw UTC-stored timestamp) still wouldn't
   close despite being well past its 14:45 IST square-off time on
   every 5-min check. Root cause in fyers_daily_best_trade.py's
   monitor_open_position(): after a close, portfolio["Position"]
   becomes None, but the status line read it back via
   `portfolio.get('Position', {}).get('Name', symbol)` - dict.get()'s
   default only applies when the KEY is missing, not when its
   value is None, so this crashed with 'NoneType' object has no
   attribute 'get' on every single close attempt. The close itself
   computed correctly in memory every time, but the crash happened
   BEFORE save_best_trade_portfolio() could persist it - so the
   position kept reappearing as "still open" on the next check,
   indefinitely. Fixed by reading the position's name before the
   close call instead of after. VERIFIED live: re-triggered, SBIN
   closed for real this time (Entry ₹1,081.90 -> Exit ₹1,085.00,
   Intraday Square-Off, PnL +₹3.10) - the first real, complete
   Fyers Intraday trade this project has ever produced.

✅ FOUND AND FIXED a related app gap while confirming the SBIN
   close: fyers_portfolio_screen.dart's "Fyers" tab only ever
   showed the Intraday section's currently-OPEN position - once a
   trade closed it just silently reverted to "No open intraday
   position today" with no way to see what had just happened. Added
   a ClosedTradeCard fallback showing the latest Intraday closed
   trade when there's no open position, matching the pattern
   Swing's own EventBanner already used. flutter analyze clean;
   rebuilt and reinstalled the APK (second local build this
   session).

✅ Reviewed today's Fyers Options live results at the user's
   request: 49 real trades, 61.2% win rate (30 wins/19 losses) -
   but still a NET LOSS of -₹3,128.35 (Cash ₹1,00,000 -> 96,871.65).
   Cause: TARGET_NET_PCT=2.0 vs STOP_LOSS_PCT=5.0 is an unfavorable
   risk/reward ratio - breakeven needs >71% win rate at those exact
   levels (5/(5+2)), and real overshoot past the nominal Stop-Loss
   (documented earlier this session) makes losses run even bigger
   in practice. Today's 61.2% win rate, while respectable-looking
   on its own, isn't enough to overcome losses that are ~2.5x the
   size of wins. Flagged as a real design issue worth revisiting
   (e.g. a more symmetric or target>stop ratio) - not changed yet,
   just documented.

✅ Updated doc/PROJECT_STATUS.md with all of the above (full-
   capital Swing+BankNifty finding, completed Intraday 50-symbol
   backtest, the testing-artifact trade caveat, the blank-screen
   bug fix, the options entry-time-gate fix, the missing-cron-job +
   git-race fixes, the Intraday close-crash fix, the app's Intraday-
   closed-trade display fix, today's Options risk/reward finding).

==================================================

Next Session Priorities

1. Watch the now-fixed automation over the next few real trading
   days: confirm Swing's Last Checked keeps advancing every ~5 min
   and Intraday keeps getting real, persisted open/close cycles
   (not just the one SBIN trade) without another silent-loss
   regression.

2. Reconsider the Options engine's TARGET_NET_PCT/STOP_LOSS_PCT
   ratio (currently 2.0/5.0, needs >71% win rate to break even) -
   today's 61.2% win rate still lost money. A more symmetric ratio
   (or target > stop) is worth testing before trusting this
   strategy's real-money potential.

3. Follow up on WHY the Daily-timeframe Swing strategy's original
   "proven" claim differs so much from today's large-sample real-
   rupee finding (-₹1,28,490.80 across 49 symbols, only 18
   profitable) - and now that Intraday's full-50-symbol result is
   in too (0/48 profitable, -31,200 points), the same question
   applies there even more strongly - not yet investigated.

4. Build the STCG (~20%) after-tax column the user asked for,
   alongside the existing pre-tax transaction-cost model, and
   re-show the full-capital results as pre-tax vs. after-tax.

5. Decide next strategy research direction now that BOTH "proven"
   baselines are in question: a futures-based approach (cont_flag=1
   gives real multi-year continuous data, unlike options) or a
   symbol-selective approach based on which of the profitable
   symbols actually showed a real edge, instead of treating the
   watchlist/intraday universe as one uniform strategy.

6. Carried over: apply strategy/transaction_costs.py's real
   cost model to the live Watchlist/Best Trade Engine's own
   ongoing evaluations (not just the new backtests).

7. Carried over: Commit Desktop App (PySide6), package as .exe.

8. Carried over: Fix TATAMOTORS / LTIM ticker symbols (still no
   valid Fyers symbol either, same root problem as yfinance).

==================================================

END OF SESSION
