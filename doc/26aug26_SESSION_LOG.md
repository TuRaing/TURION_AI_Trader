# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260826-001

--------------------------------------------------

Date

26-Aug-2026

--------------------------------------------------

MORNING TOKEN CYCLE - ROUTINE, NOT A REPEAT OF 25-AUG'S INCIDENT.
User logged into Fyers at ~7:00 AM IST; the previous day's token had
expired overnight (same daily cycle as always). Checked ownership
FIRST this time (per 25-Aug's own lesson) - confirmed 0 root-owned
files, so this morning's restart worked cleanly on the first try:
verified a fresh token was available via Firebase, restarted all 3
services as the `turion` user (not root), confirmed clean startup
logs and zero errors. GitHub Actions' own `fyers_trigger.yml` login
dispatch also confirmed successful independently. Total time from
"user says token added" to "all 3 services confirmed healthy": a few
minutes, versus 25-Aug's ~2-hour undetected gap - the ownership
discipline from yesterday's incident held.

==================================================

VULTR CONTROL-PLANE MAINTENANCE NOTICE - user forwarded a real Vultr
account alert: scheduled control-plane maintenance 27-Aug-2026, 10:00
UTC (15:30 IST), ~10 minutes, affecting only the Vultr Console/API
(new instance deploys, management actions) - NOT already-running
instances, so the TURION VPS and its 3 services are not expected to
be affected. A one-time local reminder was scheduled for 27-Aug 15:30
IST via the scheduled-tasks tool (not a cloud routine, since this
needs no VPS/SSH access - just a heads-up).

==================================================

REAL LIVE INCIDENT #3 (SECOND DAY IN A ROW, DIFFERENT ROOT CAUSE) -
ALL 3 SERVICES' WEBSOCKET ABANDONED RIGHT AT MARKET OPEN, ~9 MINUTES
UNDETECTED. User asked for a full check ("trades, market, TBT, data
collector, depth") right after market open - found all 3 services
"active" (0 restarts) but the tick/depth archives were stale by 9-10
minutes despite it being live trading time. journalctl showed the
real cause: Fyers' own WebSocket front end (Cloudflare-fronted)
returned repeated 502 Bad Gateway errors at 09:13-09:13:36 IST on
ALL 3 services simultaneously; fyers_apiv3's own reconnect logic
exhausted its 5 attempts and printed "Max reconnect attempts reached.
Connection abandoned." - the process stays alive with NO further
retry logic and NO exit code, so systemd's Restart=on-failure never
fires. Manually restarted all 3 (again as `turion`, not root) -
confirmed immediate recovery, fresh data flowing within seconds,
zero errors since.

Root cause is now understood as a real architectural gap this
project's OnFailure=/Restart=on-failure safety net does not cover -
a "silently abandoned but still-alive" connection looks identical to
"working fine" from systemd's point of view.

FIX (commit ab1a745a2, "Add a data-staleness watchdog to all 3 VPS
services") - strategy/data_watchdog.py: should_restart_for_stale_feed()
(pure, 8 new tests) decides whether `timeout_minutes` (default 5) have
passed with zero WebSocket messages DURING MARKET HOURS (09:15-15:30
IST weekdays only - deliberately silent outside that window, where a
quiet socket is normal); watchdog_loop() runs this check every 60s in
a daemon thread and calls os._exit(1) the moment it fires - a
DELIBERATE process exit, chosen specifically so the already-proven
Restart=on-failure + OnFailure=turion-alert@%N.service machinery
(every other real crash this project has hit already goes through
this) picks the connection back up and notifies the user, rather than
building a second, parallel restart/alert mechanism. Wired into all 3
entrypoints (event_driven_runner.py's main(), run_tick_collector.py,
run_depth_collector.py) - each tracks its own last-message timestamp,
updated on EVERY message (before any early-return), seeded at connect
time so a socket that never receives even one message is still
caught. Deployed as `turion`, verified clean (0 errors, 610/610 tests
passing at commit time).

==================================================

TBT (TICK-BY-TICK) FEED - FULLY VERIFIED LIVE, CORRECTS AN EARLIER
WRONG CONCLUSION. Yesterday's off-hours test (connected but received
zero data in 30s) was wrongly read as "probably no TBT access/paid
plan" - re-tested properly during live market hours and found the
REAL bug: the working example needs a two-step handshake (type:1
subscribe THEN a separate type:2 "resume channel" message) - the
earlier test only sent the subscribe. Fixed and retested: 8 real
binary Protobuf messages received in ~48s for a live NIFTY ATM option,
confirming real TBT access, no paid-plan blocker, and NFO options
(not just futures) are covered.

Decoded the real message using Fyers' own published msg.proto schema
(cloned from github.com/marketcalls/fyers-websockets) - definitively
answered the original question this whole investigation was for:
TBT's own `feed_time`/`send_time` fields are ALSO whole-second Unix
epochs, identical precision to the standard SymbolUpdate feed's
exch_feed_time. TBT does NOT solve the millisecond-timestamp problem -
that limitation is Fyers-wide, not specific to the feed this project
already uses. This closes the TBT/latency-precision investigation -
no further action planned; the only remaining potential TBT benefit
(deeper 50-level depth, possibly lower raw transport latency) was not
pursued further this session.

==================================================

LATENCY VS SPREAD SLIPPAGE - ISOLATED WITH REAL DATA, LATENCY IS A
MINOR CONTRIBUTOR. User's own follow-up question after yesterday's
latency finding: is our measured recorded-vs-realistic PnL slippage
actually caused by the ~0.7-1.2s exchange-to-VPS latency, or mostly
something else? Built analyze_latency_slippage.py (commit 70d77ae94) -
rather than reconstructing an unverifiable "zero-latency" execution
price, measures directly from today's real tick archive how much an
ATM option's own LTP typically moves over a window equal to today's
own measured median latency (never hardcoded - derived fresh each
run via tick_collector.py's existing tick_latency_ms()). 5 new tests
for the pure price_deltas_over_window() function.

Real result (26-Aug, 0.912s window): NIFTY ATM CE/PE move a median of
Rs 0.20-0.35/share (Rs 15-26/lot); BANKNIFTY ATM CE/PE move Rs
0.85-1.45/share (Rs 64-109/lot). Compared against the already-known
spread-driven slippage magnitude (Rs 300-3,000+ per trade) - latency's
real contribution is 10-30x smaller. Conclusion: today's (and by
extension, most days') observed slippage is overwhelmingly a
spread/depth-walk cost, not a latency cost - reinforces that porting
the remaining LTP-based books (oi_footprint, st2_threshold,
simple_st1_threshold) to quote-based decide_fn remains the real
lever, not chasing latency further.

==================================================

TODAY'S REAL SLIPPAGE CHECK ON A PROFITABLE DAY - user's own explicit
worry ("इतका slippage असेल तर सगळा profit तोच खाईल" - won't slippage
eat the whole profit?). Ran analyze_realtime_depth_slippage.py against
today's real trades (16 matched, all from the morning's 7 profitable
"lock" books + 2 plain RSI books): TOTAL recorded Rs 29,410.71 vs
realistic Rs 26,071.20 - 11.4% overstatement. Broken out by category
(never trust a blended headline number, per this project's own
established discipline): the quote-based lock books' PnL is
essentially exact (Rs 5,410.81 recorded vs Rs 5,417.36 realistic -
realistic was actually SLIGHTLY better) - confirming the quote-fix
genuinely works; the plain LTP-based books (st2_threshold, simple_
st1_threshold) showed a real 17-24% overstatement on their winning
trades specifically. Most of today's Rs 33,340.81 VPS profit came
from the quote-based books, so the bulk of today's gain is real, not
an LTP artifact - only the smaller plain-book portion is inflated.

==================================================

FULL VPS + GITHUB STATUS SNAPSHOTS (multiple times today, on request) -
VPS: all 14 event-driven books, today's PnL, which are locked/
breaker-stopped vs still live. By ~09:50 IST, 10 of 14 books had
already stopped for the day (7 hit their profit lock on the first
trade, 2 hit the N=2 consecutive-loss breaker after a win-then-2-
losses sequence) - only the 4 oi_footprint books (2 old + 2 new
quote-based) remained live, waiting on an OI-buildup signal that
hadn't fired yet. Checked oi_footprint's own historical first-trade-
of-the-day timing (24/25-Aug, plus 21-Aug for BANKNIFTY) to set
realistic expectations - NIFTY typically fires within ~20 min of
open, BANKNIFTY is highly variable (once not until 12:18 IST).

GitHub Actions (48 older polling-engine books, separate from the VPS)
also checked, both raw today's-PnL and matched-pairs comparison
against the VPS's own same-signal books (st2_threshold, simple_st1_
threshold, oi_footprint x2) - the VPS versions consistently show much
smaller losses/larger relative gains than their GitHub counterparts
on whipsaw-prone days, directly attributable to the consecutive-loss
breaker the GitHub polling engine has never had ported to it.

Today's combined snapshot: VPS +Rs 33,340.81, GitHub -Rs 46,572.36,
net -Rs 13,231.55 (still shifting - not a final daily figure, GitHub's
oi_footprint books alone were among the largest single-day losers on
GitHub, oi_hybrid_sl_atr_banknifty -Rs 21,458.94).

==================================================

Status

🟢 Stable

Current Version

v0.0.63

Next Version

v0.0.64

--------------------------------------------------

Next Session

1. User's own explicit decision for today: watch the quote-fix vs
   plain-LTP slippage gap for a full week (not just today's single
   profitable-day snapshot) before backtesting further changes or
   deciding whether to port oi_footprint/st2_threshold/simple_st1_
   threshold fully to quote-based decide_fn. Do not act on today's
   11.4%/17-24% figures alone.

2. Watch the new data-staleness watchdog (strategy/data_watchdog.py)
   over the next few real trading days - today's incident happened
   AFTER the watchdog code existed conceptually but BEFORE it was
   built/deployed (built and deployed reactively, same day, right
   after this exact incident) - it has not yet been proven against a
   real second occurrence.

3. oi_footprint_quote (2 new books, live since 24-Aug) - still very
   little real trade data (a handful of trades total) - too early to
   draw conclusions.

4. Carried over from 25-Aug: TBT feed investigation is now CLOSED (see
   above - confirmed working, confirmed it doesn't solve the timestamp
   precision problem) - no further TBT work planned unless the user
   wants to explore its deeper depth levels specifically.

5. Crypto (Deribit) paper-trading remains in a SEPARATE session/chat
   - explicitly not touched here today, per the user's own instruction.

6. Still open from 24-Aug: turion-tick-collector lacks turion-event-
   driven's auto-retry cron lines; sync_ticks_from_vps.py off-machine
   backup exercise never run; end-Sep-2026 statistical-tools checkpoint
   still ~4-5 weeks out.

==================================================
