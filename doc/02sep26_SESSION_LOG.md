# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260902-001

--------------------------------------------------

Date

02-Sep-2026

--------------------------------------------------

FIRST REAL FULL-DAY TEST OF THE 10-TICK DEBOUNCE ON ALL 10 BOOKS - AND
IT WORKED, CONFIRMED TWO WAYS. 01-Sep's debounce expansion landed too
late in the day (~09:56 IST, after the market-open whipsaw had already
happened and locked most books) to be a fair test. Today the debounce
was live on all 10 RSI-momentum books BEFORE market open for the first
time.

Morning routine repeated from 01-Sep: services had again been running
unbroken since the previous evening's deploy (01-Sep 16:28 IST),
spanning the calendar-day boundary, token stale again this morning -
the new `token_watchdog_loop` (deployed 01-Sep evening) hasn't had a
chance to prove itself yet, since it deliberately only acts DURING
market hours (09:15-15:30 IST), not before - so this was still a
manual restart at 07:15 IST (well before market open, same pattern as
01-Sep), not yet a live test of the new watchdog itself. Verified no
open positions first, confirmed clean reconnect ("Got today's
access_token via Firebase..." / "Successfully connected...").

Real result, checked right at market open (09:16 IST) via a scheduled
one-shot check: ALL 8 "_lock"/"_lock_quoteX%" books took exactly ONE
trade each and are still RUNNING (not breaker-stopped) - EVERY one
profitable (+Rs 3,148 to +Rs 5,373). `simple_st1_threshold`/`st2_
threshold` (plain, no daily_profit_lock) took more trades (9 each) and
did eventually hit the N=2 breaker, but were STILL net positive
(+Rs 8,970/+Rs 10,625). Combined total across all 14 books: **+Rs
58,954 - the first genuinely profitable market-open snapshot of the
week**, a dramatic reversal from 31-Aug's -Rs 2,70,005 and 01-Aug's
-Rs 1,69,938 for the same early-morning window. Zero same-second
whipsaw entries anywhere today - the exact pattern that caused both of
those earlier losses.

User's own follow-up, the right question to ask rather than just
trusting the good number: what would TODAY have looked like WITHOUT
the debounce? Copied today's own in-progress tick archive down from the
VPS (`data/ticks/ticks_020926.jsonl`, ~14 min of real market-open data)
and ran `scratch_stale_print_backtest.py`'s existing 0-vs-10-tick
sweep against it directly - not a different day's data, THE SAME
morning's real ticks:

- 0 ticks (baseline, no debounce): NIFTY -Rs 43,068, BankNifty
  -Rs 14,023 - **combined -Rs 57,091**
- 10 ticks (what's actually deployed): NIFTY -Rs 6,998, BankNifty
  -Rs 4,885 - **combined -Rs 11,882**

**~79% less loss, directly attributable to the debounce, on the exact
same real morning.** This confirms two things at once: (1) the same
market-open stale-print whipsaw pattern happened AGAIN today - not a
one-off from 31-Aug, a real recurring market-open phenomenon - and (2)
the debounce genuinely prevented most of the damage, not luck. This is
the strongest, most direct evidence yet (a same-day counterfactual on
real live data, not a different historical day) that the fix is doing
exactly what it was built to do.

==================================================

oi_footprint's OWN WHIPSAW - REAL INCIDENT, DIFFERENT ROOT CAUSE FROM
THIS WEEK'S RSI-momentum FIXES, AND TWO PROPOSED FIXES BOTH FALSIFIED.
Same day, a different pair of books lost money: `oi_footprint_nifty`/
`oi_footprint_quote_nifty` (-Rs 3,803/-Rs 4,010 today). Pulled the real
trade JSON rather than assuming it was the same stale-print bug -
it wasn't: premium declined smoothly (Rs 245.0 -> 240.3 -> 236.0, no
single-tick jump), spot stayed completely flat, and BOTH trades were
PE, back-to-back, each stopped at the ~2% hybrid SL cap. The OI-
buildup signal itself kept pointing the same direction right after a
loss - a different failure mode from a stale first tick, and one none
of this week's gates (debounce/cooldown/S-R, all built for
`_rsi_momentum_decide`) touch, since `oi_footprint` runs a completely
separate decide_fn (`_oi_footprint_decide`).

Built `scratch_oi_footprint_cooldown_backtest.py` - a NEW backtest
harness (not a reuse of this week's RSI-momentum scripts), since
`OIFootprintTickRunner` needs BOTH real tick data AND real OI snapshots
merged into one chronological replay, unlike the tick-only RSI runner.
Copied the only 3 real, non-frozen OI archive days available
(31-Aug/01-Sep/02-Sep - see 30-Aug's frozen-data finding for why
earlier days don't count) plus their matching tick files down from the
VPS for this.

Tested 2 ideas, both real backtests against all 3 days x 2 indices (6
runs), both came back negative:

1. Plain cooldown-after-close (same shape as 29-Aug's RSI-momentum
   idea): 0s +Rs 37,103; 60s +Rs 34,270 (worse); **120s +Rs 38,307
   (best, only ~3% better)**; 300s +Rs 32,911 (worse). Nowhere near the
   RSI-momentum debounce's ~79% same-day improvement - a plain time
   delay doesn't fix "the signal is still pointing the same way,"
   it just postpones the same bad trade.

2. Block a new entry in the SAME direction as the last LOSING trade
   until the OI signal genuinely flips (a more targeted idea than a
   blind time delay): **+Rs 4,723 total - much WORSE than baseline**,
   almost entirely from one real outlier (31-Aug NIFTY: -Rs 29,549 vs
   baseline's -Rs 4,464, ~6.6x worse) - the gate blocked a same-
   direction entry that would have been genuinely profitable that day,
   proving "the signal repeating itself" isn't reliably wrong the way
   "a stale first tick" reliably is. Falsified, not just weak.

Net conclusion: unlike the RSI-momentum family, `oi_footprint`'s real
whipsaw problem does not yet have a working fix - both ideas tried
today made things worse or barely moved the needle. Needs a genuinely
different approach (not built or tested today) or more real data (only
3 real OI days exist total) before trying again.

==================================================

Status

🟢 Stable

Current Version

v0.0.71

Next Version

v0.0.71 (no new code shipped today - pure verification of 01-Sep's
debounce expansion and the token watchdog still pending its first real
market-hours trigger)

--------------------------------------------------

Next Session

1. The new `token_watchdog_loop` (01-Sep) still hasn't been tested
   live - both mornings since it shipped, the stale-token state existed
   BEFORE market open (where it deliberately doesn't act) and was
   manually fixed before 09:15 IST each time. Watch for a day where the
   token goes stale mid-session, during market hours, to see the
   watchdog actually fire on its own.

2. Continue watching `simple_st1_threshold`/`st2_threshold` (the 2
   books without `daily_profit_lock`) - they still take more trades
   (9 today) before the N=2 breaker catches them, unlike their "_lock"
   siblings which stop after 1. Worth a look at whether adding
   `daily_profit_lock` to these two (already proven safe elsewhere)
   would lock in today's early gains rather than let them keep trading.

3. Local tick archive now has 8 real days (21/24/25/26/27/28/31-Aug +
   today's in-progress 02-Sep) - getting closer to a real validation
   sample size for the debounce parameter itself (still only backtested
   against the original 5-day sample when "10" was chosen).

4. `oi_footprint`'s real same-direction-after-loss whipsaw is still
   unsolved - both a plain cooldown and a signal-must-flip gate were
   tried and falsified today (see above). Only 3 real OI days exist to
   test against so far; needs either more real days or a genuinely
   different idea before trying again - not a quick follow-up.

==================================================
