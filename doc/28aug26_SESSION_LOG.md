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

Status

🟢 Stable

Current Version

v0.0.67

Next Version

v0.0.68

--------------------------------------------------

Next Session

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
