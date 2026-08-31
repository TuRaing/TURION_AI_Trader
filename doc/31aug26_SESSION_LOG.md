# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260831-001

--------------------------------------------------

Date

31-Aug-2026

--------------------------------------------------

31-Aug IS THE FIRST REAL TRADING DAY SINCE 29-Aug's NEW WEEKEND-DEPLOY
FIX AND 28-Aug's PERF FIX. Session-start check: `af0816c41` deployed to
the VPS cleanly at 08:00 IST (the routine daily deploy.sh cron found
new commits from over the weekend). All 3 services came up active -
first real confirmation that `turion-tick-collector`/`turion-depth-
collector` recover correctly on their own (29-Aug's crontab fix, not
yet tested until today).

==================================================

REAL LOGIN INCIDENT - ROOT-CAUSED AND FIXED, NOT JUST WORKED AROUND.
User reported today's login only sent an email OTP + password (no
TOTP as usual) and pasted the raw Fyers OAuth redirect URL (containing
a live, one-time auth_code) directly into chat after repeated ("12
वेळा") attempts via the app's own "Login to Fyers" screen still left
the VPS retrying on an invalid token.

Manually completed the login for the user this once (extracted the
auth_code, dispatched `.github/workflows/fyers_trigger.yml` via the
GitHub API using the local `GITHUB_PAT`) - confirmed live afterward
(VPS logs: "OI snapshot refresh OK", no more "invalid token" retries).

Investigated the real root cause rather than assuming the app was
broken: checked today's actual `fyers_trigger.yml` run history via the
GitHub API - only 3 runs existed today (not 12), 1 FAILED with
`RuntimeError: Fyers auth-code exchange failed: {'code': -1, 'message':
'invalid auth code'}`, 1 SUCCEEDED (and had already pushed a valid
token to Firebase ~1 minute before Claude's own manual trigger, making
that manual trigger redundant but harmless). Root cause: Fyers'
auth_code is single-use and short-lived - reusing an old copy (a
previous browser tab, a delayed paste) fails cleanly on Fyers' side,
but the app's "Login to Fyers" screen only ever checked whether the
GitHub Actions DISPATCH was accepted (HTTP 204), never whether the
actual auth_code exchange inside the workflow succeeded - so the user
saw an identical "Triggered! success" message whether the run
succeeded OR failed inside, with no way to tell which.

FIXED (commit a7f70e3d7 -> rebased as 1ac92e45a after a `git pull
--rebase` past a batch of unrelated automated `[skip ci]` commits):

1. `fyers_login_screen.dart` now polls the actual workflow run's
   `conclusion` (up to ~2 min, matched to the dispatch by created_at)
   before declaring success - shows the real error (e.g. "auth_code
   was likely already used or expired") on a genuine failure instead
   of a false "success".
2. `strategy/event_driven_runner.py` (on a successful `build_runners()`
   - real proof today's token works) and `run_event_driven_engine.py`
   (on each stale-token retry) now sync a live `engine_status/token`
   ready/not_ready state to Firebase via the existing `sync_state()`.
   Also closes 28-Aug's separately-flagged gap: this module never had
   a log line confirming a successful (re)connect.
3. `event_driven_realtime_service.dart`'s new `watchTokenStatus()` and
   a new badge on the VPS tab (next to the login button) surface this
   live, directly from the VPS - no more inferring login success from
   the dispatch call's own HTTP status.

`flutter analyze`: clean. Python: 621/621 tests pass. VPS-side deploy
and a fresh APK build are both explicitly deferred to this evening
(user's own call - market was about to open, did not want a live-engine
restart or new install mid-decision).

==================================================

TODAY'S LIVE TRADING - REAL DATA PULLED AND ANALYZED (09:15-09:26 IST,
first ~11 minutes). All 14 event-driven books: 43 trades, combined
**-Rs 2,70,005.24**. 12 of 14 books already breaker-STOPPED (N=2) within
the first 11 minutes; only `oi_footprint_banknifty`/`oi_footprint_
quote_banknifty` still running (both green, +Rs 5,090/+Rs 2,856).

Investigated WHY `simple_st1_threshold` (and its 3 LTP-based siblings:
`simple_st1_threshold_lock`, `st2_threshold`, `st2_threshold_lock`) lost
an unusually large -Rs 54,747.89 each (vs -Rs 7,760 for their `_lock_
quoteX%` siblings) - pulled the real trade JSON rather than guessing.
Root cause: the FIRST LTP tick of the day (09:15:00.000) read Entry
Premium 104.75 - the very next tick, SAME SECOND, showed 62.80, with
spot completely unchanged (24117.1 both times) - a ~40% "move" with
zero underlying price change is not a real market move, almost
certainly a stale/pre-open theoretical print, not a genuinely
tradeable price. Confirmed via the SAME trade's own recorded `Net PnL
(Quote)` field: +Rs 78,905.96 (a real PROFIT under quote/bid-ask
accounting) versus the LTP-based -Rs 16,823.83 (a LOSS) - direct proof
this was an LTP data artifact, not a real loss, for that specific
trade. The book's other same-second trade (Entry 104.75 -> Exit 62.80,
-Rs 37,924.06) has no quote data at all (quote fields all 0.0 -
bid/ask genuinely weren't available yet at that instant), consistent
with this being the very first tick of the day.

==================================================

LTP vs QUOTE BACKTEST - CORRECTS CLAUDE'S OWN SAME-DAY WRONG
RECOMMENDATION. Based on the single live anecdote above, initially
recommended switching the 4 remaining plain-LTP books to the already-
existing quote-based decide_fn (`rsi_momentum_quote_decide_fn`, entry
at ask/exit at bid instead of LTP/LTP) - the SAME real, unmodified
`_rsi_momentum_decide()` production function, just called with
different price fields. Built `scratch_quote_vs_ltp_backtest.py` (same
RSI-seeded LiveTickRunner-replay pattern, real N=2 breaker on) to check
this against the same 5 real days x 2 indices used all week, rather
than generalizing from one trade.

Combined PnL:

- LTP (current): -Rs 75,024
- **Quote ask/bid (the just-proposed change): -Rs 1,65,921 - 2.2x
  WORSE, not better**

Worst individual cases: 27-Aug BankNifty LTP +Rs 3,204 vs Quote
-Rs 30,160; 28-Aug BankNifty LTP +Rs 6,047 vs Quote -Rs 63,644. Root
cause of the reversal: quote-based pays the REAL bid-ask spread on
EVERY entry/exit, including this strategy's already-frequent same-
second whipsaw re-entries - each of those pays full spread cost twice
(once each direction), which compounds badly precisely because the
strategy re-enters so often. Quote-based PnL is more ACCURATE (avoids
illusory stale-print gains/losses like today's), but that accuracy
does NOT translate to lower losses here - if anything the opposite,
in this sample. Corrected recommendation explicitly given back to the
user same-day: do NOT switch these 4 books to quote-based. The narrower,
still-open question is whether a targeted stale-first-tick sanity
check (distinct from a wholesale LTP-vs-quote switch) would help
without also paying quote's full spread cost on every whipsaw re-entry
- not built or tested yet.

The already-verified best lever remains 29-Aug's combined 15-min
buffer + 120s cooldown result (+Rs 10,027 net, first profitable
combined-variant result this week) - unaffected by today's LTP/quote
finding, since it changes WHEN entries happen, not which price field
they use.

==================================================

STALE-PRINT DEBOUNCE BACKTEST - THE BEST RESULT FOUND ALL WEEK. The
narrower fix flagged as still-open above: instead of switching decide_
fn's PRICE SOURCE (quote, proven worse), require each CE/PE leg to have
received at least N ticks TODAY before trusting its premium for a NEW
entry - still plain LTP, no spread cost, just "don't act on the very
first, possibly-stale print." Built `scratch_stale_print_backtest.py`
(same RSI-seeded LiveTickRunner-replay pattern, real N=2 breaker),
swept N = 0/5/10/15/20 across the same 5 days x 2 indices.

Combined PnL:

- 0 (baseline): -Rs 75,024
- 5 ticks: -Rs 40,062
- **10 ticks: +Rs 37,004 - net PROFIT, the single best result of any
  idea tested this entire week** (beats buffer alone -Rs 3,387,
  cooldown alone -Rs 67,075, buffer+cooldown combined +Rs 10,027, and
  obviously quote-based -Rs 1,65,921)
- 15 ticks: -Rs 31,919
- 20 ticks: -Rs 12,161

NOT monotonic (10 is a clear peak, 15/20 both worse) - real caveat:
whether "10" is a genuine sweet spot or a lucky fit to this specific
5-day sample is not yet known; this swept 5 different N values against
the same small sample, which increases (not eliminates) that risk.
Still the strongest, most promising candidate found this week -
combining it with the buffer+cooldown result is the natural next step.

==================================================

ALL 3 GATES COMBINED (`scratch_triple_combined_backtest.py`, 8 variants
x same 10 day/index runs) - FOUND A REAL, COUNTERINTUITIVE INTERACTION:
adding the market-open buffer to the stale-print debounce THROWS AWAY
the debounce's own benefit rather than adding to it.

Full ranking (combined PnL):

1. 10-tick debounce alone: +Rs 37,004 (best)
2. Cooldown + debounce: +Rs 22,724
3. Buffer + cooldown (= all 3 combined, identical): +Rs 10,027
4. Buffer alone: -Rs 3,387
5. Cooldown alone: -Rs 67,075
6. Baseline: -Rs 75,024

Root cause of the interaction: `buffer + debounce`'s per-day numbers are
IDENTICAL to `buffer alone`'s, and `all 3 combined`'s are IDENTICAL to
`buffer + cooldown`'s - the 15-min buffer already delays any entry past
09:30, by which point far more than 10 ticks have already arrived on
both legs, so the debounce condition is already satisfied before the
buffer even lifts - it never actually gates anything once stacked
behind the buffer. Practical conclusion: do NOT combine the buffer with
the debounce - it silently cancels the debounce's own (much larger)
benefit and falls back to the buffer's weaker level instead. The two
real candidates going forward are debounce alone or debounce+cooldown,
not any variant involving the buffer.

Same overfitting caveat as every backtest this week applies with extra
force here - 8 variants were compared on the same 5-day sample, on top
of the 5-value N sweep that already picked "10" from the same data.
Nothing deployed. See [[project_quote_pnl_and_whipsaw_decision]] memory
for the running note.

==================================================

3 "OUT OF THE BOX" IDEAS TESTED, ALL 3 NEGATIVE - USEFUL, NOT WASTED.
User explicitly asked for genuinely different angles (not another
tweak on the same gates). Tested 3 real ideas rather than just
brainstorming:

1. Spread-widening as a CONTINUOUS (not just opening-minutes) filter -
   skip a new entry whenever a leg's bid-ask spread exceeds a multiple
   of its own recent rolling median. Combined PnL across the same 5
   days x 2 indices, multiplier 1.5x/2x/3x/5x: all 4 variants WORSE
   than baseline (-Rs 79,150 to -Rs 86,376 vs -Rs 75,024). Root cause
   of the failure: the filter needs 5+ prior ticks to establish a
   baseline before it can detect an anomaly - exactly unavailable at
   the market-open moment where the real stale-print problem lives, so
   it never protects against the case that motivated it, while still
   occasionally blocking genuinely fine mid-day trades elsewhere - net
   negative. `scratch_spread_widening_backtest.py`.

2. NIFTY-vs-BankNifty lead-lag - a pure statistical check (not a
   trading backtest), `scratch_leadlag_analysis.py`: 1-second-resampled
   cross-correlation between NIFTY's and BankNifty's spot returns at
   lags from -30s to +30s, run on 4 of the 5 days. Consistent result
   every day: correlation peaks AT lag=0 (0.48-0.53), everywhere else
   near-zero (|corr| < 0.11). No exploitable lead-lag relationship -
   the two indices move together contemporaneously, not one predicting
   the other with a tradeable delay. Ruled out.

   Found and fixed a real, separate data-quality bug while building
   this: a small number of tick-archive records carry a corrupt
   epoch-underflow timestamp ("1901-12-14...") mixed into real 2026
   data - blew up a pandas resample() call trying to allocate a
   ~124-year date range (29GB). Filtered to year>=2020 as a guard in
   the analysis script; the archive files themselves were not touched.
   Worth a look at whatever timestamp-parsing path produces these if
   it recurs elsewhere.

3. Weekly-expiry-day awareness - checked which of the 5 sample days
   was itself an expiry day by reading the real ATM symbol's own
   expiry code from the archive rather than guessing: 26-Aug (a
   Wednesday) was the expiry for the contract used across 21/25/26-Aug;
   27/28-Aug already show the next cycle's symbol. 26-Aug NIFTY had the
   single worst loss in the whole 5-day sample (-Rs 43,523) - a real,
   suggestive observation, but from exactly ONE expiry-day sample.
   Genuinely inconclusive - would need several more expiry days (the
   weekly cycle only gives ~4-5/month) before this is anything more
   than an anecdote. Not backtested further today.

Net effect: none of today's 3 new ideas add anything - the 10-tick
debounce (+ optionally cooldown) from earlier remains the single best,
most promising lever found this week. Ruling these 3 out is itself
useful (saves re-investigating them later) rather than wasted effort.

==================================================

SUPPORT/RESISTANCE GATE ADDED, THEN A FULL 3-GATE COMBO BACKTEST -
DEBOUNCE ALONE STILL WINS. User asked for one more genuinely different
angle: block a CE entry too close to recent resistance, a PE entry too
close to recent support (adapts strategy/signal_engine.py's EXISTING
apply_support_resistance_filter() - built for the older polling engine,
never wired into the event-driven RSI-momentum books - into a gate on
top of _rsi_momentum_decide, using a 30-min rolling spot high/low
instead of that function's original 20-DAILY-candle version).
`scratch_support_resistance_backtest.py`. Hit and fixed a real O(n)-
per-tick perf bug on the first attempt (min()/max() over the whole
window every tick - 19 MINUTES for one day) with a proper O(1)-
amortized sliding-window max/min via two monotonic deques - same class
of bug as 29-Aug's RSI/PnL caching fix.

Combined PnL by buffer %, real N=2 breaker: 0.1% -Rs 47,714; 0.2%
-Rs 34,690; 0.3% -Rs 27,864 (best, ~63% better than baseline, and a
genuinely clean monotonic curve unlike the other gates); 0.5%
-Rs 30,649 (over-blocks - several days show 0 trades). Real, but still
net-negative alone - weaker than the debounce.

Then built `scratch_full_combo_backtest.py` - all 8 combinations of
debounce (10 ticks) / cooldown (120s) / S-R (0.3%, 30-min lookback),
deliberately excluding the market-open buffer (already proven to
cancel debounce's benefit). Combined PnL:

1. Debounce alone: +Rs 37,004 (still the single best - unbeaten by
   ANY combination tried this week)
2. All 3 combined: +Rs 31,411
3. Debounce + cooldown: +Rs 22,724
4. Debounce + S/R: +Rs 11,017
5. Baseline: -Rs 75,024
6. S/R alone: -Rs 27,864
7. Cooldown + S/R: -Rs 40,736
8. Cooldown alone: -Rs 67,075

Consistent pattern across every combination tested this week: stacking
ANY other gate on top of the debounce dilutes it rather than improving
it - the debounce alone remains the strongest, cleanest candidate.

APPLIES TO (real gap check, not assumed): `_rsi_momentum_decide` -
which all of today's gates wrap - is the decide_fn behind exactly 10
of the 14 live event-driven books (all NIFTY): `simple_st1_threshold`,
`simple_st1_threshold_lock`, its 3 `_lock_quote0.5/1/2pct` siblings,
`st2_threshold`, `st2_threshold_lock`, and its 3 `_lock_quote0.5/1/2pct`
siblings. Does NOT apply to the 4 `oi_footprint`/`oi_footprint_quote`
books (NIFTY+BankNifty) - those run a different decide_fn (OI-buildup
based), untested by any of this week's gates.

Still backtest-only - same overfitting caveat as every combo tested
this week (5-day sample, many variants compared against it). Debounce
alone remains the strongest single candidate if/when a real deploy
decision is made.

==================================================

Status

🟢 Stable

Current Version

v0.0.70

Next Version

v0.0.70 (login-flow fix + VPS status indicator pushed to GitHub, not
yet deployed to the VPS or rebuilt as an APK - both explicitly deferred
to this evening per the user's own call; all backtest work today stays
backtest-only)

--------------------------------------------------

Next Session

1. This evening (per the user's own plan): deploy today's `af0816c41`
   -> `1ac92e45a` range's backend changes to the VPS (after market
   close), and trigger a fresh APK build so the login-flow fix and VPS
   status badge actually reach the phone.

2. Do NOT switch the 4 plain-LTP books to quote-based decide_fn - today's
   backtest showed this makes things worse (2.2x), reversing Claude's
   own same-day initial recommendation. If revisited, investigate a
   narrower stale-first-tick sanity check instead (untested idea, not
   built).

3. Carried over from 29-Aug: the combined 15-min buffer + 120s cooldown
   result (+Rs 10,027) is still the single strongest verified lever
   found this week - still needs more real trading days before any
   deploy decision (only 5 days backtested, explicit overfitting
   caveat already noted 29-Aug).

4. Watch whether `oi_footprint_banknifty`/`oi_footprint_quote_
   banknifty` (the 2 books still running as of 09:26 IST today) stay
   the only survivors for the rest of the day, or whether more books
   re-enable tomorrow (the N=2 lock resets daily).

5. Today's OI archive (`data/oi/oi_310826.jsonl`) is the first full
   real trading day - once market closes, this finally unblocks the
   PCR event-driven port / GEX-wall momentum-exhaustion / oi_footprint
   OI+Volume filter backtests that have been blocked since 28-Aug.

==================================================
