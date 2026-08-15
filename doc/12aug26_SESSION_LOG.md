# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260812-001 (local machine session - Claude Code Desktop,
D:\TURION_AI_Trader) - new session, continuing from 07aug26_SESSION_
LOG.md (which itself spanned 07 through 10-Aug).

--------------------------------------------------

Date

10, 11, 12-Aug-2026 (monitoring/Q&A across 3 real trading days, no
code changes until this entry)

--------------------------------------------------

Today's Achievements

No new features this stretch - user asked repeatedly to check real
live trading days as they accumulated (cron/login health, which
strategies traded vs which didn't and why, running P&L per strategy)
rather than build anything new. Two real findings worth carrying into
the 14-Aug review, written up in doc/PROJECT_STATUS.md's "LIVE
MONITORING FINDINGS, 10/11/12-Aug" entry:

✅ Threshold group's daily profit-lock genuinely helps on NIFTY (2/2
   real trading days: one early win pushes past the Rs 2,000 lock,
   strategy correctly stops for the day, protects the gain) but does
   NOT help on BANKNIFTY (the RSI signal there loses too often for
   cumulative profit to ever reach the lock threshold within a day -
   e.g. simple_st1_threshold/BANKNIFTY took 15 trades in one day on
   10-Aug without the lock ever engaging). Decided: evaluate
   threshold's NIFTY and BANKNIFTY legs separately at 14-Aug, not as
   one verdict - BANKNIFTY needs a loss-lock or a signal change, not
   more time on the same profit-lock-only gate.

✅ Computed real trade-frequency rates per strategy family from actual
   live data, to answer "how many days until we can trust the win
   rate" per strategy (not one answer - varies hugely): simple_st1/
   st2/st3 (~24 trades/day) already have a large, reliable sample.
   oi_footprint (~4 trades/day) will reach a trustworthy ~30-trade
   sample within a few days of 14-Aug, not by 14-Aug itself. vix_
   filter and credit_spread (~0.5-0.7 trades/day each, rare double-
   condition entries) need ~30 more trading days (into September) for
   even a rough 20-trade sample - both need their own, later review
   point instead of being bundled into the 14-Aug decision.

✅ Diagnosed a burst of "Commit updated multi-strategy portfolios"
   workflow failures the user saw as repeated emails (screenshot) -
   traced to git push contention between the ~14 concurrent per-
   strategy triggers, worsened by the assistant's own rapid manual
   pushes while fixing credit_spread/vix_filter that same window (see
   07aug26_SESSION_LOG.md's 10-Aug entries). Confirmed self-healing
   (next check re-computes and pushes fine) via live GitHub Actions
   API checks - not a code bug, no data/trade loss.

--------------------------------------------------

Date

13-Aug-2026

--------------------------------------------------

13-Aug Achievements

Deep trade-by-trade analysis of all 10 threshold-group books (user
asked directly), plus the user's own 4-stage real-capital roadmap -
both written up in doc/PROJECT_STATUS.md.

✅ Broke every threshold strategy's Closed Trades down by Exit Reason
   (Target vs Stop Loss vs Square-Off) and computed the realized
   average payout per reason. Found a very clean, mathematically
   consistent picture: st3_threshold/NIFTY's Target and Stop-Loss
   averages are nearly symmetric (matching its 5%/5% config), and its
   actual win rate sits almost EXACTLY at 50% (13W/13L of 26 trades) -
   textbook proof of a signal with ~zero real edge (breakeven needs
   >50% on a symmetric payout). Also found BANKNIFTY's win rate is
   consistently low (17.6%-33.3%) across ALL THREE RSI strategies
   (simple_st1/st2/st3_threshold), while NIFTY's is consistently
   higher (45%-70%) - a structural, index-specific pattern, not one
   strategy's bad luck. Confirmed simple_st1_threshold/NIFTY (+28.5%,
   10 trades) and st2_threshold/NIFTY (+28.1%, 31 trades, win rate now
   a more credible 45.2%) are holding up as sample grows - genuinely
   past the "small-sample fluke" stage now, unlike st3_threshold/NIFTY
   which visibly faded from 100%-win/+15% (2 trades) to 50%-win/+1%
   (26 trades) as more data came in - a real, live demonstration of
   why small samples mislead.

✅ Confirmed conceptually (no code change) that the VPS+Firebase
   architecture's event-driven (real-tick) checking removes the
   overshoot problem essentially entirely, since it eliminates the
   1-5 min polling gap that causes it - user asked to verify this
   understanding directly.

✅ Documented the user's own 4-stage real-capital roadmap as the
   project's official plan (PROJECT_STATUS.md's new "REAL-CAPITAL
   ROADMAP" entry): (1) current 25-book paper trading to find real
   edge - review points 14-Aug and later for slower strategies, (2)
   VPS+Firebase build + 1 more month of paper trading, but ONLY on
   strategies that already proved edge in stage 1 (not all 25 books),
   (3) build real Order Execution/OMS (doesn't exist yet at all) +
   Rs 10,000 live test for ~1 month, (4) Rs 1,00,000 live trading.
   Each stage is explicitly CONDITIONAL on the previous one succeeding
   - no fixed calendar dates, matching this whole project's established
   discipline of only proceeding once real data justifies it.

✅ Formal statistical pass across all 25 books (Expectancy, Wilson 95%
   Confidence Interval on win rate, Sharpe Ratio, Max Drawdown, and
   cross-strategy Correlation) - user asked directly, one-off analysis
   script over existing Closed Trades data, no code/live-strategy
   changes. Full writeup in PROJECT_STATUS.md's new "STATISTICAL
   ANALYSIS ACROSS ALL 25 BOOKS" entry. Headline findings: only 4 of
   25 books have positive expectancy (simple_st1_threshold/NIFTY,
   oi_footprint/NIFTY, oi_footprint/BANKNIFTY, st2_threshold/NIFTY);
   oi_footprint/NIFTY has the best Sharpe (2.69) of anything in the
   system; and a NEW, actionable finding - simple_st1_threshold, st2_
   threshold, and st3_threshold on BANKNIFTY are 0.99-1.00 correlated
   with each other (moving as one, not 3 independent bets), directly
   evidencing the deferred Portfolio-level Aggregation concern with
   real numbers for the first time.

✅ Second statistical pass: one-sample t-test, Monte Carlo (5,000
   reshuffles of each book's own real trades), and lag-1
   autocorrelation - full writeup in PROJECT_STATUS.md's "SECOND
   STATISTICAL PASS" entry. Headline finding: Monte Carlo "ruin risk" -
   st2/NIFTY has a 39.5% chance and simple_st1/NIFTY a 24.3% chance of
   hitting zero/negative capital across 5,000 random reshuffles of
   their own real trades under current ~100%-cash sizing, while
   oi_footprint and the promising threshold-NIFTY books show 0.0% ruin
   risk in any reshuffling - confirms the near-empty Cash balances
   already seen live are a structural property of those books' signal,
   not an unlucky historical ordering. t-test also formally confirmed
   3 books as statistically negative (st2/NIFTY p=0.008, simple_st1_
   threshold/BANKNIFTY p=0.044, st4/NIFTY p=0.002).

✅ Walk-forward / split-sample test (first-half vs second-half of each
   book's trades) - full writeup in PROJECT_STATUS.md's "WALK-FORWARD /
   SPLIT-SAMPLE TEST" entry. CONFIRMED st3_threshold/NIFTY's earlier
   informal "faded" observation formally (+Rs 154/trade first half ->
   -Rs 2,025/trade second half - a real sign flip) - DECIDED to drop it
   from further consideration rather than keep watching. Also flagged
   a cautionary note on oi_footprint/NIFTY (the system's best performer
   overall) - still positive both halves but weakened a lot (+Rs 3,803
   at 69.2% win -> +Rs 396 at exactly 50.0% win) - worth watching
   closely, not treating as settled. simple_st1_threshold/NIFTY and
   st2_threshold/NIFTY held up best - second half as strong or stronger
   than the first.

✅ Third statistical pass: VaR/CVaR, Calmar Ratio, Risk-Parity
   (inverse-volatility) weights, and a holding-duration proxy for
   options Greeks - full writeup in PROJECT_STATUS.md's "THIRD
   STATISTICAL PASS - INSTITUTIONAL-STYLE METRICS" entry. Confirmed
   true Delta/Theta/Vega decomposition isn't possible from current
   trade data (no Exit Spot or implied volatility stored) - flagged as
   a future data-collection improvement rather than faked. Calmar
   Ratio and VaR95 both reconfirm oi_footprint as the standout (Calmar
   4.46-5.23, positive VaR95 even on bad days). Risk-Parity weights
   illustrate (not implemented) what capital allocation would look
   like if sized by risk instead of flat Rs 1L each - oi_footprint/
   BANKNIFTY would get ~15.6% of pooled capital, st3_threshold/NIFTY
   (already dropped) would get the least at 2.3%.

✅ Exit Spot now saved on every closed trade across all 7 strategy
   engines, and a real implied-volatility solver + Delta/Theta/Vega
   Greeks calculator built (indicators/black_scholes.py) - full
   writeup in PROJECT_STATUS.md's "EXIT SPOT + IV/GREEKS
   INFRASTRUCTURE" entry. Confirmed Fyers' API doesn't return IV
   directly (their own community forum has open requests for it), so
   IV is backed out from real premiums via bisection on the existing
   Black-Scholes pricer. 9 new tests, 278 passing overall. NOT yet
   wired into live trade analysis - needs each trade's time-to-expiry,
   which requires parsing Fyers' two different expiry symbol formats
   (weekly numeric vs monthly 3-letter-month) - flagged as the next
   step once Exit Spot data has accumulated for a while.

✅ Built that expiry parser same day - strategy/fyers_data.py's parse_
   option_expiry() + time_to_expiry_years(), full writeup in PROJECT_
   STATUS.md's "EXPIRY PARSER BUILT SAME DAY" entry. Handles both real
   formats (weekly NIFTY - exact date encoded; monthly BANKNIFTY -
   computes last Tuesday of the month, verified against NSE's Sep-2025
   Thursday->Tuesday expiry-day change), tested against real observed
   trade symbols. 8 new tests, 286 passing overall. All 3 pieces (Exit
   Spot, IV solver/Greeks, expiry parser) now exist - just need enough
   NEW trades (with Exit Spot, which only started today) to accumulate
   before a real Theta/Delta analysis is worth running.

✅ Built Dynamic Max Pain Drift (strategy/fyers_options_max_pain_
   drift.py) - the 4th and last 09-Aug novel-indicator idea, built,
   not deployed. Full writeup in PROJECT_STATUS.md's "DYNAMIC MAX PAIN
   DRIFT BUILT + NOT DEPLOYED" entry. Tracks Max Pain strike drift
   (same "watch the change" philosophy as oi_footprint/pcr_momentum),
   plus the user's own refinement - gated to only trade within 2 days
   of the option's own expiry (using the expiry parser built earlier
   the same day - one piece of infrastructure immediately enabling a
   second feature). 13 new tests, 299 passing overall. Same "built,
   not deployed" holding pattern as pcr_momentum - not added to
   ALL_STRATEGIES, no cron-job.org trigger.

✅ Both pcr_momentum and max_pain_drift then DEPLOYED same day, on the
   user's direct request - full writeup in PROJECT_STATUS.md's "PCR_
   MOMENTUM + MAX_PAIN_DRIFT DEPLOYED" entry. Paper trading (zero
   real-money risk), each its own separate book, so no reason to wait
   for 14-Aug. Books: 25 -> 29. No threshold variant for either
   (confirmed with the user - same reasoning as oi_footprint/vix_
   filter/credit_spread). Wired into mobile app, .gitignore, and the
   GitHub Actions workflow. 301 tests passing. User then created both
   cron-job.org triggers manually and confirmed test runs - checked
   live via GitHub Actions API, both firing correctly with no errors
   (STRATEGY_NAME reaching the script correctly, real evaluation
   happening, just correctly SKIPPED since checked after square-off).

✅ Then built AND deployed pcr_vix_combo same day too - the 4th and
   last 09-Aug novel-indicator idea (VIX+OI combo), on the user's own
   "no benefit to waiting" reasoning extended to this one as well.
   Full writeup in PROJECT_STATUS.md's "PCR_VIX_COMBO BUILT + DEPLOYED
   SAME DAY" entry. Reuses pcr_momentum's logic + adds a VIX calm-band
   gate (same validated condition as vix_filter.py, applied to an
   OI-based signal). Books: 29 -> 31. 305 tests passing overall. Still
   needs its own cron-job.org trigger (STRATEGY_NAME=pcr_vix_combo).

   With this, ALL 4 of 09-Aug's novel-indicator ideas are now live:
   oi_footprint (proven), pcr_momentum, max_pain_drift, pcr_vix_combo
   (the latter 3 all deployed 13-Aug, real data still to come).

✅ On-device verification of the whole rollout via adb (screenshot the
   real phone) - confirmed all 3 new strategy tabs render correctly in
   the app with correct descriptions, and caught + fixed a real stale-
   text bug along the way (Options tab banner still said "7 strategies"
   - now says 11). Rebuilt and reinstalled the APK, reverified on
   device. Committed and pushed.

✅ Fourth statistical pass: market-direction bias (correlation to the
   underlying's own daily return), Sortino Ratio, Ulcer Index, Profit
   Factor, and properly annualized Sharpe - full writeup in PROJECT_
   STATUS.md's "FOURTH STATISTICAL PASS" entry. Headline finding: oi_
   footprint/BANKNIFTY (previously the 2nd-best book) is 0.82
   correlated with BANKNIFTY's own daily direction - a real caution
   that part of its result may be riding a favorable trend rather than
   pure signal skill, unlike oi_footprint/NIFTY (-0.16) and simple_
   st1_threshold/NIFTY (0.02) which look genuinely direction-
   independent. Also wrote up a "HOW ALL THESE STATISTICAL TOOLS GET
   USED GOING FORWARD" entry mapping each of the ~15 formulas computed
   across 4 passes to a concrete, recurring project decision point
   (screening, confidence-gating, position-sizing, robustness
   monitoring, portfolio-level risk, market-bias checking) - not a
   one-time exercise, meant to be re-run at every future review point.

✅ Discussed a real-time per-trade Theta filter idea (skip entries
   where Theta decay is too severe relative to remaining time), and
   the user asked NOT to apply it directly to the currently-working
   oi_footprint - backtest first. Good call: a genuine retrospective
   test was possible (oi_footprint's own closed trades already store
   everything implied_volatility()/black_scholes_greeks() need) and
   it showed the filter would have REMOVED oi_footprint/NIFTY's BEST
   trades (the 12 near-expiry ones contributed 65% of all profit at a
   66.7% win rate, better than the rest) - rejected, documented as a
   real negative finding in PROJECT_STATUS.md's "THETA-FILTER IDEA
   RETROSPECTIVELY TESTED - REJECTED" entry. Not applied to any code.

✅ Same backtest-first method applied to a different idea: IV vs
   Realized Volatility (is the option "expensive" relative to the
   underlying's real recent movement). Genuinely promising for oi_
   footprint specifically (IV/RV > 1.5 filter would have removed only
   Rs 730 of oi_footprint/NIFTY's Rs 54,982 total profit while cutting
   its weakest trades - close to a free lunch), but does NOT
   generalize - tested across all 6 threshold-group books and found
   it runs BACKWARDS on the 3 currently-good NIFTY-threshold books
   (removes their BEST trades, 66.7-100% win rate, instead of the
   worst). Full writeup in PROJECT_STATUS.md's "IV vs REALIZED
   VOLATILITY RETROSPECTIVELY TESTED" entry. Kept as a documented
   candidate for oi_footprint only, not implemented live yet (small
   sample caution, same as everything else).

✅ Tried a 3rd idea specifically for the RSI-threshold family: CPR
   (Central Pivot Range, indicators/cpr.py - an already-built but
   previously unused indicator) support/resistance distance. Result:
   genuinely mixed/inconsistent - helps st2_threshold/NIFTY, but runs
   backwards on simple_st1_threshold/NIFTY AND oi_footprint/NIFTY
   (removes their best trades). REJECTED - no reliable, book-
   independent signal. Full writeup in PROJECT_STATUS.md's "CPR
   (SUPPORT/RESISTANCE DISTANCE) RETROSPECTIVELY TESTED - REJECTED"
   entry. Not implemented anywhere.

✅ Backtested loss-lock (mirror of the live profit-lock - stop after N
   consecutive losses) before deciding, same discipline as the 3
   rejected filters. Found a clean, consistent pattern this time
   (unlike Theta/IV-RV/CPR): helps already-weak books substantially
   (2 of 4 even flip net-positive) but hurts already-strong ones (cuts
   off legitimate same-day recovery). IMPLEMENTED SELECTIVELY -
   strategy/fyers_options_engine.py gained daily_loss_lock (mirroring
   daily_profit_lock) + MAX_CONSECUTIVE_LOSSES=2, applied only to
   simple_st1_threshold/BANKNIFTY, st2_threshold/BANKNIFTY, st3_
   threshold/BANKNIFTY, st3_threshold/NIFTY - NOT the 2 currently-
   strong NIFTY-threshold books. Full writeup in PROJECT_STATUS.md's
   "LOSS-LOCK BACKTESTED AND DEPLOYED SELECTIVELY" entry. 7 new tests.

✅ Also built + deployed oi_iv_combo (33rd book) - oi_footprint's
   OI-buildup signal unchanged, plus the promising half of the IV/RV
   finding (skip if the option's IV > 1.5x the underlying's own
   realized volatility) as its own separate book, since that same
   filter hurts the RSI family - kept away from oi_footprint itself.
   Deployed same day (paper trading, zero risk). Wired into ALL_
   STRATEGIES, mobile app, .gitignore, GitHub Actions workflow. 3 new
   tests, 316 passing overall.

✅ Created the oi_iv_combo cron-job.org trigger (user's manual step)
   and verified it live via the GitHub Actions API: STRATEGY_NAME:
   oi_iv_combo fired correctly for both NIFTY and BANKNIFTY, no
   errors, first-ever portfolio files committed clean. All 4 new
   strategies added today (pcr_momentum, max_pain_drift,
   pcr_vix_combo, oi_iv_combo) now confirmed live end-to-end.

✅ Rebuilt the Android APK (the previously-installed build predated
   the loss-lock + oi_iv_combo commit, so oi_iv_combo's source-code
   wiring into both app screens wasn't in the phone's actual install
   yet) and reinstalled via adb. Verified on-device: Summary tab now
   shows "Total Profit/Loss (33 books)" with oi_iv_combo NIFTY +
   BANKNIFTY rows both present at the bottom of the table. Precise
   tab-bar taps needed `adb shell uiautomator dump` to read the real
   accessibility-tree bounds after a couple of pixel-estimate mis-taps
   (one landed on an unrelated video app's floating PIP overlay, which
   was blocking the bottom nav bar until the user closed it; another
   landed on the LT stock card instead of the tab bar) - eyeballing
   coordinates from a screenshot description is not reliable enough
   for this app's bottom nav, uiautomator's bounds are exact.

✅ Replayed all 4 currently-profitable books' real closed-trade history
   at Rs 10,000 starting capital (same lot-sizing formula + real
   transaction-cost model as the live engines). Two findings: (1)
   every BANKNIFTY book skipped 100% of trades - Rs 10,000 can't
   afford even 1 lot given BANKNIFTY's lot size/premium, structurally
   unusable at that capital regardless of edge; (2) NIFTY results
   don't scale linearly - fixed per-order brokerage bites harder on
   smaller trades, and st2_threshold/NIFTY actually flips from
   +Rs 28,115 profit (Rs 1L capital) to -Rs 861 loss (Rs 10k capital).
   Then found each book's own minimum capital with zero skipped
   trades: oi_footprint/NIFTY and simple_st1_threshold/NIFTY need only
   Rs 11,000, st2_threshold/NIFTY Rs 11,500, oi_footprint/BANKNIFTY
   Rs 23,000 - all 4 stay profitable at their own minimum. Full
   writeup in PROJECT_STATUS.md's "MINIMUM CAPITAL RETROSPECTIVE
   REPLAY" entry.

✅ User confirmed an explicit 2-month timeline on top of the existing
   performance-gated Stage 2/3 plan: Month 1 = current local paper
   trading, Month 2 = repeat paper trading on the VPS+Firebase Stage 2
   build, only then Stage 3 (real capital) - both the time floor and
   the performance gate (~80-100 trade sample) need to hold, not just
   one. If the top 2-3 books hold up, Stage 3 would start ONLY those
   books, sized per the minimum-capital finding above (~Rs 25,000-
   35,000 combined for 2-3 books), not the full 33-book portfolio.
   Full writeup in PROJECT_STATUS.md's "STAGED CAPITAL PLAN - TIMELINE
   CONFIRMED" entry.

✅ FIXED, 14-Aug: the morning's oi_iv_combo APK rebuild dropped
   `--dart-define=GITHUB_PAT` (a plain `flutter build apk --release`
   doesn't pass it), breaking the Login-to-Fyers button - the exact
   same bug class first hit 07-Aug. Rebuilt with the flag (read from
   local `.env`, never printed), reinstalled, and verified live: the
   user logged in again and the fyers_trigger.yml run at 08:53 IST
   completed successfully on GitHub Actions. Documented as a standing
   reminder in PROJECT_STATUS.md - every future release build needs
   this flag or the login silently breaks again.

✅ Deep-dived oi_footprint's exit mechanism after a real bad trading
   day (14-Aug: -Rs 13,503 on 4 trades) - found the actual problem
   wasn't the OI-buildup signal being "wrong," it's that the +-Rs 1,500
   Target/Stop-Loss gets overshot 2x-10x by real trades (periodic ~1-
   min checking, not continuous). Backtested capping ONLY the Stop-
   Loss side at -Rs 2,000 (leaving Target/profit uncapped, exactly as
   today) against all 40 real closed trades: NIFTY +Rs 75,032 vs actual
   +Rs 41,479 (81% better), BANKNIFTY +Rs 12,267 vs actual +Rs 11,891 -
   the strongest, cleanest finding of the session. An ATR-scaled
   version of the same cap performed statistically identical to the
   flat version (not enough ATR variation in the 5-day sample to tell
   them apart yet). Recommended next step: a real broker-side Fyers
   SL-M/GTT order for the Stop-Loss side only, NOT a symmetric target
   order (that would remove the profit-side overshoot, which the data
   shows has been net-beneficial). Also confirmed Fyers' History API
   works for option symbols (same fyers_download(), hit only an auth
   wall locally, not a rejection) - a much better future data source
   than the ~5-min premium-history snapshot log used today. Tried
   Trailing-Stop/Breakeven/Laddered/Indicator-based exits too - only
   12 of 40 trades had any real intra-trade price data at all (mixed,
   inconclusive signal), the other two ideas couldn't be tested at all
   with current data. Full writeup in PROJECT_STATUS.md's "oi_footprint
   EXIT-MECHANISM DEEP DIVE" entry.

✅ Built (not wired in) the broker-side Stop-Loss order code from the
   exit-mechanism finding above - new strategy/fyers_order_execution.py:
   compute_stop_loss_trigger_price() (pure, bisection-solved, 5 new
   tests, 321 passing overall) finds the exit premium for a ~-Rs 2,000
   net loss using the real cost model; place_stop_loss_order() places
   a real Fyers SL-M order but is untested against the live API and
   not imported/called anywhere. User's explicit request: build and
   hold, wire in later. Full writeup in PROJECT_STATUS.md's "BROKER-
   SIDE STOP-LOSS ORDER - BUILT, NOT WIRED IN" entry.

✅ Built (not wired in) the circuit-band proximity filter (candidate #3
   from the circuit-breaker ideas list) - new indicators/circuit_
   band.py, 8 new tests, 329 passing overall. Retrospectively checked
   against all 40 real oi_footprint trades: fired 0 times, closest any
   real trade came to a 10% circuit band was 9.12% away - expected
   result (circuit halts are rare tail events), confirms the filter
   wouldn't cause a false-positive early exit on a normal day. Full
   writeup in PROJECT_STATUS.md's "CIRCUIT-BAND PROXIMITY FILTER"
   entry.

✅ Built (not wired in) the high-risk event-day calendar (candidate #4
   from the circuit-breaker ideas list) - new indicators/high_risk_
   event_calendar.py, 8 new tests, 337 passing overall. is_budget_day()
   is programmatic (01-Feb every year); HIGH_RISK_EVENT_DATES (RBI MPC/
   election/macro dates) shipped empty on purpose - needs real dates
   added by hand from official calendars before it's useful beyond
   Budget day. Full writeup in PROJECT_STATUS.md's "HIGH-RISK EVENT-DAY
   CALENDAR" entry.

✅ Retrospectively tested fractional position sizing (candidate #5,
   completing today's circuit-breaker ideas list) - corrected an
   earlier assumption first: oi_footprint deploys FULL Cash per trade,
   not a %-cap (that only exists for the equity Swing engine). Replayed
   all real trades at 100/50/30/20/10% of Cash per trade: profit and
   worst-case loss shrink together, roughly proportionally (NIFTY
   +Rs 41,479/-Rs 14,851 worst trade at 100% down to +Rs 2,657/-Rs 826
   at 10%) - not a free-lunch risk reduction, just a direct ceiling on
   how much can be trapped in one circuit-halted position. Not
   implemented (analysis only). Full writeup in PROJECT_STATUS.md's
   "FRACTIONAL POSITION SIZING" entry. This completes all 5 circuit-
   breaker protection candidates for today.

✅ Researched circuit-breaker protection for an open position (not a
   strategy edge question - a risk-infrastructure one). 5 candidate
   mitigations identified and prioritized, NONE built or backtested
   yet - explicitly deferred, user wants to backtest next session.
   Top priority: broker-side GTT/SL-M orders (not just software
   polling) so a position is protected even if the VPS script itself
   has a hiccup or a halt lands between checks. Full list in
   PROJECT_STATUS.md's "CIRCUIT-BREAKER PROTECTION IDEAS" entry.

==================================================

Next Session Priorities

Unchanged from doc/07aug26_SESSION_LOG.md's last "Next Session
Priorities" list - nothing here supersedes it, just adds today's
findings as extra context for the 14-Aug review itself:

0. DONE, 14-Aug (same session, later): all 5 circuit-breaker ideas
   backtested/built - see PROJECT_STATUS.md's "EXIT-MECHANISM /
   CIRCUIT-BREAKER IDEAS - FINAL PRIORITY RANKING" entry for the full
   8-idea ranking (includes Trailing/Breakeven/Laddered/Indicator exits
   too). Top priority confirmed: the broker-side Stop-Loss cap
   (strategy/fyers_order_execution.py, 81% NIFTY improvement on the
   full 40-trade sample) - built, not wired in. Next concrete step:
   test place_stop_loss_order() for real (small position) once Stage 2
   VPS is live - it has never been called against Fyers' real API.

0b. MAJOR CORRECTION, 14-Aug (same session, right after the 14-Aug
    review's initial verdict below): applying the same -Rs 2,000 SL cap
    to the books just verdicted "no edge, stop pursuing" flips 5 of
    them from real losses to real profits (simple_st1/NIFTY -Rs 91,799
    -> +Rs 50,957; st3/NIFTY -Rs 78,163 -> +Rs 1,19,227; st2/BANKNIFTY
    -Rs 50,157 -> +Rs 13,709; st3/BANKNIFTY -Rs 46,101 -> +Rs 19,897;
    st3_threshold/NIFTY -Rs 21,097 -> +Rs 53,171), and shrinks the other
    3 by 50-68%. The "RSI signal has no edge" verdict was likely
    measuring the same exit-overshoot problem as oi_footprint, just
    much worse here (87-128 trades vs 31). Do NOT retire these on the
    original numbers - re-evaluate once the broker-side SL order is
    live-tested. Also swept the cap level itself and found a suspicious
    monotonic "tighter is always better" pattern down to Rs 50 -
    flagged as unrealistic below ~Rs 1,000-1,500 (real slippage, and
    the backtest doesn't model the higher trade frequency a genuinely
    tighter SL would cause). Full writeup in PROJECT_STATUS.md's
    "MAJOR CORRECTION" entry.

0c. FLAT-Rs vs %-OF-DEPLOYED-CAPITAL SL CAP, 14-Aug: tested whether the
    SL cap should be a flat rupee amount or scale with each trade's
    actual position size. Full sequential replay (cash carried trade-
    to-trade, 12 capital tiers Rs 15,000-10,00,000, 8 books) - flat-Rs
    wins the aggregate at every tier, and by a growing margin (~2x at
    Rs 1,00,000+), because %-of-deployed lets the loss cap grow right
    alongside a winning account (risk compounds upward when succeeding
    - the opposite of disciplined). BUT the aggregate hides a real
    reversal at small capital: at Rs 15,000-50,000 - the ACTUAL Stage 3
    range already planned - %-of-deployed wins or ties for most of the
    8 books. Recommendation: use %-of-deployed for the real Stage 3
    sizing, revisit flat-Rs only if capital per book scales toward
    Rs 1,00,000+ later. st2_threshold/BANKNIFTY stays negative under
    BOTH methods at every capital tier - confirmed its problem isn't
    exit-overshoot, keep it excluded from real-capital plans regardless.
    Full writeup in PROJECT_STATUS.md's "FLAT-RUPEE vs %-OF-DEPLOYED-
    CAPITAL" entry.

0d. HYBRID SL CAP - min(flat, pct) BEATS BOTH, 14-Aug: tested combining
    the two instead of picking one - at each Stop-Loss, use whichever
    of (flat_cap, pct_of_deployed_cap) is SMALLER. Wins or ties at
    EVERY capital tier tested (Rs 15,000 to Rs 10,00,000, 8 books) -
    structurally can't be worse than the better of the two pure
    versions. REVISED FINAL RECOMMENDATION: use this hybrid, not either
    pure form. Also worked out exactly how this maps onto the already-
    built broker-order code (strategy/fyers_order_execution.py) - the
    hybrid math runs once in our own code at position-open time; the
    broker only ever receives one final trigger price via the existing
    compute_stop_loss_trigger_price(..., max_loss_rupees=hybrid_value)
    -> place_stop_loss_order() pipeline, no new function needed. Full
    writeup in PROJECT_STATUS.md's "HYBRID SL CAP" entry.

0e. _slcap BOOKS BUILT + DEPLOYED, 14-Aug: implemented the hybrid SL
    cap as 8 new PAPER-TRADING books, alongside (not replacing) the
    originals - strategy/fyers_options_engine.py gained an optional
    hybrid_sl_cap_pct parameter + pure _hybrid_stop_loss_cap() helper
    (5 new tests), and strategy/options_strategies.py gained
    simple_st1_slcap/st2_slcap/st3_slcap (both indices) + st3_
    threshold_slcap (NIFTY) + st2_threshold_slcap (BANKNIFTY) - 8
    books, ALL_STRATEGIES 33 -> 41. Wired into all 3 mobile-app option
    screens, .gitignore, and the GitHub Actions workflow, same pattern
    as every other same-day strategy deployment. 344 tests passing.
    Both the original and _slcap book-sets now run in parallel, so the
    hybrid-cap hypothesis gets a real, not just retrospective, test
    going forward. Full writeup in PROJECT_STATUS.md's "_slcap BOOKS
    BUILT + DEPLOYED" entry.

0f. oi_footprint EXIT-MECHANISM VARIANTS BUILT, 14-Aug: the 5 profit-
    booking filters that couldn't be retrospectively backtested
    (Trailing-Stop/ATR/Breakeven/Laddered/Indicator-based - no fine-
    enough historical data for oi_footprint's 0.6-8.9-min trades) got
    built as 6 LIVE paper-trading variants instead (oi_hybrid_sl +
    5 more, each adding exactly one idea on top of the hybrid SL cap -
    see fyers_options_oi_footprint_variants.py). oi_footprint itself
    untouched. 12 new books (6 x 2 indices), ALL_STRATEGIES 41 -> 53,
    7 new tests, 353 passing overall. BACKEND ONLY THIS ROUND - user
    explicitly said not to wire these into the mobile app yet ("app
    madhe add karu nakos, ajun khup kam aahe" - more work still coming)
    - reverted the app-screen edits already made, kept everything else
    (strategy code, tests, .gitignore, GitHub Actions workflow). App
    wiring is a separate, later step once this round of work settles.
    Full writeup in PROJECT_STATUS.md's "oi_footprint EXIT-MECHANISM
    VARIANTS BUILT" entry.

0g. REMAINING THRESHOLD BOOKS GIVEN THE HYBRID SL CAP, 14-Aug: tested
    the hybrid cap on every threshold book not yet covered - st3_
    threshold/BANKNIFTY and simple_st1_threshold (both indices) flip
    from real losses to real profits; st2_threshold/NIFTY and simple_
    st1_threshold/NIFTY (already profitable) get meaningfully MORE
    profitable (2.6x and 1.3x respectively at Rs 1,00,000); st4_
    threshold improves but doesn't flip (small 3-trade samples).
    st2_threshold/BANKNIFTY re-confirmed negative under every cap at
    every capital tier - correctly left without a second attempt.
    Deployed 6 new threshold _slcap books at the user's explicit
    request to cover everything tested, including st4_threshold
    despite the weaker result (new hybrid_sl_cap_pct on fyers_options_
    st4.py's make_st4_config() - only touches the initial Stop-Loss
    phase, not the trailing-stop mechanism). Backend only again, same
    as the oi_footprint variants. ALL_STRATEGIES 53 -> 59, 355 tests
    passing. Full writeup in PROJECT_STATUS.md's "REMAINING THRESHOLD
    BOOKS GIVEN THE HYBRID SL CAP" entry.

0h. MOBILE APP - GROUPED OVERVIEW + PER-TRADE COST BREAKDOWN, 14-Aug:
    user's explicit app-update request, now that ALL_STRATEGIES has
    grown to 59 - (1) group every book into 4 buckets (New SL-cap /
    Profitable / Loss-making / No data yet) instead of one long tab
    row, computed LIVE from real Cash on every load, not hardcoded;
    (2) tapping any trade (live or history) shows full detail
    including REAL trading costs (brokerage/STT/exchange/stamp-duty/
    SEBI/GST) - explicitly NOT personal income tax, which the user
    clarified depends on total annual income and can't be computed
    in-app. New FyersOptionsGroupedScreen (10th bottom-nav tab) +
    FyersOptionsBookDetailScreen (per-book drill-down) + options_
    transaction_costs.dart (client-side mirror of the Python cost
    formula, works on historical trades too, no backend change
    needed) + showOptionTradeDetails() in widgets/common.dart.
    VERIFIED LIVE on the phone: Grouped screen showed correct real
    groupings and PnL; a real -Rs 4,321.06 Stop-Loss trade's detail
    sheet showed the full cost breakdown with Net PnL matching the
    backend's real recorded value EXACTLY. flutter analyze clean.

1. 14-Aug review checkpoint - now explicitly split: (a) simple_st1/
   st2/st3/st4 and their threshold variants have enough sample to
   decide on now (NIFTY and BANKNIFTY threshold legs separately -
   see finding above; simple_st1_threshold/NIFTY and st2_threshold/
   NIFTY look genuinely promising, st3_threshold/NIFTY's early promise
   already faded, all BANKNIFTY RSI legs confirmed weak), (b)
   oi_footprint close to enough sample, (c) vix_filter/credit_spread
   need their own later review point (~September), not a 14-Aug
   verdict. Plus the equity engines (Swing/Intraday) retune-vs-
   redirect decision, Portfolio-level Aggregation (now has concrete
   evidence - see the 0.99-1.00 BANKNIFTY correlation finding below),
   shared Backtest-Live engine, and the PCR Momentum + Volume-Weighted
   OI deploy decision - all still queued as before.

2. The user's 4-stage real-capital roadmap (see above) - Stage 2 (VPS+
   Firebase) build should realistically start once oi_footprint (the
   furthest-along strategy) reaches a trustworthy ~80-100 trade sample
   - roughly another week at its current ~9 trades/day pace, tracked
   live, not a fixed date.

3. Desktop App Android-parity expansion - still not started.

4. DONE, 13-Aug: Dynamic Max Pain Drift built (see above) - now joins
   pcr_momentum.py in the "built, awaiting a deployment decision"
   pile for the 14-Aug review.

5. DONE, 15-Aug (discussion only, no code): tick-by-tick data
   storage follow-up. User asked three concrete questions in
   sequence - (a) given the Stage 2 VPS's own spec (Rs 400-600/mo,
   40-60GB SSD), what tick-rate/scope can it sustain by itself
   (answer: disk is the bottleneck, not CPU/bandwidth - ~100
   ticks/sec on a narrow ~25-instrument scope fits within the VPS's
   own disk); (b) what changes if external cloud storage is added
   (answer: disk stops being the constraint, cost becomes the real
   lever - Rs 15-450/month depending on scope x tick-rate at
   Backblaze B2 rates, new ceiling becomes the VPS's 1-vCPU compute
   at ~300-500 ticks/sec); (c) cloud object storage vs cloud block
   storage vs a physical SSD (answer: physical SSD can't attach to a
   cloud VPS directly, only usable at home which reintroduces the
   always-on-machine problem the VPS was meant to solve - recommend
   cloud object storage/B2). Also worked out the "store forever"
   trap (cost climbs every month, ~Rs 35,100 for year 1 at the
   priciest scope) vs rolling/rotated retention (flat, ~200x cheaper
   at the cheap end) and 5 concrete compression techniques beyond
   plain gzip (binary format, delta encoding, zstd - all lossless;
   skip-unchanged-ticks and lower-frequency OI sampling - only safe
   if implemented carefully, genuinely lossy otherwise). Full
   writeup in PROJECT_STATUS.md's "TICK-BY-TICK DATA STORAGE" entry,
   filed as reference for whenever Stage 2 VPS or the narrow
   position-window tick-capture idea actually gets built - nothing
   actioned yet.

6. DONE, 15-Aug (discussion + one-off analysis, no code built):
   equity Swing/Intraday check (see below) led into a "is this whole
   effort going to be wasted if real trading doesn't work" moment -
   answered with the staged-capital safety net already in place, not
   false reassurance. Follow-up explained execution-delay (our own
   check-cadence - genuinely fixed by the planned Stage 2 VPS) vs
   slippage (bid-ask spread/depth - NOT a speed problem, VPS speed
   doesn't touch it) as two different problems. User asked for a
   rough theoretical stress-test since a real one isn't possible (no
   historical bid/ask depth was ever captured, only LTP - same data
   gap as the oi_footprint exit-mechanism variants earlier). Applied
   an assumed round-trip spread cost to all 40 real oi_footprint
   trades (original +Rs 53,370 Net PnL): at 0.5% spread ~46% of the
   profit gets eaten (+Rs 28,738 left), at 1% ~92% eaten (+Rs 4,105,
   barely profitable), at 2% it flips NEGATIVE (-Rs 45,160, 6 trades
   flip sign). Side finding: oi_footprint sizes every trade with
   nearly all available cash (lots ranged 4->118 across the 40
   trades as capital compounded), which directly amplifies slippage
   sensitivity as capital grows - flagged as a position-size-cap
   idea for the real-capital stage, not a paper-trading change now.
   Full writeup in PROJECT_STATUS.md's "SLIPPAGE & EXECUTION-DELAY
   DISCUSSION + THEORETICAL STRESS-TEST" entry. Also did a same-day
   equity health check (yfinance Intraday: +Rs 13, 52 closed; yfinance
   Swing: +Rs 1,944 realized/+Rs 263 unrealized on 15 open positions,
   54% win rate on 24 closed; Fyers Intraday: -Rs 11, 17 closed; Fyers
   Swing test: -Rs 571 on only 12 closed trades, 17% win rate) - all 4
   GitHub Actions workflows green as of 14-Aug. Fyers Swing's weak
   win rate traced to running the EXACT SAME process_signal/ATR-SL
   code as yfinance Swing (which shows 54% win rate on a longer, more
   varied 4-week sample) - concluded this is most likely a small,
   time-concentrated sample (12 trades, all in one week) rather than
   a flaw in the SL/Target methodology itself; deliberately NOT
   tuning any parameter off a 12-trade sample, consistent with this
   project's standing data-driven-patience approach.

==================================================

END OF SESSION
