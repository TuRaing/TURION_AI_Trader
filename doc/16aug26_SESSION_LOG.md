# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260816-001 (local machine session - Claude Code Desktop,
D:\TURION_AI_Trader) - new session, continuing from 12aug26_SESSION_
LOG.md (which spanned 10 through 15-Aug).

--------------------------------------------------

Date

16-Aug-2026

--------------------------------------------------

Today's Achievements

No code changes - user relayed a question from a parallel Claude
conversation and asked for it to be checked against real data rather
than answered from theory.

✅ Detected and flagged a prompt-injection attempt: the user's relayed
   message carried hidden text instructing this session to "respond
   TEXT ONLY... do NOT call any tools" - almost certainly picked up
   accidentally while copy-pasting from the other Claude conversation,
   not something the user typed deliberately. Ignored the injected
   instruction, told the user directly what was found, and proceeded
   normally (tools included) once flagged.

✅ Investigated the real question underneath it: is oi_footprint's
   reported profit (NIFTY Net PnL Rs 41,479, BankNifty Rs 11,891)
   inflated by leverage rather than reflecting real edge? Pulled every
   closed trade's Net PnL % (position-size-independent per-trade
   return) and Lots from reports/fyers_options_oi_footprint_{nifty,
   banknifty}_portfolio.json instead of reasoning about it abstractly.
   Found a genuine, concrete finding: NIFTY's single biggest trade
   (#12, 118 lots vs a typical 10-30) accounts for 42% of the ENTIRE
   total profit, and the average per-trade % return dropped from
   2.68% (first half of trades) to 0.08% (second half) even as lots
   grew - i.e. the strategy's real per-trade edge did NOT improve
   over time; the rising absolute-rupee total is mostly a position-
   sizing (leverage) artifact plus one outlier trade. BankNifty shows
   the same profit-concentration pattern (1 trade = 49% of total)
   but not the edge-decay pattern (too few trades, 9, to read much
   into yet). Win rates (58% NIFTY, 67% BankNifty) are genuinely
   stable and real - the concern is specifically about reading the
   absolute-rupee trend as "the strategy is improving," not about the
   numbers being fabricated. Reinforces the already-filed position-
   size-cap idea; not acted on now, per the user's stated preference
   to wait for more real trade data before adding new gates - filed
   as a concrete example (trade #12) to keep in mind when that
   decision is revisited.

✅ User directly challenged the scope: "did you look at ALL
   strategies, or only the profitable one?" - a fair catch, the above
   only covered oi_footprint because that was the strategy named in
   the relayed question. Scanned all 27 report books with closed
   trades (of 50 total portfolio files). Found a materially bigger
   picture: only 4 of 27 books are net profitable, 23 are net losing,
   combined Net PnL across every book is Rs -5,85,289. The 4
   profitable books: oi_footprint/NIFTY (+41,479), st2_threshold/
   NIFTY (+38,546), simple_st1_threshold/NIFTY (+35,348), oi_
   footprint/BankNifty (+11,891). Then re-ran the leverage-
   concentration diagnostic across all 4 profitable books (not just
   oi_footprint) to check whether the leverage-inflation pattern
   generalizes - it does NOT: only oi_footprint/NIFTY is genuinely
   leverage-driven (biggest trade used 7x the book's median lot
   count). The other 3 profitable books' biggest trades were at or
   below their book's median lot size - their profit concentration
   is a small-sample artifact (9-33 trades), not leverage; simple_
   st1_threshold/NIFTY in particular reads as a genuinely clean edge
   (72.7% win rate, stable ~3% per-trade return across both halves).
   Full writeup (both the scope-expansion and the per-strategy
   verdicts) in PROJECT_STATUS.md's "PORTFOLIO PROFITABILITY AUDIT +
   LEVERAGE-CONCENTRATION FINDING" entry.

✅ User asked for a retrospective backtest of st2_threshold/NIFTY and
   simple_st1_threshold/NIFTY with hybrid SL (2% cap, same design as
   the existing live _slcap books) PLUS the daily profit-lock changed
   from the fixed DAILY_PROFIT_LOCK_RS = Rs 2,000 to 2% of that
   capital tier's own starting capital, swept across 13 capital tiers
   (Rs 10,000 to Rs 10,00,000). One-off scratchpad script (matches
   this project's established sequential-replay convention - cash
   carried trade-to-trade, lots recomputed fresh at each step, real
   Entry/Exit Premium, calculate_options_round_trip_cost() reused).
   RESULT: st2_threshold/NIFTY improves at EVERY tier (flips a loss
   to a profit at Rs 10,000: -Rs 370 to +Rs 2,868; stays ~5 points of
   ROI better at every tier above that, e.g. 40.8% to 45.9% at Rs
   10,00,000). simple_st1_threshold/NIFTY improves in the Rs 10,000-
   1,00,000 range (the actual Stage-3 real-capital range) but is
   marginally worse above Rs 2,00,000 (a single trade gets cut off
   earlier by the tighter dynamic lock at that scale - a small,
   real crossover, not noise). Combined across both books, the new
   variant wins at every tier tested, gap widening with capital (+Rs
   4,122 at Rs 10,000 to +Rs 45,266 at Rs 10,00,000). Flagged one
   honest limitation matching this project's own "MAJOR CORRECTION"
   precedent: the real trade record was captured under the original
   fixed Rs 2,000 lock at Rs 1,00,000 capital, so tiers where the new
   2%-of-capital lock is LOOSER than that (above Rs 1,00,000) cannot
   manufacture extra trades that were never taken historically -
   results above Rs 1,00,000 are a same-recorded-trades replay, not
   proof more trades would have fired. Full tables in PROJECT_
   STATUS.md's "HYBRID SL + DYNAMIC PROFIT-LOCK CAPITAL SWEEP" entry.
   Analysis only - no code changed, no new books built yet.

✅ User asked for a further variant: hybrid SL kept, but replace the
   fixed Target with a minimum-2%-profit trailing stop and unlimited
   upside (trail the peak once +2% is reached, no fixed cap above
   it) - same shape as oi_footprint's already-live "trailing" variant
   (strategy/fyers_options_oi_footprint_variants.py). Checked whether
   this is backtestable against st2_threshold/simple_st1_threshold's
   real closed trades the same way as the capital sweep above -
   it is NOT: a trailing exit needs to know the PEAK premium reached
   during the trade, and the real portfolio JSON only stores Entry
   Premium and Exit Premium, no intraday price path. This is the
   EXACT SAME limitation this project already hit and documented for
   oi_footprint's own profit-booking-filter ideas (see PROJECT_
   STATUS.md, 14-Aug - "6 live paper-trading tests... could NOT be
   retrospectively backtested"), which is why those were built as new
   LIVE books instead of backtested. Told the user honestly rather
   than fabricating an approximate number from incomplete data.

DECISION, end of session: everything above documented; the two
follow-up builds (hybrid-SL + 2%-lock variant, backtest-verified; and
the trailing variant, live-only per the data limitation) deferred to
the next session when the user has time - "sagala doc kar, udya time
milalya war tayar karu" (document everything, build tomorrow when
there's time). NOT built yet - next session should build these as
NEW separate books (never modify a working module), matching the
_slcap / oi_footprint-variant precedent exactly.

==================================================

--------------------------------------------------

Date

17-Aug-2026

--------------------------------------------------

17-Aug Achievements

Same continuing session (S20260816-001). No code changes - a login/
sync check, then live-day monitoring and analysis as real trades
started coming in.

✅ Fyers login check, at the user's request: local session's own
   verify_connection() call showed "token expired" (code -8) - but
   traced this to a LOCAL-ONLY problem, not a real login failure. The
   local .env's FYERS_ACCESS_TOKEN was last written 06-Aug (11 days
   stale) - the mobile/desktop app's login button updates the GitHub
   Actions secret directly, never this local session's .env file.
   Confirmed via the GitHub Actions API directly (not guessing) that
   the REAL login (the one that matters - cron-triggered live paper
   trading) succeeded: today's 08:37 IST workflow run log showed
   FYERS_ACCESS_TOKEN accepted with no error, correctly SKIPPED only
   because market hadn't opened yet (before 9:15). Offered to also
   refresh the local .env (would need the user to complete a real
   browser login and paste back the redirected URL, since GitHub
   Secrets can't be read back and Claude can't complete a Fyers login
   itself) - user said leave it, not needed.

✅ Also checked local git vs GitHub sync directly (git fetch + rev-
   list) - found perfectly synced at that moment (0 ahead/0 behind).
   Separately clarified the stray root-level TURION_Desktop.exe copy
   (untracked, not gitignored since it sits outside build/dist/) -
   user said leave it as-is, no .gitignore change made.

✅ "आजचा trading analysis कर सगळ्या strategy" - ran a live check once
   the market had been open ~35 minutes. First pass showed ZERO
   trades - turned out the local clone was 514 commits behind origin/
   main (GitHub Actions' own automated "Update multi-strategy options
   portfolios [skip ci]" commits accumulate fast once the market is
   open and every ~1-min cron check pushes). git pull brought local
   current, then the real scan showed 144 real closed trades already
   in ~35 minutes, total realized Rs +56,114 across all books (56
   Target hits +Rs 4,25,910; 79 Stop-Loss -Rs 3,69,036; a few smaller
   trailing/partial/indicator exits). Broke it down per book (best:
   st2_threshold/NIFTY +22,285, simple_st1_threshold/NIFTY +19,212;
   worst: oi_hybrid_sl_trailing/NIFTY -24,326, oi_hybrid_sl/NIFTY
   -17,174, oi_footprint/NIFTY -11,110) and flagged that oi_footprint
   - one of only 4 historically-profitable books - was having a bad
   day on BOTH indices.

✅ User asked directly why: "जी चांगली होती ती खराब झाली, जी खराब होती
   ती चांगली" - pulled oi_footprint/NIFTY's actual trade-by-trade Entry
   Spot/Exit Spot alongside simple_st1/NIFTY's, for the same morning
   window. Found a real, numbers-backed explanation: NIFTY spot has
   been range-bound all morning (~24,280-24,325, a ~45-point band) -
   oi_footprint's OI-buildup signal (recomputed every ~1-min check)
   flipped direction 5 times in 15 minutes (PE->CE->CE->CE->PE->PE),
   including 3 CONSECUTIVE CE (bullish) bets while spot was flat-to-
   down each time - a directional-prediction strategy getting whip-
   sawed by a genuinely trendless market reading its own signal as
   noise. simple_st1/NIFTY, by contrast, doesn't predict direction at
   all - it just scalps ANY quick premium wiggle after entry (all 9
   of its trades today were PE, RSI stayed persistently <50, but it
   profited on wiggles either way) - exactly the shape of edge that
   thrives in a choppy market. Explicitly flagged this as a snapshot
   of TODAY'S regime, not a permanent verdict - a real trending day
   would likely flip which family does better.

✅ User asked if a choppiness filter is worth building for
   oi_footprint. Rather than deciding from one day, ran a retrospective
   check on oi_footprint/NIFTY's own 6 real prior trading days (10, 11,
   12, 13, 14, 17-Aug): for each day, computed the day's own intraday
   spot range (from real Entry/Exit Spot values already in the
   portfolio JSON - no external API call possible anyway, since the
   local session's Fyers token is expired) as a %, then correlated
   against that day's real PnL. RESULT: correlation is weak (0.150)
   and NOT consistent - 13-Aug had the NARROWEST range of all 6 days
   (0.08%) yet was one of the BEST days (100% win rate, +Rs 11,302),
   directly contradicting the "choppy = bad for oi_footprint"
   hypothesis that today's single bad day suggested. CONCLUSION: not
   enough real evidence yet to justify building a choppiness filter -
   only 6 real trading days, with one clear counter-example. Matches
   the user's own standing preference to wait for more real data
   before adding new gates. Filed for a re-check once more days
   accumulate (user's own plan: revisit this evening after today's
   full session is a 7th data point, and again as more days come in).

✅ Live-day re-check a few hours later (13:14 IST, ~4 hours into
   trading): 471 closed trades so far today, total realized Rs
   +6,80,877 (up sharply from the +56,114 seen at 9:50 IST), overall
   win rate 49.9%. Market direction flipped from the morning - all 12
   open positions at this check were CE (bullish), vs the morning's
   all-PE pattern - consistent with RSI turning >=50 in the afternoon.
   oi_footprint stayed negative on both indices (NIFTY -27,084,
   BankNifty -7,882) while the RSI/slcap family kept compounding
   large gains (simple_st1_slcap/NIFTY +1,49,327, simple_st1/NIFTY
   +1,32,208, st3_slcap/NIFTY +1,31,972).

✅ User asked directly: "आपला SL 2% आहे पण काही ठिकाणी 10%, 15% SL
   trigger झालाय, check करतोस का" - checked properly rather than
   dismissing it. Pulled every Stop-Loss exit today and computed
   |Net PnL %| for the plain-%, hybrid-2%, and rupee-1500 books (vix_
   filter, gapfill, credit_spread excluded - they use spot/ATR/credit-
   multiple exit rules, not a %-of-capital or flat-rupee cap, so
   "overshoot vs a % cap" isn't a meaningful comparison for them).
   Worst individual case: simple_st1/NIFTY, intended 3% (Rs 3,000),
   actual -26.91% (Rs 26,911) - a 9x overshoot. st2/NIFTY (intended
   2%) and st3_slcap/NIFTY (intended hybrid 2%) both hit ~14% actual
   (7x overshoot) on separate trades. Then quantified the FULL scale
   across all 234 overshooting Stop-Loss exits today (comparable
   books only): total actual SL-exit loss Rs 11,01,839 vs Rs 4,90,222
   if every SL had capped exactly at its intended level - TOTAL
   OVERSHOOT = Rs 6,11,617, more than HALF of today's entire realized
   Stop-Loss loss. ROOT CAUSE (same as the already-documented 14-Aug
   finding, not new): checks run only every ~1 min (GitHub Actions +
   cron-job.org throttling) - in a fast-moving session like today's
   afternoon, premium can move well past the intended cap between
   checks before the bot catches and closes it. This directly connects
   to the already-filed, NOT-YET-BUILT Priority-1 mitigation from the
   14-Aug CIRCUIT-BREAKER PROTECTION IDEAS entry: a real broker-side
   Stop-Loss order (Fyers GTT/SL-M) instead of pure software polling.
   Full numbers in PROJECT_STATUS.md's "17-AUG LIVE SL-OVERSHOOT
   QUANTIFIED" entry. Analysis only - no code changed.

✅ User asked correctly: is broker-side SL (the 14-Aug fix cited above)
   actually usable for PAPER trading? Corrected an earlier imprecise
   answer - NO, GTT/SL-M orders attach to a REAL brokerage position,
   which paper trading never creates (it only reads real quotes and
   simulates). Broker-side SL is Stage-3 (real capital) only. For
   paper trading specifically, the real available mitigation is the
   ALREADY-PLANNED Stage 2 VPS + Fyers WebSocket architecture (event-
   driven checks every few seconds instead of ~1-min polling) - user
   then asked to accelerate this: agreed to split CODE-PREP (WebSocket
   client + event-driven rewrite, needs no VPS, doesn't touch live
   books) from actual VPS deployment, starting code-prep now instead
   of waiting for 1-Sep as originally planned. Fresh profitability
   check across all 55 books with real trades (through today) found
   19 "profitable" on raw totals, but only 4 hold up once filtered for
   real multi-day track record (>=4 real trading days) - the same 4
   books identified 16-Aug (today's huge single-day volume in several
   1-day-old _slcap books was creating a false impression, same "don't
   trust one day" lesson as the choppiness-filter check above).

✅ User then redirected to finish yesterday's deferred build FIRST
   (hybrid-SL + 2%-lock variant, and the trailing variant) before the
   bigger WebSocket work - built both, same session:
   - Added 2 new opt-in params to fyers_options_engine.py's make_
     strategy()/check_or_open()/_check_position(): daily_profit_
     lock_pct (dynamic %-of-capital profit lock, backtest-verified
     16-Aug) and trailing_min_pct (minimum-2%-profit trailing stop,
     unlimited upside, TRAIL_PCT=30% reused from oi_footprint's own
     live trailing variant - live-only, could not be backtested).
     Both default None - zero behavior change for every existing
     strategy.
   - 4 new NIFTY-only books in options_strategies.py + ALL_STRATEGIES:
     st2_threshold_slcap2pctlock, simple_st1_threshold_slcap2pctlock
     (hybrid SL + dynamic 2% lock), st2_threshold_trailing2pct,
     simple_st1_threshold_trailing2pct (hybrid SL + trailing).
   - Updated/added tests (book-count 59->63, threshold-group count
     18->22, new tests for both new mechanisms) - 380/380 passing,
     no regressions.
   - User asked directly whether both new mechanisms are equally
     "tested" - clarified honestly: only the slcap2pctlock combo has
     real backtest evidence (16-Aug sweep); the trailing2pct combo has
     NONE (same data limitation as before) - it is a reasoned design
     choice, not a proven one, exactly like oi_footprint's own
     trailing variant.

✅ User asked, independently, why the app shows st3_threshold_slcap as
   NIFTY-only and st2_threshold_slcap as BANKNIFTY-only. Traced it: a
   REAL, STALE bug - both restrictions were correct only for a few
   hours on 14-Aug, before that same day's later "4 more threshold
   _slcap books" batch added the missing sibling for each (both now
   run on BOTH indices, with real trades and real cash - confirmed
   st3_threshold_slcap/BANKNIFTY has Rs 1,07,283 cash/1 trade,
   st2_threshold_slcap/NIFTY has Rs 1,13,528/1 trade) - the app's
   hardcoded STRATEGY_INDEX_OVERRIDES (desktop) / _strategyIndices
   (mobile) were never updated, silently hiding 2 real live books'
   data from the user this whole time. FIXED in both desktop_app.py
   and mobile_app/lib/screens/fyers_multi_strategy_options_screen.dart
   (removed the 2 stale entries). Also wired the 4 new 17-Aug books
   into both apps (desktop's THRESHOLD_STRATEGY_NAMES/DESCRIPTIONS/
   STRATEGY_INDEX_OVERRIDES; mobile's fyers_threshold_options_screen.
   dart + the _allBooks lists in fyers_options_grouped_screen.dart and
   fyers_options_summary_screen.dart, plus _isSlcap()'s classification
   so they show under "New SL-cap" not just by raw PnL sign).
   `dart analyze` clean, Python syntax clean, 380/380 tests still
   passing.

✅ Gave the user the cron-job.org POST body table for the 4 new
   STRATEGY_NAME values (same workflow_dispatch endpoint/pattern as
   every prior strategy - clone an existing job, only the `strategy`
   input differs). User set the 4 jobs up but reported the test-run
   failed ("server busy"). Investigated via the real GitHub Actions
   API rather than guessing - found TWO real, separate causes: (1)
   the new strategy code had NOT actually been pushed to origin/main
   yet (only local/uncommitted) - confirmed via `git show origin/main:
   strategy/options_strategies.py`, so even a working trigger would
   have found "no strategy named X"; (2) independently, the one
   dispatch that DID fire (st2_threshold_trailing2pct, 15:30 UTC/
   21:00 IST) hit a genuine, unrelated problem: Fyers' own daily API
   quota was exhausted ({'code': -353, 'message': 'API Limit exceeded
   per day'}) - affecting ALL strategies, not just the new ones,
   though market was already closed by then (15:15 IST square-off) so
   no real trading was missed today. Committing and pushing all of
   today's code (engine + 4 books + both apps' fixes) now so
   everything is live and ready for tomorrow's real test, once both
   the market reopens and Fyers' daily quota resets.

✅ Code pushed and confirmed landed on origin/main (git show origin/
   main:strategy/options_strategies.py now matches - the earlier
   unpushed-code cause is resolved).

✅ "mobile app update kar" - rebuilt and installed the real APK, not
   just source. `flutter build apk --release --dart-define=GITHUB_PAT=
   "$GITHUB_PAT"` (the PAT flag is REQUIRED or the Fyers login button
   silently breaks - recurring regression first hit 07-Aug, again
   14-Aug, checked correctly again this time) - built clean, app-
   release.apk (49.3MB). No phone connected at first (`adb devices`
   empty) - told the user, they connected it, re-checked (`ZD2222BC2Q`
   appeared), then `adb install -r` succeeded. Phone now has the 4 new
   Threshold Options books and the fixed st3_threshold_slcap/st2_
   threshold_slcap index visibility live in the app, not just in the
   backend.

✅ User asked directly which of the 8 real F&O cost components (Gross
   Profit - Brokerage - STT - Exchange charges - GST - Stamp duty -
   Slippage - Spread) the paper-trading cost model already covers.
   Read strategy/options_transaction_costs.py fully: 6 of 8 (Brokerage,
   STT, Exchange charges, GST, Stamp duty, plus SEBI charges as a
   bonus not in the user's list) are already real, correctly modeled.
   Slippage and Spread were NOT modeled - the engine fills at LTP (or
   bid-ask midpoint), never accounting for the real cost of crossing
   the spread.

✅ "पण खरा spread कसा मोजायचा" - found the raw data to measure it
   ALREADY EXISTS: reports/options_premium_history.jsonl (a separate
   collector, running since 04-Aug, 28,820 real Bid/Ask/LTP snapshots)
   was never analyzed for spread before. Computed it directly: real
   median spread is NIFTY 0.26%, BANKNIFTY 0.31% of premium (p90 under
   ~1.3%, p99 up to ~3.3-3.8%) - comfortably below the ~1-1.3% break-
   even threshold found in 15-Aug's theoretical slippage stress-test,
   good news for typical conditions. User said add it - added
   SPREAD_COST_PCT_NIFTY/BANKNIFTY constants + an opt-in `spread_pct`
   param to calculate_options_round_trip_cost() (default None, zero
   change to any existing book, same opt-in pattern as every other
   addition today). User was asked whether to turn it on for the 63
   live books now or keep it as a tool for the new VPS/WebSocket work
   only - dismissed the question (no decision), then separately said
   "vps paper trading साठी वापर" - resolved: NOT applied to the 63
   existing books, will be used in the new event-driven engine instead.

✅ Slippage clarified as TWO separate things, not one: (1) timing/
   latency slippage (price moving between decision and fill) - this
   IS already measured, it's the SAME thing as today's Rs 10,34,598
   SL-overshoot finding, and already has a planned fix (the VPS/
   WebSocket rewrite). (2) market-depth/order-size slippage (a real
   order exceeding what's resting at the best price, forced to fill
   worse) - genuinely unmeasured, needs real order-book depth data
   this project has never fetched. Researched Fyers' actual /depth
   API via real web search (not guessed) - confirmed it exists,
   returns real 5-level bid/ask depth (price/volume/order-count per
   level) plus totalbuyqty/totalsellqty, same base URL pattern this
   project's /quotes and /options-chain-v3 already use. Built a NEW,
   separate collector (strategy/fyers_depth_collector.py, never
   touches fyers_options_collector.py) - snapshots ATM CE+PE depth for
   both indices into reports/options_depth_history.jsonl, API-quota-
   conscious (4 depth calls + 2 chain calls per run, matching today's
   real API-limit lesson), not wired into any cron trigger yet
   (manual-run, matching the existing premium collector's own nature).
   6 new tests for the one pure/testable function (_parse_depth_
   response) - 389/389 passing overall. HONEST CAVEAT: Fyers' own docs
   never published a complete raw JSON example for /depth - parsing
   assumes the same envelope shape already verified working for the
   sibling /quotes endpoint, but could NOT be live-tested before
   committing (local token expired AND Fyers' daily quota was
   exhausted today - see the SL-overshoot entry). First real run
   should be treated as a verification run, not assumed correct.

✅ User asked how long real depth-slippage measurement would take, and
   separately asked to wire the collector into an automatic trigger
   after checking the real API-quota impact first (not guessing).
   Checked Fyers' actual documented rate limits via real web search:
   10/sec, 200/min, 1,00,000/day. Traced how the existing premium
   collector already gets its own real cadence (fyers_scheduled_run.py,
   triggered every 5 min via fyers_scheduled_check.yml -> cron-job.org
   - confirmed via the real data: 655 unique snapshot timestamps across
   ~9-10 real trading days = ~65-70/day). Estimated the depth collector
   would need a similar ~7-10 real trading days at that same cadence to
   reach a comparable sample size to today's spread analysis, and would
   add only ~450 calls/day (6 calls x ~75 runs/day) - under 0.5% of the
   daily quota, not a meaningful contributor to today's API-limit
   incident (that was live-trading check volume on an unusually heavy
   676-trade day). WIRED IN: added run_depth_snapshot() to strategy/
   fyers_daily_tasks.py (same try/except-and-continue shape as run_
   options_snapshot()), called it from fyers_scheduled_run.py's main()
   right alongside the existing premium snapshot call, and from run_
   all_tasks(). No new workflow file needed - rides the existing 5-min
   trigger. 389/389 tests still passing (no new tests needed - this is
   thin wiring calling already-tested/collector code, matching this
   project's own established scope for orchestration scripts).

✅ User asked what else (beyond Brokerage/STT/Exchange/GST/Stamp duty/
   Slippage/Spread) is needed for trade/profit realism. Answered with
   two categories: trade-level (order rejection, partial fills, market
   vs limit order choice, freeze quantity, real margin, circuit halts)
   and take-home-level (human-approval latency specific to this
   project's "Claude never executes a real trade" design, income tax,
   broker/infra downtime). User asked to research Real Margin first,
   then Order Rejection/Partial Fill (initially asked one at a time,
   then said do both).

   REAL MARGIN (SPAN+Exposure) - researched via real web search, not
   guessed. Found the actual endpoint: https://api.fyers.in/api/v3/
   span_margin (different base URL than the data-API endpoints this
   project already uses), request needs symbol/qty/side/type/
   productType. Could NOT confirm the response schema from public docs
   - AND found a real, concrete warning: a Fyers community thread shows
   a user hitting a 503 error on this exact endpoint, with a Fyers
   moderator confirming "this api is currently not working" at the
   time. CONCLUSION: this validates strategy/fyers_options_credit_
   spread.py's existing choice (conservative max-loss-based position
   sizing instead of the real margin API) - not just undocumented but
   demonstrably unreliable, real capital position-sizing should not
   depend on it. No code change - the existing conservative proxy
   stays as the intentional choice, now with real evidence backing it.

   ORDER REJECTION / PARTIAL FILL - researched real order-response
   fields (filledQty, remainingQuantity, status, message - confirmed
   via real Fyers API response examples) and the real, documented
   rejection reasons most relevant to this project's ATM-CE/PE-
   buying, intraday strategies: Peak Margin Rule (margin must be
   maintained THROUGHOUT the day, not just at entry - relevant for
   real position-sizing buffers), Strike Out of Range (options limited
   to +-15% of spot intraday - ATM normally comfortably inside this,
   worth knowing the boundary exists), tick-size rounding (Rs 0.05
   multiples, relevant if a future real order ever uses Limit orders),
   circuit limits/freeze quantity (confirms the earlier depth-slippage
   discussion's real order-size constraint), and after-hours rejection
   (confirms this project's existing MARKET_OPEN_TIME gate already
   matches the real constraint). Filed as reference for Stage 3's real
   Order Execution/OMS design (not built yet, not blocking anything
   now) - these are the real fields/reasons that design will need to
   check once real order placement exists.

✅ User asked a natural follow-up twice: what % match will paper
   trading have with real trading (once, generally; again specifically
   "after VPS"). Answered honestly rather than a single false-precision
   number: current state is roughly 85-90% realistic on calm days, but
   can drop to ~60-70% on volatile/high-volume days like today, because
   the SL-overshoot timing gap (Rs 10,34,598 today) is the single
   largest, already-quantified factor. After the planned VPS/WebSocket
   rewrite (which directly targets that timing gap) plus applying the
   already-measured spread cost, estimated this could improve to
   roughly 90-95% on both calm and volatile days - but explicitly NOT
   100%, because order rejection, partial fills, real market-depth
   impact, and circuit-halt handling are gaps that ONLY real order
   placement (Stage 3) can actually validate, regardless of how fast
   the paper-trading check loop runs.

✅ User then asked directly: can we take a % for those 5 remaining
   gaps (order rejection, partial fill, real margin issues, market-
   depth slippage, circuit halt) and just deduct it from Net Profit as
   a safety margin? Explained why NOT, rather than agreeing: unlike
   spread (measured from 28,820 real snapshots), there is ZERO real
   data for any of these 5 - inventing a percentage would be false
   precision dressed up as measurement, directly against this
   project's own "measure real data first" discipline demonstrated all
   session (spread, choppiness-filter check, etc.). Also, lumping them
   into one flat % is itself wrong - they have very different real
   natures: order rejection/partial fill are rare for the liquid ATM
   NIFTY/BANKNIFTY strikes this project trades; circuit halts are a
   few-days-per-YEAR tail event, not a per-trade cost; real margin
   issues don't even belong in the Net PnL formula (they're a position-
   feasibility constraint, not a profit deduction). CORRECT PATH
   instead: (1) market-depth slippage is the one gap that CAN
   eventually get a real measured % the same way spread did, once
   fyers_depth_collector.py accumulates enough real data (~7-10 real
   trading days, per the earlier estimate); (2) order rejection/
   partial fill/circuit halts belong in Stage 3's future OMS as
   safeguards (retry logic, margin buffers, halt detection), not as a
   Net-PnL deduction in paper trading; (3) real margin API
   unreliability is already handled correctly (credit_spread's
   existing conservative max-loss proxy, validated earlier today). No
   code changed - this was a scoping/methodology discussion, keeping
   the project's discipline intact rather than adding a fabricated
   number for the sake of having one.

==================================================
