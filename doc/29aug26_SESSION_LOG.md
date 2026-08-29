# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260829-001

--------------------------------------------------

Date

29-Aug-2026

--------------------------------------------------

SESSION-START CHECK (per CLAUDE.md continuity rules) - CLEAN, NO
INCIDENT. `git fetch origin` + `git log HEAD..origin/main` - nothing
to pull, `main` already up to date. Found one unmerged branch,
`crypto-paper-trading` (6 commits ahead of `main`, incl. a systemd unit
for the crypto engine "live-tested on the real VM") - a separate,
deliberately-unmerged track (Deribit BTC/ETH paper trading), not
another session's in-progress duplicate of today's work; confirmed the
main VPS (65.20.78.253) runs no crypto service, so that "real VM" is a
different box.

VPS check: all 3 live services (`turion-tick-collector`, `turion-
depth-collector`, `turion-event-driven`) active, uptime 15h46m since
yesterday evening's clean restart (post Vultr-CPU-abuse-incident
reboot, see 28-Aug log), load average 0.03, disk 40% used, zero
root-owned files (no ownership drift). OI archive (`data/oi/`)
genuinely accumulating (28-Aug and 29-Aug files present). Saw
continuous "Please provide valid token" retries all morning (27-Aug's
stale-token retry fix doing its job) - confirmed harmless: **29-Aug is
a Saturday, market closed**, so there is no login today and the retry
loop is expected to run all day with no functional impact.

==================================================

MARKET-OPEN BUFFER BACKTEST - REAL RESULTS, AFTER FIXING BOTH A
METHODOLOGY BUG (28-Aug) AND A REAL PRODUCTION PERFORMANCE BUG (today).
Continuation of the market-open-buffer idea 27-Aug deferred to the
weekend (see that day's log) - user's own report at the start of this
session: yesterday's backtest run had "kahi tari bug" (some bug), a
corrected version was started again this morning, and the Windows
Claude app crashed before it finished - asked to re-run it.

Investigated rather than blindly re-running:

1. Yesterday's `scratch_buffer_backtest.py` (28-Aug) had a real
   methodology bug, documented in today's own `scratch_buffer_
   backtest_v2.py` docstring: `CandleAggregator` was left unseeded, so
   RSI only became available ~75 minutes after the archive's first
   spot tick (`MIN_CANDLES_FOR_RSI=15` closed 5-min candles from cold
   start) - coincidentally landing around 09:35 regardless of the
   buffer setting, making every buffer value look identical. Not a
   real finding.

2. This morning's fix (`scratch_buffer_backtest_v2.py`, already
   written before the crash) seeds `CandleAggregator` with real
   historical 5-min candles the same way production does
   (`event_driven_runner.py`'s `RSI_SEED_PERIOD`/`RSI_SEED_INTERVAL`
   pattern) - substituted `yfinance` for `fyers_download()` since this
   local machine has no Fyers token; both return the same OHLC shape
   for `^NSEI`/`^NSEBANK`.

3. Re-running it hit a SECOND, real problem - not a hang, a genuine
   performance bug in production code: `strategy/live_tick_harness.py`
   was recomputing `current_rsi()`, `_today_realized_pnl()`, and
   `_today_consecutive_losses()` FROM SCRATCH on every single tick
   (re-running `calculate_rsi()` over the candle window, and re-
   parsing every closed trade's "Exit Time" string with `strptime`
   for every trade, every tick) even though all three values are
   provably unchanged between a candle close / a trade close. Profiled
   with `cProfile` on a 30k-line subset: 1.18M `strptime` calls for
   14,899 ticks, dominated by `_today_realized_pnl`/`_today_
   consecutive_losses` alone. A single day/index backtest took **22.5
   minutes** - almost certainly the real cause of last night's/this
   morning's crash (a 20+ minute unresponsive process, not a script
   bug).

   Fixed with pure caching, zero logic change: `CandleAggregator.
   current_rsi()` now caches by `len(self.candles)` (the value can
   only change when a candle closes); `LiveTickRunner._today_realized_
   pnl()` caches by `(len(Closed Trades), today's date)`;
   `_today_consecutive_losses()` gained an optional `_cache` dict
   parameter (default `None` - the existing pure-function tests still
   call it with no cache, unchanged behavior), with both `LiveTickRunner`
   and `OIFootprintTickRunner` now owning a per-instance cache dict.
   All 3 caches are correctness-preserving (verified: single-day
   result identical before/after the fix; full suite - **621/621
   tests still pass**). Result: 22.5 minutes -> ~60 seconds per
   day/index run (~20x). This same inefficiency runs on the live VPS
   engine too, just masked there by realistic tick pacing and lower
   daily trade counts - worth keeping in mind given the VPS's own
   1vCPU/1GB budget and the recent Vultr CPU-abuse incident (different
   cause, same box). NOT YET COMMITTED - local change only this
   session, pending user confirmation before pushing to `main`.

Ran the corrected backtest across all 5 locally-available trading days
(21/25/26/27/28-Aug; 24-Aug's tick archive is not present on this
machine) x both indices, 10 runs total, combined PnL by buffer length:

- 0 min (baseline): -Rs 4,07,551
- 5 min: -Rs 4,71,202 (WORSE than baseline)
- **10 min: -Rs 3,36,888 (best)**
- 15 min: -Rs 3,39,139
- 20 min: -Rs 3,49,113

Findings: a 10-minute buffer is the best of the 5 values tested, ~17%
less total loss than no buffer - real, but far weaker than the
cooldown-after-close idea's ~65% reduction found on 28-Aug. A 5-minute
buffer is actively worse than no buffer at all - on several days
(25-Aug, 26-Aug) the first real trade didn't happen until after 09:20
anyway, so a 5-min buffer changed nothing there while cutting good
early trades on the days it did bind (21/27/28-Aug), a net negative.
Not monotonic (15/20-min are both slightly worse than 10-min) - 10-min
is the best candidate from this data, not a proven universal optimum,
same caveat as the cooldown backtest. Nothing deployed live - backtest
only, per this project's own data-driven-patience discipline.

See [[project_quote_pnl_and_whipsaw_decision]] memory for the running
note across all these backtests.

==================================================

MARKET-OPEN BUFFER BACKTEST RE-RUN WITH THE REAL N=2 daily_loss_lock
BREAKER ON - SUPERSEDES THE RESULT ABOVE. User's own catch: the first
run above used `make_st2_threshold_event_cfg` with its default
`daily_loss_lock=False` - NOT what any real book on the VPS actually
runs with (every live event-driven book has the N=2 breaker on, per
21/27-Aug's own incidents). Re-ran the identical 10 day/index sweep
with `daily_loss_lock=True, max_consecutive_losses=2` added to the cfg
(one-line change to `scratch_buffer_backtest_v2.py`, not committed -
still a throwaway script).

Combined PnL by buffer length, breaker ON:

- 0 min (baseline): -Rs 75,024
- 5 min: -Rs 50,059
- 10 min: -Rs 10,909
- **15 min: -Rs 3,387 (best - near break-even)**
- 20 min: -Rs 8,474

Two real differences from the breaker-OFF run: (1) every value's
MAGNITUDE dropped by roughly 5-10x (2-9 trades/day now instead of
100-1600+) - the breaker itself already caps most of the damage, so
total losses look far smaller across the board regardless of buffer;
(2) the OPTIMAL buffer shifted from 10-min (breaker off) to **15-min**
(breaker on), and unlike the breaker-off run, every buffer value now
beats baseline (the breaker-off run had 5-min actively worse than no
buffer - that inversion disappears once the real breaker is in the
loop). This run reflects what adding a buffer on top of the ALREADY-
DEPLOYED breaker would actually do, not a from-scratch hypothetical -
treat this as the real number, the breaker-OFF version above as a
useful but less faithful first pass. Still backtest-only, nothing
deployed.

==================================================

COOLDOWN-AFTER-CLOSE BACKTEST ALSO RE-RUN WITH THE REAL N=2 BREAKER ON
- LARGELY OVERTURNS 28-Aug's ORIGINAL "65% reduction" FINDING. User
asked which backtest finding was actually worth pursuing; recommended
re-testing the 300s cooldown-after-close idea (28-Aug's strongest
result) against the real breaker, same gap as the buffer backtest had.
28-Aug's original cooldown script no longer exists locally (never
committed) - rebuilt it fresh (`scratch_cooldown_backtest.py`, same
RSI-seeded LiveTickRunner-replay pattern, same "don't touch the real
decide_fn" rule) with `daily_loss_lock=True, max_consecutive_losses=2`
from the start.

Combined PnL by cooldown length, breaker ON (same 10 day/index runs):

- 0s (baseline): -Rs 75,024
- 30s: -Rs 82,527 (worse)
- 60s: -Rs 82,356 (worse)
- **120s: -Rs 67,075 (best, only ~11% better than baseline)**
- 300s: -Rs 1,08,957 (WORST - actively harmful)

28-Aug's original "300s cooldown, ~65% reduction" finding was measured
WITHOUT the breaker - cooldown was doing double duty there (both
preventing rapid whipsaw AND doing the damage-capping the breaker
already does in production). With the real breaker already capping
each day at 2 consecutive losses, cooldown's own added value shrinks
to a modest ~11% at 120s, and a long 300s cooldown actively HURTS
(occasionally causes the strategy to miss good recovery trades or
re-enter at a worse moment once the cooldown window finally clears).
Net conclusion: neither the buffer nor the cooldown idea, once tested
against the ACTUAL production config, is anywhere near as strong as
their breaker-off numbers suggested - 120s cooldown (~11%) is currently
the single best verified lever from either backtest. Still backtest-
only, nothing deployed. See [[project_quote_pnl_and_whipsaw_decision]]
memory for the running note.

==================================================

DEPLOYED THE PERF FIX LIVE, THEN FOUND AND FIXED A REAL CRON GAP IT
EXPOSED. User approved deploying today's `live_tick_harness.py` perf
fix to the VPS after confirming it was safe (Saturday, market closed,
no open positions on any of the 3 event-driven services - the 3 open
positions found on the VPS belong to a completely separate system, the
GitHub-Actions-driven swing strategies, which don't run on this VPS at
all). Ran `deploy/deploy.sh` as `turion` (not root, per the established
ownership-drift lesson) via `sudo -u turion bash -c`: git fast-forwarded
cleanly, dependencies installed, all 3 services restarted successfully.
(The script's own final `sudo systemctl status` step failed - turion's
sudoers NOPASSWD scope covers `restart`/`start` but not `status` - a
minor, pre-existing gap in deploy.sh itself, not a deploy failure; the
restarts had already succeeded by that point.)

All 3 services then showed "inactive" - investigated rather than
assuming a break: this is a real, pre-existing, deliberate feature
(added 22-Aug-2026 after an earlier real Saturday crash-loop incident)
- each entrypoint checks `now_ist.weekday() >= 5` at startup and exits
cleanly (exit 0, not a crash) on a weekend. Confirmed via `journalctl`:
"Saturday - NSE is closed on weekends, skipping this start attempt."
NOT caused by today's perf fix - this is the first restart since
Friday, so it's the first time this exact weekend-skip path has been
exercised outside of a crash scenario.

Found a real, previously-latent gap this exposed: `turion-event-driven`
already has 3 crontab lines (`30-55/5 2 * * 1-5` / `*/5 3 * * 1-5` /
`0-25/5 4 * * 1-5 sudo systemctl start turion-event-driven`, documented
in `deploy/turion-event-driven.service`, added 18-Aug-2026) that retry
`systemctl start` across the pre-market window every weekday, so it
reliably comes back up regardless of `deploy.sh`'s own restart firing.
`turion-tick-collector` and `turion-depth-collector` never got the
matching entries - and `deploy.sh` only restarts services when there is
a NEW commit to pull, which isn't guaranteed on a Monday morning (all
of this project's own automated GitHub Actions commits - best-trade
shortlist refresh, etc. - are weekday-scheduled, so nothing new lands
over a weekend). Net effect: without a fix, both collectors would have
stayed down all Monday with nothing to bring them back automatically.
Real trading itself was never at risk (`turion-event-driven` - the
actual trading engine - is the one already covered); this was a data-
archival gap only.

Fixed live: added the same 3-line pattern for both collectors to
`crontab -u turion` on the VPS (verified: `start` for both was already
in turion's NOPASSWD sudoers scope alongside `restart` - no sudoers
change needed). Documented the same fix in `deploy/turion-tick-
collector.service` and `deploy/turion-depth-collector.service` (mirroring
`turion-event-driven.service`'s own 18-Aug-2026 pattern) so a future
VPS reinstall reproduces this crontab, not just the live box having it.

==================================================

Status

🟢 Stable

Current Version

v0.0.69

Next Version

v0.0.69 (perf fix committed, pushed, and deployed live to the VPS this
session; the buffer backtest itself stays backtest-only, nothing shipped
from it)

--------------------------------------------------

Next Session

1. Verify Monday morning (31-Aug, next real trading day) that BOTH
   `turion-tick-collector` and `turion-depth-collector` actually come
   back up via today's new crontab entries (not just `turion-event-
   driven`, which already had this safety net) - this is the FIRST
   real trading-day test of that fix.

2. Both the 15-min market-open buffer (near break-even) and 120s
   cooldown-after-close (~11% better than baseline) are real but modest
   levers once tested against the ACTUAL production config (N=2 breaker
   on) - neither is close to their breaker-off numbers. Still just one
   dataset (5 days) either way, same "more real data before deciding"
   discipline as everything else on this project. Not deployed. Worth
   testing whether combining both (buffer + cooldown together) beats
   either alone, if the user wants to take this further.

3. PCR event-driven port, GEX-wall momentum-exhaustion, and the
   OI+Volume oi_footprint filter improvement all still blocked on OI
   archive data (only 2 partial days so far) - real backtest possible
   after 31-Aug. Volume-spike breakout (+Rs 2,123, 28-Aug) is the only
   profitable new strategy found so far but hasn't been re-tested with
   the real breaker either - same open question as the two above.

4. Carried over: `event_driven_runner.py`'s missing "reconnected"
   log line, and the Firebase `CLOSE-WAIT` socket-leak cleanup - both
   still open, low priority.

5. `data/ticks/ticks_240826.jsonl(.gz)` is missing on this local
   machine (present days: 21/25/26/27/28-Aug only) - if a full 6-day
   buffer/cooldown comparison is wanted, sync it down from the VPS
   first (`sync_ticks_from_vps.py`).

6. 31-Aug (Monday, next real trading day) is the real test of whether
   `data/oi/` keeps accumulating cleanly across a full trading day -
   only 2 partial days confirmed so far (28/29-Aug, the latter a
   closed-market day).

==================================================
