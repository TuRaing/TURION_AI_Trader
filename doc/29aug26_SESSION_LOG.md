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

Status

🟢 Stable

Current Version

v0.0.68

Next Version

v0.0.68 (no code shipped live this session - the live_tick_harness.py
perf fix is made and fully tested locally, but not yet committed/
pushed/deployed; the buffer backtest itself stays backtest-only)

--------------------------------------------------

Next Session

1. Decide whether to commit + push the `live_tick_harness.py`
   perf-caching fix (RSI/today_realized_pnl/today_consecutive_losses)
   to `main` - safe and fully tested (621/621), but user has not yet
   been asked to confirm the commit itself.

2. 10-minute market-open buffer is the best candidate found - still
   just one dataset (5 days), same "more real data before deciding"
   discipline as everything else on this project. Not deployed.

3. Carried over from 28-Aug, still not run: the cooldown-after-close
   gate (~65% reduction candidate) and the 5 new-strategy backtests
   (order-book imbalance, VWAP, volume-spike breakout, PCR event-
   driven port, ORB) + the OI+Volume oi_footprint filter improvement -
   timing was left flexible by the user ("sandyakali kiva udya").

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
