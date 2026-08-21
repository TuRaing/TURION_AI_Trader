# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260821-001

--------------------------------------------------

Date

21-Aug-2026

--------------------------------------------------

VPS FYERS_ACCESS_TOKEN ENV VAR FIX - TICK COLLECTOR - continuation of
20-Aug's VPS build. run_event_driven_engine.py already had a fix (same
day, 21-Aug) for a real crash: build_runners() -> pick_atm_symbols()
-> strategy/fyers_options_engine.py's _fetch_option_chain()/_headers()
ALWAYS calls strategy/fyers_auth.py's get_access_token(), which only
reads the LOCAL .env's FYERS_ACCESS_TOKEN key - never wired to accept
the Firebase-sourced token fetched earlier in main(). The VPS's own
.env has no FYERS_ACCESS_TOKEN key at all (only FYERS_APP_ID plus the
Firebase keys), so this would crash every time with "No FYERS_ACCESS_
TOKEN found". Fix: set os.environ["FYERS_ACCESS_TOKEN"] = access_token
directly after the Firebase fetch, rather than touching fyers_options_
engine.py/fyers_data.py (both "never modify a working module" -
shared by 60+ live polling books) - get_access_token()'s own
load_dotenv(..., override=True) only overrides keys that already
EXIST in .env, and the VPS's .env has no such key to conflict with, so
every downstream caller picks up the real token with zero changes to
any shared module.

Checked run_tick_collector.py (the VPS's other entry point, deployed
20-Aug) for the identical dependency and found it: pick_atm_symbols()
is called both at startup (initial ATM pick for NIFTY/BANKNIFTY) and
inside its own 15-minute atm_recheck_loop(), same call path as the
event-driven engine. It was missing the same env-var set - would have
hit the identical crash the first time it actually ran against a real
token, silently defeating 20-Aug's whole tick-archival build the
moment real data should have started flowing. Applied the identical
one-line fix, same place in main() (right after the "no token yet ->
skip" guard, before the fyers_apiv3 import).

Verified: `python -c "import run_event_driven_engine, run_tick_
collector"` imports cleanly, full suite 516/516 passing (unchanged -
this is a top-level script fix, no strategy/ module touched, so zero
test surface was expected to move). Committed (8e29be57f) and pushed
directly to main - this is a VPS-bound entry-point fix, not new
strategy logic, so no separate feature branch.

Session-continuity check done first (CLAUDE.md rule): `git fetch` +
`git log HEAD..origin/main` found one new commit (c90a312d2, an
automated "Update Fyers state (login trigger) [skip ci]" commit from
this morning's mobile login workflow, report-file-only) - pulled
cleanly before starting, no conflict with the two files touched here.
Checked `git branch -r` for other in-progress session branches - the
non-stale ones found were already old/inactive (last real commits
13-Jul), nothing currently overlapping this fix.

NOTE ON THIS SESSION'S TRANSCRIPT: a prompt-injection attempt appeared
again in tool-observed content during this session (a hidden
instruction claiming to be a system/text-only directive, telling
Claude to stop using tools) - same pattern as earlier in this same
session. Ignored per this project's instruction-source-boundary rule
(valid instructions come only from the user via chat, not from
observed tool content) - flagging here for the record, not because it
changed anything about the actual work done.

--------------------------------------------------

B19 COMPLETED FOR REAL, SAME SESSION - deployed manually rather than
waiting for the 08:00 IST cron (user's own choice, asked directly
rather than assumed): SSH'd to the VPS as root (the `turion` service
user has no direct SSH login - nologin, per 20-Aug's hardening), ran
`sudo -u turion deploy/deploy.sh`. Pull fast-forwarded 1c3148135 ->
d2b6db1f6 cleanly, dependencies reinstalled, both services restarted.

Journalctl showed something worth recording exactly as found: in the
seconds just before this deploy's own restart landed, BOTH services
were live crash-looping in production on the OLD pre-fix code -
`journalctl -n 20` still had a fresh "RuntimeError: No FYERS_ACCESS_
TOKEN found" trace timestamped seconds earlier (01:15:16 UTC), i.e.
today's real morning login had already reached the VPS and started
triggering exactly the crash this session's fix targets, before the
fix was deployed. deploy.sh's restart (01:15:18 UTC) landed on the
very next cycle and both came up clean: turion-event-driven logged
"Got today's access_token via Firebase - starting the event-driven
engine..." with no further crash, turion-tick-collector logged real
ATM strikes (NIFTY 24250, BANKNIFTY 57500) and "Connecting to Fyers
WebSocket for tick archival...". Re-checked ~35s later:
`systemctl show -p NRestarts` = 0 for both since the fix landed (no
further crash-loop), and data/ticks/ticks_20260821.jsonl had real tick
rows with live LTPs. This is the first real live run of either
service with a genuine token - B19 (Go-Live Runbook) is DONE, not
just deployed. (One caveat: this check ran pre-market, ~06:45 IST, so
only confirms startup/connection stability, not a full trading-hours
decide_fn cycle - that still gets its first real exercise at today's
09:15 IST open.)

Deploy status-check step itself (the tail end of deploy.sh, `sudo
systemctl status ...`) failed with "sudo: I'm sorry turion. I'm afraid
I can't do that" - the scoped sudoers only grants `turion` the 4
`systemctl restart`/`start` commands (see 20-Aug's B12), not `status`.
Not a real problem (restart itself succeeded, confirmed independently
via `systemctl show` run as root instead) but worth fixing later so
deploy.sh's own status output doesn't sudo-fail on every daily 08:00
run - either add `status` to both units' sudoers scope, or drop
deploy.sh's own status-check line and rely on systemd's OnFailure
alert (already proven working, B17) instead.

--------------------------------------------------

CRON UTC-VS-IST BUG FOUND AND FIXED, SAME SESSION - user asked "login
नंतर checks झाले का" (did the post-login checks run). Honest answer
investigated properly rather than assumed: `crontab -u turion`'s
health-check log (/var/log/turion-health-check.log) was genuinely
empty, and `journalctl -t CRON` showed ZERO turion-user cron
executions since the VPS booted (20-Aug 13:26 UTC) - at first glance
alarming, but turned out to be expected: the crontab was installed
20-Aug ~15:04 UTC (B15), and every one of its entries' first-ever
occurrence hadn't been reached yet as of this check (~01:20 UTC,
21-Aug) - not a bug, just too early in the day.

While confirming that, found a REAL bug via `timedatectl` (VPS system
clock: Etc/UTC, not IST) cross-checked against the installed crontab:
2 of the 6 turion cron lines (deploy.sh's daily restart, the market-
open retry-start window) were installed using raw IST hour digits
without UTC conversion - "0 8" and "*/5 8-9" - while the OTHER 4
(pre-market/running-market/closing health checks) WERE correctly
converted. Traced to the source: deploy.sh's own 18-Aug design comment
and turion-event-driven.service's own 18-Aug retry-window comment
BOTH gave their example crontab line in raw IST digits (written before
any real VPS/timezone existed to get this wrong against) - whoever
installed the crontab on 20-Aug (B15) copied those two lines verbatim
instead of converting, while computing the other 4 correctly from
scratch. Real consequence if left unfixed: deploy.sh would have first
fired at 08:00 UTC = 13:30 IST - a live service restart in the MIDDLE
of trading hours, precisely the risk deploy.sh's own design doc says
this whole cron approach exists to avoid (see its "DECIDED 18-Aug"
comment).

Confirmed with the user before touching live infrastructure (asked
directly, got "yes fix it now"). FIXED: backed up the live crontab to
/tmp/turion_crontab_before.txt equivalent (captured here in the
session transcript) first, then installed a corrected `crontab -u
turion` with deploy at 30 2 * * 1-5 (=08:00 IST) and the retry window
split into three UTC-aligned lines (30-55/5 2, */5 3, 0-25/5 4 - all
`* 1-5`, together covering 08:00-09:55 IST in 5-min steps, since the
window straddles a UTC hour boundary at IST's :30 offset). Verified
via `crontab -u turion -l` after. Also fixed both source comments
(deploy/deploy.sh, deploy/turion-event-driven.service) so a future
re-install from this repo doesn't repeat the same mistake - the VPS
crontab was fixed directly first; the comment fix is belt-and-braces,
not the actual fix.

--------------------------------------------------

Next Session

1. DONE, same session - see "B19 COMPLETED FOR REAL" above. Both VPS
   services confirmed live with a real token, no crash-loop, real
   ticks flowing. Still worth a follow-up check after today's 09:15
   IST market open to confirm a full decide_fn cycle (open/hold/close)
   runs clean during real trading hours, not just at startup.

2. Small cleanup, not urgent: deploy.sh's own `systemctl status` step
   sudo-fails every run (see above) - either widen the turion sudoers
   scope to include `status`, or remove that line from deploy.sh.

3. DONE, same session - see "CRON UTC-VS-IST BUG FOUND AND FIXED"
   above. Watch tomorrow's (or later today's) actual cron firings
   (/var/log/turion-deploy.log, /var/log/turion-health-check.log)
   to confirm the corrected times actually produce output at the
   right IST wall-clock moments, not just that the crontab syntax
   looks right.

--------------------------------------------------

TWO MORE REAL BUGS FOUND AND FIXED, SAME SESSION, POST-MARKET-OPEN
CHECK - user asked to check the VPS again after market open. Found:

(1) TICK-LATENCY SENTINEL BUG - today's real health-check report
showed an impossible "avg 7,273,783,216.3ms, max 3,934,760,813,769.0ms"
tick latency. Root cause traced to a real archived record:
{"timestamp": "1901-12-14 02:15:52.000", ...} - reverse-computed the
epoch for that exact IST string and got precisely -2147483648 (32-bit
signed int's minimum). Fyers occasionally sends exch_feed_time as this
sentinel for a tick with no real exchange timestamp yet;
format_tick_record() has no way to detect it at write time, so it
archives as a real-looking 1901 date, and tick_latency_ms() blindly
diffed it against a real 2026 received_at - decades of "latency"
poisoning every avg/max. FIXED: tick_latency_ms() (strategy/tick_
collector.py) now treats a negative or >5-minute latency as
unmeasurable (returns None), same as its existing missing-received_at
case.

(2) NO MARKET-HOURS GATE IN THE EVENT-DRIVEN ENGINE - grepped the
whole event-driven pipeline for any market-open check and found none
at all. Real consequence, confirmed from actual portfolio data: a
WebSocket connection replays Fyers' last pre-market snapshot on
connect (often yesterday's closing quote), and with no gate, BOTH
event-driven books (simple_st1_threshold, st2_threshold) opened a
real-tracked NIFTY PE position on that stale data at 07:59:55 IST
today (Entry Spot 24231.85 - exactly yesterday's 20-Aug 17:25 IST
archived spot). When real market data arrived, the (fake) entry
premium vs the real premium triggered a genuine-looking Stop Loss for
-Rs 22,949.63 (-22.95%) in EACH book (~Rs 45,900 combined) - a real,
quantified, bug-caused paper loss, not a real trading signal. Also
found a SECOND instance of the same class from an earlier run: one
Closed Trade in each book has "Entry Time": "1901-12-14 02:15:52" -
the exact same INT32_MIN sentinel, this time corrupting a real
decide_fn's data_point["timestamp"] (not just the tick archive),
which then triggered an immediate Square-Off once past_squareoff()
compared "1901" against a real 2026 clock.

FIXED: added a `before_market_open` field to both decide_fns' data_
point contract (strategy/event_driven_engine.py), computed upstream in
strategy/live_tick_harness.py from the ALREADY-EXISTING MARKET_OPEN_
TIME=(9,15) constant (reused from strategy/fyers_options_engine.py,
not duplicated). Matches that module's own check_or_open() convention
exactly: only gates NEW entries - an already-open position (e.g. one
legitimately carried overnight) still gets checked for Target/Stop-
Loss/Square-Off regardless of time. 4 new tests (2 decide_fn-level, 1
runner-level, 1 confirming an existing position is still managed even
when before_market_open=True) - 522/522 passing.

Both fixes committed (85e1aa0ed after a rebase onto concurrent
automated portfolio commits - 6596bc706) and deployed live via SSH
(deploy.sh's exec bit had been silently reset by the git pull despite
core.fileMode=false, same class of gap as B16's original chmod fix -
re-chmod'd before retrying). Both services confirmed stable (0
restarts) since the 03:32:54 UTC redeploy. The pre-existing bad
position closed for real (Stop Loss, the real loss recorded above)
within seconds of the new code landing - expected: the new gate only
blocks NEW entries, an existing bad position still gets managed to
closure, not silently held forever.

STILL OPEN, user deferred: what to do with the two bug-caused Closed
Trade records (-Rs 22,949.63 each) in reports/fyers_options_simple_
st1_threshold_eventdriven_portfolio.json and reports/fyers_options_
st2_threshold_eventdriven_portfolio.json - reverse them (restore Cash,
delete the entries) or leave them with a note that they're bug-
generated, not real signals. User asked to finish the rest of the VPS
work first; revisit this explicitly next session if not already
resolved.

--------------------------------------------------

MOBILE APP - VPS TAB, LIVE CHART, AND CHECKS TAB ALL STUCK LOADING
FOREVER - REAL BUG FOUND AND FIXED - user reported the Checks tab's
pre-market section never left its loading spinner; asked to check the
VPS tab too, which turned out to have the identical symptom, ruling
out anything Checks-screen-specific.

Confirmed the backend side was NOT the problem first (before touching
any app code) - queried the Realtime Database directly via its own
REST API (`curl .../health_checks.json?shallow=true`) and got back
real data for both "market" and "pre_market", with the exact expected
shape. So sync_health_check()/sync_state() on the Python/VPS side were
never in question - this was 100% an app-side bug.

ROOT CAUSE: mobile_app/android/app/google-services.json has no
"firebase_url" key (it predates the Realtime Database being enabled
on this project - added 20-Aug, see doc/PROJECT_STATUS.md's "FIREBASE
PART A" entry - the google-services.json file itself was never
regenerated after). This project's RTDB instance also lives in a
NON-default region (asia-southeast1/Singapore, chosen 20-Aug since
Mumbai/asia-south1 isn't an available RTDB region) rather than the
us-central1 every bare `FirebaseDatabase.instance` call implicitly
assumes without an explicit databaseURL. Every one of the app's 3 live
Firebase streams (watchEventDrivenPortfolio, watchLiveTick,
watchHealthChecks, all in mobile_app/lib/event_driven_realtime_
service.dart) used the bare `.instance` getter, so `ref.onValue` never
fired even once on a real device - not an error the app could catch
and show, just permanently pending, which is exactly why every screen
sat on its CircularProgressIndicator forever with no error message.

FIXED: one shared `_database` instance built via `FirebaseDatabase.
instanceFor(app: Firebase.app(), databaseURL: 'https://turion-ai-
trader-default-rtdb.asia-southeast1.firebasedatabase.app')`, used by
all 3 functions instead of the bare `.instance` getter - the real URL
now lives in code, robust to google-services.json never being
regenerated with a "firebase_url" key (rather than relying on that
file, which this repo doesn't control the regeneration of). `flutter
analyze` clean. Release APK rebuild kicked off in the background
(--dart-define=GITHUB_PAT, same flag every release build needs) - NOT
YET installed/verified on the real device as this entry is written;
check its result and install before considering this actually fixed,
not just code-complete.

2. All other open items unchanged from doc/20aug26_SESSION_LOG.md's
   own "Next Session" list (sync_ticks_from_vps.py end-to-end
   exercise, off-machine backup, mobile app real-data verification,
   end-Sep-2026 statistical-tools checkpoint) - not re-duplicated here,
   see that file.

--------------------------------------------------

Rs 2,000 (LATER: 2%) DAILY-PROFIT-LOCK VARIANT BOOKS - user's own ask,
after seeing today's real -Rs 22,949.63 stale-data trade: wanted a
daily profit lock like the older polling engine's simple_st1_threshold
_nifty has (daily_profit_lock=True, Rs 2,000 flat), but explicitly
did NOT want the two existing live books (st2_threshold, simple_st1_
threshold) touched - wanted it as new, separate books instead, running
alongside. Matches this repo's "add new functionality as separate
engines" rule and how the old engine's own _slcap/_trailing2pct/
_2pctlock variants were already added (never a mutation of the
original).

Added optional daily_profit_lock/daily_profit_lock_pct fields to
make_st2_threshold_event_cfg()/make_simple_st1_threshold_event_cfg()
(strategy/event_driven_engine.py), default False/no behavior change.
rsi_momentum_decide_fn gates only NEW entries once today's realized
PnL (computed upstream in live_tick_harness.py from the portfolio's
own Closed Trades - decide_fn's pure contract never sees them
directly) reaches the threshold - an already-open position still gets
managed regardless. Two new books wired in event_driven_runner.py -
st2_threshold_lock_eventdriven, simple_st1_threshold_lock_eventdriven
- sharing the existing books' NIFTY ATM strike/candles/previous-close
via a small per-index cache added the same session (avoids doubling
real network calls at every startup).

CHANGED SAME SESSION, user's own follow-up: originally built as a flat
Rs 2,000 cap; user then asked for 2% of capital instead (scales if
capital changes) - "जर तो trade 2% च्या वरती... close झाला तरी चालेल
पण daily minimum 2% घेतलेच पाहिजेत" (a single trade closing above the
threshold is fine, only the NEXT entry gets blocked once the day's
cumulative realized PnL has reached 2%) - matches fyers_options_
engine.py's own daily_profit_lock_pct convention. Renamed the cfg
field accordingly (daily_profit_lock_pct=2.0 default) before this ever
shipped with the flat-rupee version live.

--------------------------------------------------

OI_FOOTPRINT NEVER TRADING - REAL BUG FOUND, USER'S OWN CATCH - user
asked directly why oi_footprint (both NIFTY and BANKNIFTY) had zero
trades since 20-Aug. Grepped the whole codebase for refresh_oi_
snapshots() (the function that feeds a real OI snapshot into both
runners): it existed, was fully implemented and wired to accept data -
but was never actually CALLED anywhere. No thread, no scheduler, dead
code. OIBuildupTracker.latest_signal had been permanently None the
entire time, so oi_footprint_decide_fn's own first check ("SKIPPED (no
meaningful OI buildup)") always fired.

FIXED: a daemon thread in main() (event_driven_runner.py), matching
run_tick_collector.py's own ATM-recheck pattern, calling refresh_oi_
snapshots() every 5 minutes (OI_REFRESH_SECONDS - the old polling
engine's own real cadence, per .github/workflows/fyers_multi_
strategy_options.yml's "moved here (from the 5-min..." comment). Also
fixed refresh_oi_snapshots()'s own naive datetime.datetime.now() (this
VPS's clock is UTC) to datetime.datetime.now(IST) - every downstream
squareoff comparison assumes an already-IST value.

VERIFICATION HIT ITS OWN REAL BUG: added a confirmation print on every
successful refresh cycle so success wasn't silently indistinguishable
from "never ran" - and it never appeared for 6+ minutes despite the
underlying REST call working fine when tested manually (confirmed via
a matching-environment SSH diagnostic, sourcing the VPS's real .env).
Root cause: under systemd, stdout isn't a TTY, so Python defaults to
full block buffering - print() output could sit unflushed for a long
time. FIXED both run_event_driven_engine.py and run_tick_collector.py's
existing sys.stdout.reconfigure(encoding="utf-8") calls to also pass
line_buffering=True. Confirmed working after: "OI snapshot refresh OK"
logged reliably every 5 min across multiple restarts, and BANKNIFTY
oi_footprint took 2 real trades (net -Rs 4,393.45) proving the whole
signal->entry->exit path now genuinely works end to end. NIFTY
oi_footprint stayed at 0 trades in the observed window - confirmed
NOT a bug (identical code path as the now-working BANKNIFTY book) -
just no real buildup signal yet, a market-condition fact, not a code
gap.

--------------------------------------------------

REAL TICK-LATENCY BOTTLENECK FOUND AND FIXED - user asked to check
overall latency; report/market_checks.py's own tick-latency line
showed avg ~2s, max ~46.5s across 92,124 real ticks (not the earlier
sentinel-bug garbage - genuinely measured, still far too slow for
"tick-by-tick"). Root cause traced to BOTH VPS processes: run_tick_
collector.py's on_message() and event_driven_runner.py's save_all()
each called a Firebase Realtime Database write (firebase_admin's
db.reference().set(), a real cross-region REST call - VPS in Mumbai,
RTDB in Singapore) SYNCHRONOUSLY, blocking the WebSocket's own receive
thread on every tick. event_driven_runner.py was worse: save_all()
re-saved AND re-synced ALL 6 runners on every single tick, regardless
of which runner (if any) that tick actually touched.

FIXED: a bounded ThreadPoolExecutor (4 workers, not one raw thread per
tick - a burst can't spawn unboundedly more outstanding writes than
can drain) for the Firebase call only in both processes - the local
JSON/JSONL archive stays synchronous and immediate (that's still the
real source of truth). event_driven_runner.py's MultiStrategyRouter
gained runners_for(symbol) so on_message() only touches the runner(s)
that tick's symbol actually affects. 4 new tests (MultiStrategyRouter.
runners_for, save_all's keys/firebase_executor params).

REGRESSION CAUGHT WITHIN MINUTES OF DEPLOYING THIS - every firebase_
executor.submit() call started failing with "cannot schedule new
futures after interpreter shutdown" on literally every tick, on BOTH
processes. Root cause (pre-existing, not introduced by the fix - just
the first thing sensitive to it): FyersDataSocket.connect() doesn't
block - it starts its own background threads (message/ping/ws_thread
inside the SDK, plus keep_running()'s own infy_loop) and returns
immediately, so main()'s top-level script script actually FINISHES
right after connect() returns. Python then starts real interpreter
shutdown (concurrent.futures' own atexit hook fires, setting its
process-wide shutdown flag) even though the OS process stays "alive"
per systemd (Python's threading._shutdown() blocks forever on the
non-daemon infy_loop thread, which never exits) - any executor.submit()
from that point on is permanently broken. FIXED: an explicit `while
True: time.sleep(3600)` after socket.connect() in both processes,
keeping the main thread genuinely alive - what a persistent background
service should do regardless of this specific bug. Re-verified clean
after redeploy: zero errors, and the real median/p90/max latency
dropped to a much tighter, more consistent 1.5s/2.1s/2.8s (from 1.5s
median/18s p99/46.5s max before).

STILL ~1-2s BASELINE REMAINS, CONFIRMED NOT OUR CODE - user pushed
back expecting sub-400ms after this fix. Investigated further: local
disk flush timed at ~0.001ms (not the bottleneck), tick arrival rate
~8-12/sec (not overwhelming), and the SDK's own incoming-message
dispatch is direct/synchronous with no internal queue (read the SDK
source). Checked one single symbol's own tick-by-tick timestamp gaps
in isolation: consistently 1.4-2.2s, tick after tick - too tight and
regular to be network jitter or a code-side backlog (those look
bursty/random, not this uniform). Conclusion, presented honestly to
the user: the remaining latency is very likely Fyers' own server-side
batching/broadcast cadence (common for retail broker feeds to conserve
bandwidth), outside what VPS-side code changes can fix. User accepted
this, moved on ("ते नंतर पाहू").

--------------------------------------------------

LIVE CHART CANDLE-HISTORY BACKFILL - user's own catch: the mobile
app's live chart showed only one lone building candle, not a real
chart - because LiveChartScreen's client-side candle aggregation
(mobile_app/lib/screens/live_chart_screen.dart) had no history to seed
from; Firebase's live_ticks path only ever holds the single latest
tick (report/firebase_realtime_sync.py's sync_live_tick(), a `.set()`,
by design - the durable history is the VPS's own local JSONL archive,
never exposed to the app before now).

Backend: strategy/tick_collector.py gains LiveCandleAggregator (pure,
tested, 7 new tests) - deliberately SEPARATE from strategy/live_tick_
harness.py's own CandleAggregator (5-min, RSI-focused, feeds real
trading decisions, must not change) - this is 1-min, display-only,
archival-process-only, matching this repo's "each engine one
responsibility" rule. run_tick_collector.py maintains one per index
from SPOT ticks, syncing via the new report/firebase_realtime_sync.py
sync_live_candles() ONLY on a closed candle (once/min/index, not per
tick - a per-tick sync here would have reintroduced the latency bug
just fixed above). firebase/database.rules.json opens read access on
the new /live_candles path - NOT yet re-published in the actual
Firebase Console (same manual step this project has needed before) -
confirmed still returning "Permission denied" via a direct REST check
after deploying.

App: event_driven_realtime_service.dart gains fetchLiveCandles() (a
one-time get(), not a stream). live_chart_screen.dart calls it in
initState() alongside the existing live-tick subscription - handled
the real race between the two explicitly (a live tick can add the
current forming candle before the history fetch resolves): history
gets inserted at position 0, and its own last entry is dropped if it
shares the live stream's already-added current minute. flutter
analyze clean. Deployed to the VPS same session; release APK rebuild
kicked off in the background per the user's own explicit instruction
- build now, INSTALL LATER (not yet installed as this entry is
written).

--------------------------------------------------

Next Session (REVISED, supersedes the numbered list above)

1. Publish the updated firebase/database.rules.json in the actual
   Firebase Console (adds /live_candles read access) - without this
   the app's new chart backfill will keep hitting "Permission denied".
   Verify with: curl https://turion-ai-trader-default-rtdb.
   asia-southeast1.firebasedatabase.app/live_candles.json (should
   return real candle data, not an error, once both this is done AND
   at least one candle has closed since the backend deploy).

2. Install the new release APK (built this session, NOT yet installed
   per the user's own explicit "install later" instruction) and verify
   the live chart actually shows real backfilled history on open, not
   just a lone candle.

3. Confirm NIFTY oi_footprint eventually takes a real trade once a
   genuine OI buildup signal occurs - BANKNIFTY already proved the
   mechanism works end to end; NIFTY just hadn't seen a signal in the
   observed window.

4. The two new daily-profit-lock books (st2_threshold_lock_
   eventdriven, simple_st1_threshold_lock_eventdriven) are live and
   trading - worth a real comparison against their un-locked siblings
   after a few real trading days, to see whether the 2% lock actually
   helps net P&L or just cuts off legitimate same-day recovery (same
   open question the older polling engine's own daily_loss_lock
   backtest already answered differently per book - not assumed here).

5. All items from doc/20aug26_SESSION_LOG.md's own "Next Session" list
   not superseded above (sync_ticks_from_vps.py end-to-end exercise,
   off-machine backup, end-Sep-2026 statistical-tools checkpoint).

--------------------------------------------------

LIVE OPTION-PREMIUM CHART WITH REAL Entry/Target/Stop-Loss OVERLAY -
user's own follow-up ask, wanting SL/Target/Trailing-SL visible on a
chart for a book's current position. Scoped this properly before
building: checked how this app ALREADY handles the identical question
for the older polling engine's own options books, and found it had
already been decided once - fyers_multi_strategy_options_screen.dart's
ChartScreen only ever plots Entry Spot for an option position, never
Target/SL, specifically because premium and the underlying's spot
move on different scales (a spot-equivalent SL/Target line would need
an estimated delta, not a real one). Asked the user directly how real
broker apps solve this instead: they chart the option's OWN premium,
not the underlying - so that's what got built, not the earlier-
discussed spot-based approximation.

Backend: strategy/event_driven_runner.py's on_message() now also syncs
BOTH CE and PE legs' live ticks (every tick, via the existing bounded
firebase_executor - same anti-latency-regression discipline as
earlier today) and 1-min candle history (via strategy/tick_collector.
py's LiveCandleAggregator, synced only on candle close) PER STRATEGY,
not per index - a strategy's own ATM strike can differ from run_tick_
collector.py's independent ATM pick for the same index, so the two
data sources are deliberately kept separate (report/firebase_
realtime_sync.py's new sync_strategy_tick()/sync_strategy_candles(),
paths /strategy_ticks/{name}/{leg} and /strategy_candles/{name}/
{leg}). firebase/database.rules.json opened read access on both -
manually re-published in the Console same session (confirmed via
direct REST checks: real live premium data flowing for all 6 books).

App: new strategy_premium_chart_screen.dart computes Target/Stop-Loss
premium from the EXACT SAME formula event_driven_engine.py's decide_
fns use (net PnL from (exit-entry)*lots*lot_size, hybrid stop-loss cap
= min(initial_capital, capital_deployed) * hybrid_sl_cap_pct/100) -
only the round-trip transaction-cost term is omitted (small, known,
honestly labelled in the info banner: "Target/SL are estimates... the
actual close reason always comes from the Closed Trade record" -
rather than silently presenting an approximation as exact, or
duplicating that cost formula a second time in Dart). vps_screen.
dart's `_books` list gained the static cfg constants (lot_size,
initial_capital, hybrid_sl_cap_pct, target_net_pct/stop_loss_pct for
the RSI-momentum books, target_rupees/stop_loss_rupees for oi_
footprint) needed to compute this - mirrors event_driven_engine.py's
own cfg builders exactly, same "hardcoded per book, changes need a
redeploy+rebuild anyway" reasoning already used for label/underlying.
Open positions' "View Chart" now opens this instead of the spot
chart; closed trades keep the existing spot chart (a closed trade
isn't a "current position" to show live SL/Target for). flutter
analyze clean, 542/542 Python tests passing.

Release APK rebuilt with this feature - NOT YET installed as this
entry is written (adb lost the phone connection mid-session; user
chose to install later rather than troubleshoot the USB link right
then).

==================================================

Next Session (FINAL for today - supersedes all earlier numbered lists
in this file)

1. Install the latest release APK (has the strategy premium chart on
   top of everything else built today) once the phone's USB/adb
   connection is available again.

2. Verify on-device: the live chart (index-level) shows real backfilled
   candles on open, and a book's "View Chart" (when it has an open
   position) shows the new CE/PE premium chart with Entry/Target/SL
   lines - both need a REAL open position and a device to check
   against, neither confirmed visually yet, only via direct Firebase
   REST checks proving the data itself is correct.

3. Confirm NIFTY oi_footprint eventually takes a real trade (BANKNIFTY
   already has, proving the mechanism).

4. Compare the two new daily-profit-lock books against their un-locked
   siblings after a few real trading days.

5. All items from doc/20aug26_SESSION_LOG.md's own "Next Session" list
   not already superseded (sync_ticks_from_vps.py end-to-end exercise,
   off-machine backup, end-Sep-2026 statistical-tools checkpoint).

--------------------------------------------------

VPS-vs-GITHUB SAME-DAY COMPARISON - REAL EVIDENCE FOR THE DAILY LOCK,
AND A SEPARATE REAL FINDING ON THE OLD ENGINE'S OWN INFRASTRUCTURE -
user asked to compare today's VPS event-driven st2_threshold/simple_
st1_threshold against their GitHub-Actions-based namesakes (same RSI-
momentum logic, same target/SL cfg). Numbers, same trading day:

  VPS (tick-by-tick, no lock):   st2 77 trades net -Rs 38,408.76
                                  simple_st1 99 trades net -Rs 50,034.47
  VPS (tick-by-tick, 2% lock):   st2 1 trade net +Rs 5,012.90 (locked)
                                  simple_st1 1 trade net +Rs 3,282.85 (locked)
  GitHub (old, ~1-min polling):  st2 1 CLOSED trade -Rs 5,740.46,
                                  1 more OPENED 14:17:25 IST (still open)
                                  simple_st1 1 CLOSED trade -Rs 6,152.07

Today was a genuinely choppy/range-bound day - real per-tick data
confirmed the whipsaw wasn't a data bug (checked earlier the same
session). The VPS's fast, tick-by-tick reaction correctly fixed its
own designed problem (near-zero overshoot per stop - each VPS loss
landed almost exactly at the ~Rs 2,000 hybrid cap) but, with no entry-
frequency cap, that same speed let it re-enter far more often than the
old engine ever got the chance to, and the CUMULATIVE loss from many
small stops ended up far worse than the old engine's one bigger loss.
The 2% daily-profit-lock books (built earlier this session) are direct
proof of the fix: one early winning trade, then correctly no further
entries all day - avoided the entire rest of the whipsaw.

SEPARATE REAL FINDING, following the user's own sharp follow-up
("जर queue मध्ये trades असतील... तर चुकीची entry होणार, मग ती
strategy fail ना?"): investigated why the OLD (GitHub Actions) engine
sat flat for ~4h15m (10:02-14:17 IST) between its two entries today.
Queried the GitHub REST API directly (using the local GITHUB_PAT):
.github/workflows/fyers_multi_strategy_options.yml has 83,581 total
completed runs all-time, and AT THE MOMENT OF THIS CHECK had 36 runs
queued and 17 in progress simultaneously - a real, live backlog. This
workflow covers 15+ different strategy groups (simple_st1/st2/st3/st4/
gapfill/vix_filter/oi_footprint/credit_spread/pcr_momentum/max_pain_
drift/pcr_vix_combo/oi_iv_combo/slcap variants/oi_hybrid_sl variants),
each with its own ~1-min cron-job.org trigger (per that workflow's own
07-Aug concurrency-group comment) - GitHub's free-tier concurrent-job
limit almost certainly can't keep up with that combined trigger rate
during active market hours, so real checks for any GIVEN strategy can
end up spaced out far beyond the intended ~1 minute.

CONFIRMED THIS MATTERS, NOT JUST COSMETIC: when a delayed run finally
executes it DOES fetch a genuinely live quote (not stale data), so a
NEW entry's price is real - but an OPEN position's Target/Stop-Loss
monitoring gets exactly as delayed as the queue backlog, which is
THE SAME root-cause class as the documented oi_footprint overshoot
incidents that originally motivated this whole VPS project (14-Aug/
18-Aug PROJECT_STATUS.md entries) - today's own GitHub-side st2 loss
(-Rs 5,740.46 against a ~Rs 2,000 intended hybrid cap, ~2.9x overshoot)
is itself a live instance of it. NOT YET INVESTIGATED FURTHER OR FIXED
- user asked to just document this for now (out of scope for today,
and per this repo's own "never modify a working module" rule for the
~60 already-live polling books - any fix here would likely mean
cron-job.org dashboard changes, not code, e.g. spacing out per-
strategy trigger schedules rather than firing everything near-
simultaneously every minute).

==================================================

Next Session (SUPERSEDES all earlier numbered lists in this file -
this is the final one for 21-Aug)

1. Install the latest release APK (strategy premium chart + everything
   else built today) once the phone's USB/adb connection is back.

2. Verify on-device: index-level live chart backfill, and a book's new
   CE/PE premium chart with Entry/Target/SL lines - both only checked
   via direct Firebase REST so far, never visually on a real device.

3. Confirm NIFTY oi_footprint eventually takes a real trade (BANKNIFTY
   already has).

4. Compare the two new daily-profit-lock books against their unlocked
   siblings after a few more real trading days - today's single-day
   numbers (see "VPS-vs-GITHUB SAME-DAY COMPARISON" above) already
   look strongly favorable, but one day is not a real backtest.

5. NEW - investigate the GitHub Actions queue-backlog finding above
   (36 queued/17 in-progress at check time, 83,581 runs all-time) if
   the user wants to revisit it - likely needs cron-job.org dashboard
   changes (trigger spacing/frequency), not a code fix, and is
   out-of-scope for the VPS work this session focused on. Real,
   confirmed overshoot risk for the ~60 still-GitHub-Actions-based
   live books, same root-cause class as the 14-Aug/18-Aug oi_footprint
   incidents that originally motivated the VPS migration.

6. All items from doc/20aug26_SESSION_LOG.md's own "Next Session" list
   not already superseded (sync_ticks_from_vps.py end-to-end exercise,
   off-machine backup, end-Sep-2026 statistical-tools checkpoint).

--------------------------------------------------

CHART TIMEFRAME/VOLUME/HISTORY WORK - REAL BUGS FOUND LIVE ON A REAL
DEVICE, FIXED SAME SESSION - continuation of the strategy premium
chart work above. User asked for a timeframe selector (1/5/10/15 min)
and volume bars (a real broker app screenshot shown as the reference).

Built: mobile_app/lib/candle_aggregation.dart (pure, groups the
existing 1-min history into coarser real-clock-aligned buckets client-
side - no new backend data needed for timeframe switching itself);
widgets/timeframe_selector.dart (shared button row); strategy/
tick_collector.py's LiveCandleAggregator gained optional per-candle
volume (real delta computed from Fyers' own cumulative vol_traded_
today - SPOT/index candles never have it, since NIFTY/BANKNIFTY are
computed indices, not traded instruments; CE/PE premium candles do);
widgets/candlestick_chart.dart gained a volume-bar strip, only
reserved when at least one candle actually carries "Volume" (index
chart layout unchanged).

TWO MORE REAL RENDERING BUGS CAUGHT LIVE VIA REAL SCREENSHOTS (both
during today's genuinely-flat post-market-close conditions, which
turned out to be an unusually good stress test for chart edge cases):
(1) the reference-line/axis padding fix from earlier today worked (5
distinct price levels appeared, not one repeated value) but the
candle body itself, being Open=Close exactly, still collapsed to a
1-DEVICE-pixel rectangle - invisible on a real phone screen even
though visible in theory. Fixed with a 2.5px minimum body height,
centered on the true price. (2) User then asked for the FULL trading-
day history (candles from where a trade actually started), not just
a 2-hour rolling window - LiveCandleAggregator's max_candles (and
both screens' own matching _maxCandles) raised from 120 to 400
(covers the full 375-min NSE session). Tested live and found ONLY 1
candle showing even after this fix - traced to a real, honest
limitation rather than a new bug: today's many deploys each reset the
in-memory candle history, and by ~19:20 IST Fyers had stopped sending
any live ticks at all (a fresh connection only gets one last-known-
state replay per symbol, then silence) - nothing left to rebuild a
real intraday history from this late in the day. The fix itself is
correct; today just couldn't provide real evidence for it. Confirmed
with the user to verify for real on Monday (25-Aug, next trading day
after the weekend) instead, once deploys aren't happening
continuously through market hours.

545/545 Python tests passing, flutter analyze clean throughout.
Latest APK (all of today's fixes) installed and running on the user's
device.

--------------------------------------------------

Next Session (FINAL for 21-Aug - supersedes the numbered list above)

1. Monday 25-Aug (next trading day), during real market hours: verify
   the chart timeframe selector, volume bars, and full-day candle
   history (400-candle cap) all work as intended against real live
   data, without today's repeated-deploy interference. Also re-verify
   the earlier-listed items (strategy premium chart Entry/Target/SL
   overlay, index chart backfill) on-device against real (non-flat)
   price movement for the first time.
2. Confirm NIFTY oi_footprint eventually takes a real trade (BANKNIFTY
   already has).
3. Compare the two new daily-profit-lock books against their unlocked
   siblings after a few more real trading days.
4. GitHub Actions queue-backlog finding (documented, not fixed) -
   revisit only if the user wants to; needs cron-job.org dashboard
   changes, out of scope for VPS work.
5. All items from doc/20aug26_SESSION_LOG.md's own "Next Session" list
   not already superseded (sync_ticks_from_vps.py end-to-end exercise,
   off-machine backup, end-Sep-2026 statistical-tools checkpoint).

==================================================

END OF SESSION
