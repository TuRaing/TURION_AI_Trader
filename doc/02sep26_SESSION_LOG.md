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

==================================================
