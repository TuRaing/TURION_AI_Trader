# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260828-001

--------------------------------------------------

Date

28-Aug-2026

--------------------------------------------------

REAL LIVE VALIDATION - 27-AUG'S STALE-TOKEN RETRY FIX WORKED PERFECTLY
ON ITS FIRST REAL TRIGGER. All 3 VPS services hit today's login gap
right on schedule (~08:46 IST, before the user's login) and did
EXACTLY what was designed the day before: no crash, no systemd
restart-limit exhaustion, one push notification, and a clean silent
retry every 120s. Once the user logged in, `turion-tick-collector`
and `turion-depth-collector` both reconnected within one retry cycle
(08:54:16 IST) with an explicit "Fetching initial ATM strikes..." log
line confirming success.

`turion-event-driven` reconnected too, but LOOKED stuck for several
minutes - Claude initially suspected a real bug (investigated process
CPU state, open sockets, systemd status) before finding the real
explanation: `strategy/event_driven_runner.py`'s own `main()`/`build_
runners()` has NO log line at all confirming a successful (re)connect
- unlike `run_tick_collector.py`/`run_depth_collector.py`'s own
explicit prints. The only confirmation is the periodic "OI snapshot
refresh OK" line, which only fires every 5 minutes - so a successful
retry can go up to ~5 minutes with zero visible log output, looking
identical to a real hang. Confirmed genuinely fine via `ss -tnp`
(a live ESTABLISHED WebSocket connection to a Cloudflare IP) and
later the 09:16 IST scheduled check (OI-refresh lines + real trades
already flowing). NOT a bug - a real gap in this module's logging
that made a working system look broken. Flagged, not fixed this
session (low priority, cosmetic - the process was never actually
stuck).

Also noticed (not fixed, low priority): `turion-event-driven`'s
socket list showed 5 stale `CLOSE-WAIT` connections to Firebase-
related IPs, one per retry attempt made before today's login - likely
`report/firebase_realtime_sync.py`'s `fetch_access_token()` not
cleanly closing its HTTP connection on each call. No functional
impact observed (reconnected and traded normally once the token was
valid), just a minor resource-leak note for a future cleanup pass.

==================================================

OI_FOOTPRINT STRATEGY FAMILY VERIFIED HEALTHY (all 4 books). User
asked to specifically check whether oi_footprint was "working
correctly" after the previous day's whipsaw. Inspected real trade-
by-trade data:

- `oi_footprint_eventdriven_nifty` / `oi_footprint_quote_eventdriven_
  nifty`: real, sensible Target/Stop-Loss sequences from 09:19-09:20
  IST, premiums moving logically, PnL consistent with position sizing
  - clearly working as designed.
- `oi_footprint_eventdriven_banknifty` / `oi_footprint_quote_
  eventdriven_banknifty`: zero trades, Position: None - NOT a bug.
  `journalctl` confirmed the "OI snapshot refresh OK" line firing
  cleanly every 5 minutes for the whole morning with zero errors -
  the OI data pipeline is healthy, BankNifty's own entry condition
  (an OI buildup pattern) simply hadn't triggered yet. A quiet book
  with a healthy data feed is a different, harmless state from a
  stuck one - confirmed the distinction with real log/file evidence
  rather than assuming either way.

==================================================

TODAY'S TRADING SNAPSHOT (as of ~09:29 IST, still early in the day) -
14 VPS event-driven books, total so far Rs -19,983:

Profitable: simple_st1_threshold_lock (+Rs 5,517), st2_threshold_lock
(+Rs 2,720), oi_footprint_quote_nifty (+Rs 1,658), oi_footprint_nifty
(+Rs 1,024), simple_st1_threshold (+Rs 790).

Loss / N=2-locked: all 6 "_lock_quote0.5/1/2pct" books hit their N=2
breaker again this morning (-Rs 4,421 each - same market-open whipsaw
pattern as yesterday), plain st2_threshold (-Rs 5,166, not yet
locked).

No trades yet: oi_footprint_banknifty, oi_footprint_quote_banknifty
(see above - healthy, just no signal yet).

Separately confirmed all 74 local + VPS portfolio files show zero
activity outside this set - no other book has traded today as of this
check.

==================================================

==================================================

REAL INCIDENT (28-Aug evening) - VULTR CPU-ABUSE TICKET + VPS REBOOT
FROM RUNNING BACKTESTS ON THE LIVE VPS. Hours of heavy scratch-
backtest scripts (cooldown, order-book imbalance, VWAP, ORB, volume-
spike, then a market-open-buffer test) were run directly on the live
1vCPU/1GB VPS - the same machine running the 3 real trading services.
User received a real Vultr email/auto-ticket: "your CPU resource
utilization profile is excessive... we have limited the maximum CPU
resources your instances can consume." Checked live: the VPS had just
rebooted (~7 min uptime, load average 1.31 on 1 core) - almost
certainly Vultr's enforcement. All 3 live services recovered on their
own (systemd Restart=on-failure) - no manual fix needed, no confirmed
trading impact, but genuinely avoidable and close.

Root cause: backtests were run on the wrong machine - there was never
a technical need for the VPS itself, only its archived tick/depth
data, which copies down via scp just as easily. Killed the running
backtest immediately. New PERMANENT rule: all backtest/analysis
workloads run locally (or a separate box) from now on, copying only
the needed day's archive file(s) down first - the VPS is for the 3
live services only. See [[project_vps_migration_on_live_trading]] and
[[project_quote_pnl_and_whipsaw_decision]] memories for the full note.

==================================================

4 NEW-STRATEGY BACKTESTS RUN FOR REAL, SAME DAY + OI ARCHIVAL BUILT
AND DEPLOYED LIVE. Followed the cooldown backtest below with real
standalone backtests (same LiveTickRunner-replay pattern, real tick/
depth archive) of 4 proposed new strategies, reusing the existing
Target/hybrid-SL exit math so only the entry signal differs:

Volume-spike breakout: +Rs 2,123 combined (6 days x 2 indices, best of
the 4) - notably profitable on 21-Aug (the worst RSI whipsaw day) on
BOTH indices. Order-book imbalance: -Rs 97,908 (worst on BankNifty,
0 wins on 3 of 5 days). ORB (options-level): -Rs 121,076. VWAP
(options-level): -Rs 221,225 (worst, 393 trades - too noisy). Only
volume-spike breakout is worth a second look; the other 3 in this
simple form showed no real edge.

GEX-wall momentum-exhaustion, the PCR event-driven port, and the
oi_footprint OI+Volume filter all stayed blocked on the same real gap:
OI has only ever been read live, never archived. User asked to fix
this ("OI collect karayla suruvat") - built strategy/oi_collector.py
(pure record-shaping, mirrors depth_collector.py's pattern) + a small
append hook inside event_driven_runner.py's existing refresh_oi_
snapshots() - purely additive, reuses the SAME real REST call already
made every ~5 min for the 2 live oi_footprint books, no new API load,
no change to any decision logic. 3 new tests, 621/621 passing,
deployed to VPS same day as `turion` (not root), turion-event-driven
restarted cleanly. Writes data/oi/oi_DDMMYY.jsonl - live verification
of the first real write is in progress as this entry is written (past
market close, so today's own file may only get 0-1 real snapshots -
tomorrow's session should confirm it's accumulating properly).

See [[project_quote_pnl_and_whipsaw_decision]] memory for full numbers.

==================================================

COOLDOWN BACKTEST - REAL RESULTS, RUN THE SAME DAY (user chose "doc
kar backtest karu" -> "backtest chalu karu" - started immediately
rather than waiting for 29-Aug). Built a standalone experimental
harness (a throwaway script, NOT touching the real live decide_fn)
that replays real archived tick data through the SAME LiveTickRunner
state-assembly production uses, testing a cooldown-after-close gate at
0/30/60/120/300 seconds against ALL 6 real trading days for BOTH
NIFTY and BankNifty (st2_threshold cfg). Hit and fixed one real bug
live: the daily tick-compression cron gzipped 27-Aug's file mid-run -
script now handles both .jsonl and .jsonl.gz transparently.

Combined totals across all 8 day/index runs: baseline (0s) -Rs 770,740
total loss; 300s cooldown -Rs 266,558 - a ~65% reduction, the
strongest and most consistent performer. Most dramatic single case:
25-Aug BankNifty baseline had 1,594 trades (-Rs 345,802) - a 30s
cooldown alone cut it to 378 trades and flipped the day to +Rs 24,710
profit. Caveat: NOT monotonic - 60s/120s were sometimes worse than
baseline, and the single best value differs day to day - 300s is the
strongest overall candidate from this data, not a proven universal
optimum. Still backtest-only, nothing deployed live. Before any real
deployment: needs more days, a check against interaction with the
existing N=2 daily_loss_lock breaker, and the same test on oi_
footprint. See [[project_quote_pnl_and_whipsaw_decision]] memory for
the full per-day numbers.

==================================================

ROOT CAUSE FOUND - WHY THE RSI-MOMENTUM BOOKS ARE MOSTLY NET NEGATIVE.
User asked directly "RSI ka chukat aahe" (why is RSI going wrong)
after seeing the all-14-books-combined all-time PnL: Rs -245,707,
5 of 6 real trading days net negative (21-Aug -90k, 24-Aug -39k,
25-Aug -60k, 26-Aug +25k, 27-Aug -61k, 28-Aug -20k so far). Investigated
with real data rather than guessing: `_rsi_momentum_decide()` in
strategy/event_driven_engine.py picks direction with `RSI >= 50 -> CE
else PE`, computed once per closed 5-min candle - but when flat, it
re-checks and reopens on EVERY tick with zero cooldown. Proven on real
`st2_threshold` trades (27/28-Aug): the gap between one trade's Exit
Time and the next trade's Entry Time was 0.0 seconds in nearly every
case, six trades in a row, all the same direction (PE) - since RSI
hadn't changed within that 5-min window, a noisy/wide option bid-ask
spread right at market open kept re-triggering the tight Target/Stop-
Loss on the same side, each round-trip paying real spread cost (some
of the same-second re-entries even hit Target, not just SL - the
direction was often right, the re-entry cost was the problem).

This is NOT a new root cause - it's the same mechanism already found
21-Aug (which motivated the N=2 `daily_loss_lock` breaker) - this
session's investigation just re-confirmed it with sharper, harder
numbers (0.0s gaps) rather than discovering something new. The breaker
caps the DAMAGE (stops after 2 losses) but was never a fix for the
zero-cooldown re-entry mechanism itself.

User's decision: build a cooldown/confirmation gate before re-entry -
explicitly deferred to a BACKTEST tomorrow (29-Aug), not built/
deployed today. See [[project_quote_pnl_and_whipsaw_decision]] memory
for the full note.

==================================================

NEW STRATEGY IDEAS PROPOSED (28-Aug), 4 options, backtest planned for
THIS EVENING (after market close). User asked for genuinely new
strategies, not just an RSI fix. Proposed, grounded in infra already
built (explicitly did not re-propose trailing-SL/IV-filter/Kelly-
sizing - already backtested and rejected earlier):

1. Order-book imbalance (recommended first) - uses the depth archive
   (collected since 24-Aug) as a live signal for the first time, not
   just post-hoc slippage analysis.
2. VWAP-based momentum/reversion - tick archive already has volume per
   leg.
3. Volume-spike breakout - reacts faster than RSI's 5-min-candle lag.
4. PCR event-driven port - `pcr_momentum`/`pcr_vix_combo` already
   exist in the older polling engine; port with cooldown/breaker built
   in from day one.

Nothing built yet - backtest first, per the same data-driven-patience
discipline as every other change on this project.

==================================================

WEB RESEARCH - 2 MORE IDEAS FOUND, 2 ALREADY-PROPOSED ONES
CORROBORATED. User asked Claude to web-search for proven ideas.
Added:

5. Opening Range Breakout (ORB) - wait for the first 15-30 min range
   to form, only enter on a real breakout beyond it. This is a TESTED
   version of the market-open buffer-time idea from 27-Aug - real
   backtests found (NIFTY 8-year: 2,122 trades, 48.7% win rate, +91.6%
   total return, profit factor 1.23; a Jul-Oct 2025 Nifty-futures
   backtest: 57% win rate, 2.88% return). One finding independently
   matches this project's own earlier result: "fixed targets beat
   trailing stops" - this project already backtested trailing-SL and
   found it made things worse (22-Aug).
6. OI+Volume combined confirmation filter - not a new strategy, a
   cheap improvement to the EXISTING oi_footprint book (high volume+
   rising OI = strong signal, high volume+flat OI = noise, high
   volume+falling OI = unwinding).

VWAP and order-book-imbalance (already proposed) both got real
external corroboration (VWAP: 65-68% win rate in trending conditions;
order-book imbalance: academic research confirms a near-linear
relationship with short-horizon price moves, strongest within tens of
seconds).

Full list now 5 new-strategy ideas + 1 cheap existing-book
improvement. Backtest timing loosened by the user to "sandyakali kiva
udya" (this evening OR tomorrow, 29-Aug) - not a hard commitment to
tonight. See [[project_quote_pnl_and_whipsaw_decision]] memory for
full detail and sources.

==================================================

VERIFIED 3 ROUNDS OF PASTED CHATGPT OPTIONS-STRATEGY RESEARCH AGAINST
REAL WEB SOURCES. User pasted three successive rounds of ChatGPT-
generated options-strategy research (VRP/regime ideas, GEX-wall
momentum exhaustion, "compression -> gamma trigger -> breakout" option
buying) and asked Claude to independently verify each before trusting
it. Ran real web searches against every specific, checkable claim
rather than accepting the summaries at face value.

Pattern found across all 3 rounds: GPT's underlying financial/quant
LOGIC was almost always real and independently confirmable, but its
SPECIFIC NAMED CITATIONS were frequently unreliable - a named open-
source tool ("bhav"), a named bias-analysis source ("MoneyTicks"), and
specific Barron's/MarketWatch articles could not be found by Claude's
own search, despite the underlying concepts being real via OTHER
genuine sources. One claim was actively wrong, not just unverifiable:
GPT said a 2026 SSRN S&P 500 study found IV/skew/put-call metrics have
"no predictive significance" for breakout failure - Claude found real
papers (including one by Vilkov, the same author behind the separately
-verified 0DTE research) showing the opposite - skew/PCR DO carry some
real predictive power.

What DID verify as real and useful:
- Nifty VRP is real but not retail-capturable: a second real paper
  (Sumin Pillai, SSRN) backtested 4 short-vol Nifty strategies with
  realistic costs (STT/brokerage/slippage) over 119 monthly expiries
  (2015-2025) - ALL net negative, best case (put-write) still -0.9%
  annualized, Sharpe -0.37. Confirms: don't build a pure premium-
  selling strategy on the "VRP exists" argument alone.
- A REAL, already-written open-source backtest exists for "GEX-wall +
  momentum-exhaustion credit spread" (github.com/sujoypaulhome/
  0dte-gex-backtest, real option prices via Polygon API) - the single
  most actionable lead found this session, since every other idea
  needs to be built from scratch.
- Vilkov's 0DTE replication package and the Wallmeier 2025 skew-
  premium paper both independently confirmed as real.

Final candidate ranking (user's own, after all 3 rounds): (1) full
Adaptive Gamma+IV/RV+regime classifier - multi-week scope, not a quick
backtest; (2) GEX-wall momentum exhaustion - most tractable, real code
exists; (3) IV/RV+skew relative value; (4) "Compression->gamma
trigger->confirmed breakout->option buy" - internally coherent logic,
but no combined backtest exists anywhere yet, genuinely untested.
Pure option-selling explicitly rejected (now doubly disproven).

Nothing built - this was pure research/verification. See
[[project_quote_pnl_and_whipsaw_decision]] memory for full detail and
all sources.

==================================================

"EXPECTED MOVE" OPTION-BUYING IDEA - REAL PHASE-1 DATA CHECK RUN, ONE
SOBERING AND ONE USEFUL FINDING. Follow-on from the research thread
above: settled on comparing a forecast of future realized volatility
against an option's own implied move as a more principled basis for
option buying than GEX-wall signals. User correctly flagged the real
blocker before any code was written: our own real options archive is
only ~6 days old (21/24-28 Aug) - nowhere near enough for a real
strategy backtest.

Checked what IS possible with available data: yfinance has 5 real
years of both NIFTY (^NSEI) and India VIX (^INDIAVIX) daily history
(confirmed live, 1236/1230 rows). Ran a real Phase-1 check (1190 usable
days) comparing 3 forecasters of the next 20 trading days' realized
vol - naive rolling RV, Yang-Zhang (OHLC-based), and India VIX itself:

Naive RV: RMSE 5.92, corr 0.347. Yang-Zhang: RMSE 5.44, corr 0.440.
India VIX: RMSE 4.61, corr 0.629 - BEST of the three. Finding: the
market's own implied vol already beats simple homemade forecasts -
weakens the "out-forecast the market" premise for this strategy.

But: VIX has a strong, persistent bias - overstates future realized
vol by +2.18 vol points on average, 78.3% of days. Independently
reconfirms the VRP finding from the real Agarwal/Pillai papers found
earlier this session, now on our own 4-year sample. A simple "VIX
minus its own historical bias" is a much more tractable next test than
building HAR-RV/GARCH from scratch.

Decision: document and defer ("doc kar backtest karu") - joins the
evening/tomorrow backtest queue. See [[project_quote_pnl_and_whipsaw_
decision]] for full numbers.

==================================================

Status

🟢 Stable

Current Version

v0.0.67

Next Version

v0.0.68

--------------------------------------------------

Next Session

-1. Confirm data/oi/oi_DDMMYY.jsonl is genuinely accumulating real
   snapshots on real trading days (deployed late 28-Aug, past market
   close - not yet confirmed live). Once a few real days exist, GEX-
   wall momentum-exhaustion, the PCR event-driven port, and the
   oi_footprint OI+Volume filter all become backtestable.

0. TWO backtests planned, not yet run, timing flexible ("sandyakali
   kiva udya" - this evening or tomorrow, user's own words):
   (a) 5 new strategy ideas (order-book imbalance, VWAP, volume-spike
       breakout, PCR event-driven port, Opening Range Breakout) + 1
       cheap oi_footprint OI+Volume filter improvement - against real
       tick/depth archive data.
   (b) A cooldown/confirmation gate for the existing RSI-momentum
       re-entry logic (see root-cause finding above).
   Do not deploy either without showing the user real backtest
   numbers first.

1. `event_driven_runner.py`'s missing "reconnected successfully" log
   line (see above) is a real, if low-priority, gap - worth a one-line
   fix (print on successful `build_runners()`/socket connect) so a
   future retry-recovery doesn't need this same live investigation
   again. Not done this session - flagged only.

2. The Firebase `CLOSE-WAIT` socket leak on repeated `fetch_access_
   token()` retries (see above) - low priority, no functional impact
   observed yet, but worth checking `report/firebase_realtime_sync.py`
   for a missing `response.close()`/session reuse if it recurs or
   grows across more retry cycles.

3. TODAY (28-Aug) is the quote-fix vs plain-LTP checkpoint day the
   user set on 26-Aug - watch for the user to raise it; don't
   preemptively backtest/decide without them.

4. Carried over: the market-open buffer-time idea (27-Aug, see that
   day's log) is still explicitly deferred to the weekend - don't
   build without the user raising it again.

5. Carried over from 24-Aug, still open: `turion-tick-collector`'s own
   VPS-level auto-retry cron lines, `sync_ticks_from_vps.py` exercise,
   end-Sep-2026 statistical-tools checkpoint.

==================================================
