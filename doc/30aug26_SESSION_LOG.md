# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260830-001

--------------------------------------------------

Date

30-Aug-2026

--------------------------------------------------

OI ARCHIVE CHECKED - ZERO USABLE DATA YET, WORSE THAN "JUST 2 PARTIAL
DAYS". Following up on 29-Aug's plan to backtest OI-based strategies
(PCR event-driven port, GEX-wall momentum-exhaustion, the oi_footprint
OI+Volume filter) once enough real OI archive data exists - user asked
to do a quick, low-effort check first before investing time in a full
backtest script. Synced `data/oi/oi_280826.jsonl` (82 records) and
`data/oi/oi_290826.jsonl` (144 records) down from the VPS (read-only
scp pull, no compute on the VPS) and inspected them directly.

Real finding: EVERY record in both files carries the identical spot/
strike/CE-OI/PE-OI values - not just similar, byte-for-byte the same
number repeated every ~5 minutes for hours. Root cause (confirmed, not
a bug): `oi_280826.jsonl`'s records run 20:32-23:58 IST (AFTER 28-Aug's
15:30 market close); `oi_290826.jsonl`'s run 00:03-05:58 IST (BEFORE
that day's 09:15 market open, and 29-Aug was a Saturday besides). The
option chain's OI genuinely does not change outside market hours (no
one is trading), so the collector correctly returns the same last-known
value on every poll - this is expected API behavior, not a collector
defect.

Consequence: `strategy/oi_collector.py` (deployed 28-Aug) has not yet
recorded a single real intraday OI movement, because it has not yet
been running during actual market hours (09:15-15:30 IST) on any real
trading day. 31-Aug (Monday) is the FIRST day this gets a real test.
All 3 OI-dependent backtest ideas remain genuinely blocked until then -
this is a stronger statement than 29-Aug's "only 2 partial days," which
undersold how little signal those 2 days actually contain.

==================================================

Status

🟢 Stable

Current Version

v0.0.69

Next Version

v0.0.69 (pure investigation - no code/config change this session)

--------------------------------------------------

Next Session

1. 31-Aug (Monday) is the real test on two fronts now converging on the
   same date: (a) whether `turion-tick-collector`/`turion-depth-
   collector` come back up via the new crontab safety-net (29-Aug), and
   (b) whether `data/oi/` finally captures genuine intraday OI movement
   for the first time - both should be checked at the start of the next
   session.

2. Once 31-Aug's OI data exists, re-attempt the PCR event-driven port /
   GEX-wall momentum-exhaustion / oi_footprint OI+Volume filter
   backtests - all still genuinely blocked until then.

3. Carried over from 29-Aug: the combined 15-min buffer + 120s cooldown
   result (+Rs 10,027 net profit, first positive total from any variant
   tested) needs re-verification on more days before any deploy
   decision - explicit overfitting caveat noted (4 variants compared on
   only 5 days). 24-Aug's tick archive is still missing locally if a
   fuller comparison is wanted.

==================================================
