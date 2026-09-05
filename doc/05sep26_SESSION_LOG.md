# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260905-001

--------------------------------------------------

Date

05-Sep-2026 (Saturday, market closed - pure analysis/data session,
no live trading)

--------------------------------------------------

CATCHING UP ON 04-SEP'S INTERRUPTED WORK - THE SCHEDULED 15:30 IST
BUFFER TEST NEVER FIRED. The previous session had scheduled a session-
local one-shot cron (via CronCreate) for 15:30 IST on 04-Sep to run
the market-open-buffer + cooldown combo backtest once the full trading
day's data was available. That session's process ended before 15:30
(session-local cron jobs die with the session, they are not written
to disk) - the job never ran. Two other backtest re-runs from the
previous session (the RSI-momentum cooldown sweep and the SL-grace-
period sweep, both being re-run after fixing a harness bug - see
below) were also left incomplete, interrupted mid-sweep for the same
reason. This session resumed and finished all three.

==================================================

RECAP: THE SYMBOL-SWITCH HARNESS BUG (found and fixed 04-Sep, carried
over here since it invalidates several of this week's backtest
numbers). Every scratch backtest replay script this week (scratch_
cooldown_backtest.py, scratch_buffer_backtest_v2.py, scratch_combined_
backtest.py, scratch_rsi_cooldown_backtest.py, scratch_sl_grace_
backtest.py, scratch_oi_footprint_cooldown_backtest.py) shared a bug:
the replay loop REASSIGNED runner.ce_symbol/pe_symbol whenever a NEW
option-strike symbol appeared later in the tick stream (ATM drifting
intraday - the tick archive shows 3-7 distinct CE/PE symbols per index
per real trading day, confirmed via a full scan). This silently
redirected an OPEN position's exit price to a DIFFERENT option
contract mid-trade. Confirmed real instance: 01-Sep 09:15:13-14, a
position on NIFTY strike 24200 (entry Rs 7.65) "exited" reading strike
24050's Rs 42.0 tick instead - a fake 449% jump that inflated one
backtest cell to +Rs 431,623 before the fix was found and applied.

Real production (`strategy/event_driven_runner.py`) does NOT have this
bug - each runner's ce_symbol/pe_symbol are fixed once at startup
(`_atm_for()`) and `router.register()` only ever routes that exact
symbol to that runner; a documented, separate, already-accepted
limitation (ATM not re-derived intraday) is the only real-world
analogue, not this bug. Fixed in all 5 scratch scripts + `scratch_
combined_backtest.py` (04-Sep for the first 5, 05-Sep for `scratch_
combined_backtest.py` when it was needed for today's buffer test) by
replacing the reassignment with a bare `continue` (skip ticks for any
symbol other than the runner's own) - matching production's fixed-
symbols-per-lifetime behavior exactly. A separate, read-only bad-tick
scanner (`scratch_bad_tick_scan.py`) built to look for OTHER similarly
corrupt prints found none of comparable severity - the 90 sub-3-second
jumps it did flag across the archive are all on near-zero-premium
(Rs 0.05-0.30) deep-OTM/near-expiry options right before square-off,
which is normal tick-size noise on a thin book, not bad data.

==================================================

THREE BACKTESTS RE-RUN/RUN FRESH WITH THE FIXED HARNESS, ALL 44
COMBINATIONS EACH (11 real tick-archive days x 2 indices x 2 RSI-
momentum book families: st2_threshold, simple_st1_threshold) -
completed today after resuming from where 04-Sep's session left off.

1. COOLDOWN-AFTER-CLOSE (RSI-momentum family) - conclusion UNCHANGED
   by the fix: baseline (no cooldown) is still the best variant.

       0s (baseline)   -Rs 9,798.03   <- best
       120s            -Rs 49,581.71
       30s             -Rs 56,399.78
       15s             -Rs 62,817.07
       60s             -Rs 69,715.68
       300s            -Rs 76,315.35  <- worst

   No cooldown duration helps. Same conclusion as before the fix (the
   specific numbers moved, the ranking/verdict did not) - matches
   oi_footprint's own 03-Sep finding for the same idea.

2. SL-GRACE-PERIOD (suppress a Stop-Loss exit for the first N seconds
   after entry - the genuinely different idea from comparing the
   polling vs event-driven engines, see 04-Sep's log) - MIXED, not
   proven:

       30s grace   +Rs 18,645.50   <- best raw total
       60s grace   +Rs 11,662.60
       5s grace    +Rs 10,328.24
       15s grace   +Rs  9,962.67
       0s baseline -Rs  9,798.03
       10s grace   -Rs  5,770.43

   30s grace's raw total looks like a genuine win, but its top-2
   contributing combos (both 21-Aug, NIFTY, st2_threshold and simple_
   st1_threshold: +Rs 15,747 and +Rs 14,877) sum to 164.2% of the total
   - remove just those 2 and the total flips to -Rs 11,978.65, WORSE
   than baseline. Same outlier-fragility this project has flagged
   repeatedly this week. The one genuinely encouraging sign: 30s
   grace is profitable on 19/44 combos (43%) vs baseline's 11/44
   (25%) - a real, broad-based improvement in HIT RATE, not just a
   lucky sum. Verdict: promising enough not to discard, not proven
   enough to ship. Needs either more real data or a design that
   isolates the win-rate improvement from the single-day PnL swing
   before it's trustworthy.

3. MARKET-OPEN BUFFER (15-min, skip entries until 09:30 IST) +
   COOLDOWN (120s) COMBINED - the test originally scheduled for 04-Sep
   15:30 IST, run today instead. RESULT REVERSES 29-Aug's original
   (pre-fix, now known-buggy) finding entirely:

       0s/0min baseline         -Rs  9,798.03   <- best
       120s cooldown only       -Rs 49,581.71
       15min buffer only        -Rs 59,053.52
       15min buffer + 120s      -Rs 92,648.96   <- WORST of all 4

   29-Aug's original combined-backtest run (pre-fix) had reported
   buffer+cooldown as the ONLY profitable variant of the week (+Rs
   10,027 vs baseline -Rs 75,024) - that result does not survive the
   harness fix at all; it flips to being the single worst option
   tested. This was very likely the same symbol-switch contamination
   as the 01-Sep +Rs 431,623 outlier, just never caught at the time.
   The market-open buffer, alone or combined, is not a fix - closes
   out this idea definitively rather than leaving it as an open lead.

NET CONCLUSION ACROSS ALL THREE (RSI-momentum family): no cooldown
duration, no market-open buffer, and no combination of the two,
reliably beats doing nothing. The ONLY idea from this whole week's
testing (across both oi_footprint and RSI-momentum, cooldown/buffer/
direction-flip/consistent-signal/SL-grace) that shows a real, non-
outlier-driven signal is the SL-grace-period's higher hit-rate - and
even that is not yet proven enough to deploy. The RSI-momentum debounce
fix (31-Aug, already live) remains the only genuinely validated win
this project has found for either whipsaw problem, since it is the
only one confirmed via a real live-trading day, not backtest alone.

==================================================

VPS DATA SYNC COMPLETED - the depth (order-book) archive gap flagged
04-Sep (3 of 11 real days missing after a mid-transfer disk-full
stop) is now fully closed: all 10 real trading days' depth files
(24,25,26,27,28,31-Aug + 01,02,03,04-Sep, ~520MB total) synced cleanly
from the VPS with disk space checked before and monitored during the
transfer (local D: was at 3.3GB free beforehand, 2.7GB after - tight
but sufficient, no repeat of 04-Sep's mid-transfer failure). Local
`data/depth/` now matches the VPS byte-for-byte across all 10 files.
Nothing deleted from the VPS.

==================================================

Status

🟢 Stable

Current Version

v0.0.71 (unchanged - backtest/data-only session, no app or VPS config
changes)

--------------------------------------------------

Next Session

1. Both known whipsaw problems (oi_footprint's same-direction-after-
   loss, RSI-momentum's rapid-re-entry/fast-open-stop-out) remain
   unsolved after exhaustive testing this week - cooldown, direction-
   flip, signal-consistency, trailing SL, and market-open buffer have
   ALL been ruled out with reasonable confidence now (buffer and
   cooldown re-verified on a corrected harness). SL-grace-period is
   the one open, unproven lead (better hit-rate, fragile raw PnL) -
   worth more real data before the next decision, not another gate
   variant.

2. Re-verify oi_footprint's own 03-Sep 8-variant gate sweep against
   the fixed harness too (scratch_oi_footprint_cooldown_backtest.py
   was fixed 04-Sep but never re-run) - lower priority than the
   RSI-momentum work since oi_footprint's conclusion was already "no
   reliable fix found," matching the fixed-harness RSI-momentum result,
   but the specific numbers/ranking should be treated as unverified
   until re-run.

3. `data/depth/` is now fully synced and unused - still no backtest
   consumes it. Worth deciding whether it's worth building a depth/
   spread-based analysis now that the data exists, or whether that's
   lower priority than the still-open whipsaw problem.

4. Local disk (D:) is still tight (2.7GB free of 139GB) even after
   05-Sep's mobile_app/build + duplicate-exe cleanup (~1GB freed
   04-Sep) - the depth sync used up most of that headroom again. Will
   need another look if more large data accumulates.

==================================================
