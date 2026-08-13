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

==================================================

Next Session Priorities

Unchanged from doc/07aug26_SESSION_LOG.md's last "Next Session
Priorities" list - nothing here supersedes it, just adds today's
findings as extra context for the 14-Aug review itself:

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

==================================================

END OF SESSION
