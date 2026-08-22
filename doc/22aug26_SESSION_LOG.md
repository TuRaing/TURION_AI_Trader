# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260822-001

--------------------------------------------------

Date

22-Aug-2026

--------------------------------------------------

QUOTE-BASED PnL BOOKKEEPING - REPORTING ONLY (commit 7c6de64fa) -
continuation of 21-Aug's real depth-based slippage finding (the
event-driven engine's LTP-based "Entry/Exit Premium" overstated
realized PnL by ~87-91% on a thin ATM book - a real 21-Aug trade
recorded Rs 3,282.85/Rs 5,012.90 vs a realistic ~Rs 435-616 once
bid/ask spread is walked via real order-book depth data). Added
`Entry Premium (Quote)` / `Exit Premium (Quote)` / `Net PnL (Quote)`
fields to `rsi_momentum_decide_fn` and `oi_footprint_decide_fn` in
strategy/event_driven_engine.py - REPORTING ONLY, does not change any
decision logic (user explicitly chose this scope over changing live
decisions). Reuses ce_bid/ce_ask/pe_bid/pe_ask that were already
flowing into every live data_point but never read anywhere. 4 new
tests added, 87/87 passing that day. Pushed to main this session.

==================================================

SIX NEW QUOTE-BASED STRATEGIES + CONSECUTIVE-LOSS CIRCUIT BREAKER
(commit 473d05653) - user asked for 4 groups of new strategies
(2%/1%/0.5% daily-lock tiers using real quote-based decisions, plus a
4th capped-size/no-lock group). The 4th group was explicitly dropped
by the user after discussion, leaving 3 groups x 2 base strategies
(ST2 Threshold, Simple ST1 Threshold) = 6 new books. Built with a
formal Plan (EnterPlanMode/ExitPlanMode workflow) given the scope - 2
Explore agents researched the existing cfg-builder signatures, the
STRATEGY_NAMES/build_runners() registration pattern, and existing
"stop trading" cfg fields (found the consecutive-loss pattern already
existed in fyers_options_engine.py, avoiding reinventing it) before
the plan was written.

Built:

- `rsi_momentum_quote_decide_fn` in strategy/event_driven_engine.py -
  a NEW decide_fn where Target/Stop-Loss actually TRIGGER off real
  bid/ask (not LTP). Refactored the existing `rsi_momentum_decide_fn`
  into a shared private `_rsi_momentum_decide(cfg, position,
  data_point, entry_field, exit_field)` core so both variants share
  one implementation - `rsi_momentum_decide_fn` became a thin wrapper
  (`entry_field=exit_field="ltp"`), confirmed byte-identical behavior
  via the full existing test suite passing unchanged.

- 6 new STRATEGY_NAMES keys registered in strategy/event_driven_
  runner.py's build_runners(): st2_threshold_lock_quote2pct/quote1pct/
  quote0pt5pct and simple_st1_threshold_lock_quote2pct/quote1pct/
  quote0pt5pct (each _eventdriven-suffixed for the persisted portfolio
  filename).

- Consecutive-loss circuit breaker: ported (not reinvented) from
  strategy/fyers_options_engine.py's already-proven
  MAX_CONSECUTIVE_LOSSES=2 / _today_consecutive_losses() /
  daily_loss_lock mechanism. New `daily_loss_lock` / `max_consecutive_
  losses` cfg fields added to the RSI-momentum cfg builders.
  `today_consecutive_losses` computed in LiveTickRunner (strategy/
  live_tick_harness.py), using the SAME naive-IST date convention as
  the existing `_today_realized_pnl` (deliberately NOT the polling
  engine's naive-UTC convention - a documented, avoided pitfall).
  Turned ON for st2_threshold/simple_st1_threshold specifically -
  these two whipsawed 81/106 trades on 21-Aug (71-79% Stop-Loss rate,
  net -Rs 44,142/-Rs 49,783), backtested against that real trade
  sequence: N=2 was the only rule (vs cooldown timers, max-trades
  caps) that flipped both books to profit (+Rs 3,844/+Rs 1,821, though
  on only 3-4 trades - too few to trust the exact parameter yet).

- mobile_app/lib/screens/vps_screen.dart updated with the 6 new book
  entries (its book list is hardcoded/static, not fetched - confirmed
  via code exploration that this file and vps_summary_screen.dart both
  hardcode STRATEGY_NAMES).

12 new tests (9 in tests/test_event_driven_engine.py, 3 in tests/
test_live_tick_harness.py). Full repo suite: 566/566 passing.

--------------------------------------------------

REAL DEPLOY ATTEMPT EXPOSED A WEEKEND CRASH-LOOP, FIXED SAME SESSION
(commit 3a0231b9f) - after committing the two items above, user asked
to deploy to both git (push) and VPS. Git push succeeded. VPS deploy
(deploy/deploy.sh, SSH as root) pulled the code fine but both systemd
services (turion-event-driven, turion-tick-collector) crash-looped on
restart with "Please provide valid token" (Fyers access_token expired
- nobody had reason to log in on a Saturday, market closed). Confirmed
via journalctl this was UNRELATED to the new code - the old process
was already failing the same way in its periodic OI-refresh calls
before the restart; the restart just exposed it via build_runners()'s
unguarded pick_atm_symbols() call. User initially thought market might
be open (confused about day of week) - corrected, then asked "why does
the code even try to run when market is closed."

Fix: both run_event_driven_engine.py and run_tick_collector.py now
check `datetime.now(IST).weekday() >= 5` (Saturday=5, Sunday=6) as the
VERY FIRST check in main(), before even fetching a token, and
`sys.exit(0)` cleanly with a log line if it's a weekend. NSE real
holidays (Diwali, Republic Day etc.) are explicitly NOT covered -
would need a maintained holiday calendar, out of scope. Verified live
on the actual VPS: both services now print "Saturday - NSE is closed
on weekends, skipping this start attempt." and exit with
status=0/SUCCESS, Active: inactive (dead) - no more crash-loop.

--------------------------------------------------

MOBILE APP - APK REBUILT AND INSTALLED (TWICE) - `flutter build apk
--release` + `flutter install` onto the user's connected Android phone
(Motorola edge 20 fusion), done twice this session: once after the
6-new-strategies mobile_app change (commit 473d05653 above), and once
again after adding the one-line Marathi book descriptions (see the
tick-compression entry below).

==================================================

TICK ARCHIVE SIZE CHECK + DAILY LOCAL COMPRESSION, PLUS PER-BOOK
MARATHI DESCRIPTIONS (commit 4f091b582) - user asked how big the
tick-by-tick archive (run_tick_collector.py's output, data/ticks/ on
the VPS) had grown: 44MB uncompressed for one full real trading day
(21-Aug, 214,303 real ticks, confirmed both NIFTY and BANKNIFTY
present with continuous 09:15:00-15:30:00 coverage, zero gaps over 60
seconds). Gzip-compressed: 2.86MB (~16x smaller).

Built run_tick_compress.py - gzips every COMPLETED day's tick file in
place (verifies the compressed output is real/non-empty/smaller before
deleting the original), keeping the .gz locally on the VPS - does NOT
need the B2 cloud account run_tick_upload.py (the existing sibling
script) still isn't configured for. Cron'd on the VPS: `30 12 * * 1-5`
(18:00 IST Mon-Fri). Manually run once already to compress the real
21-Aug file (confirmed: 45,662,418 bytes -> 2,491,324 bytes). The
compressed file was also copied to the user's local machine
(D:\TURION_AI_Trader\data\ticks\, gitignored - real trading data never
belongs in git history).

Same commit added the per-book Marathi one-line descriptions to
mobile_app/lib/screens/vps_screen.dart (user's explicit ask) - a
`description` field added to each of the 12 `_books` record entries,
displayed at the top of that book's own tab.

--------------------------------------------------

TICK FILENAME FORMAT CHANGE: YYYYMMDD -> DDMMYY (commit 855d2d611) -
user's explicit ask. Changed strategy/tick_collector.py's
`tick_log_filename()` from `%Y%m%d` to `%d%m%y` (e.g.
"ticks_220826.jsonl" for 22-Aug-2026). Along the way, found and fixed
a real bug: run_tick_compress.py (built earlier this session) had its
OWN hand-inlined "%Y%m%d" format string instead of calling the shared
`tick_log_filename()` - would have silently drifted out of sync with
this exact change. Fixed to reuse the real function. Noted in the
function's own docstring: DDMMYY filenames do NOT sort into
chronological order alphabetically (unlike YYYYMMDD) - not a problem
for any current caller (none need chronological sort), but worth
knowing. Renamed the already-existing files on both the VPS and the
user's local machine to match (ticks_20260821.jsonl.gz ->
ticks_210826.jsonl.gz).

--------------------------------------------------

REAL TICK-ARCHIVE VERIFICATION - no code change, pure analysis, using
the local copy of ticks_210826.jsonl.gz. Confirmed both NIFTY (103,347
ticks) and BANKNIFTY (110,956 ticks) are present, with real SPOT+ATM
CE/PE coverage (ATM strike drift visible: NIFTY 24050/24200/24250,
BANKNIFTY 57500/57600/57700/57800). Confirmed continuous
09:15:00-15:30:00 coverage with zero gaps longer than 60 seconds
(204,094 ticks in that window) - an earlier quick check had a bug in
its own bucket-math that falsely suggested hourly gaps; corrected and
re-verified properly.

--------------------------------------------------

REAL SPREAD-BY-MONEYNESS ANALYSIS - no code change. Using reports/
options_premium_history.jsonl (42,724 historical multi-strike
premium/bid/ask records, NOT limited to ATM), computed real bid/ask
spread % grouped by distance from ATM: ATM 0.36% avg / 0.26% median,
ITM 1-2 strikes 0.38%/0.25%, ITM 3+ 0.48%/0.28%, OTM 1-2 0.46%/0.27%,
OTM 3+ (deep OTM) 0.81%/0.34% - confirms ATM has the tightest real
spread, deep OTM roughly double.

==================================================

FYERS WEBSOCKET DepthUpdate RESEARCH, SCHEDULED FOR MONDAY (commit
0c313ca35) - user wants more accurate slippage numbers (the ~87-91%
overstatement finding still stands as an ESTIMATE, not verified ground
truth - explained why: stale 5-min depth snapshots, no real execution
latency modeled, spreads likely widen further on exactly the
choppy/whipsaw days the strategy trades most). Real web research
(WebSearch + WebFetch, not guessed) confirmed Fyers' WebSocket
supports a `data_type="DepthUpdate"` subscription mode (alongside the
`"SymbolUpdate"` this project's event_driven_runner.py/tick_
collector.py already use) - would give real-time depth instead of the
~5-min-stale REST /depth polling (strategy/fyers_depth_collector.py,
quota-limited). Could NOT confirm the exact message field shape from
any documentation or sample code found - conflicting signals, some
sources describe a different, possibly-paid "50 Market Depth" product
using protobuf, not plain JSON. This is the SAME situation the REST
/depth endpoint was in on 16-Aug-2026 (needed 3 rounds of live fixes
because the assumed shape was wrong, per that day's session log) - so
a "guess and build" approach was explicitly avoided.

Built verify_depth_websocket.py - a ONE-OFF, manually-run diagnostic
script (NOT a permanent service, no systemd unit) that subscribes to
DepthUpdate for NIFTY's ATM CE/PE and prints/saves the first 20 raw
messages (or 120 seconds, whichever first) completely unparsed, to
data/depth_websocket_verification.jsonl, so a human can see the real
shape before any real parsing code gets written. Deployed to VPS.
Since market was closed (Saturday) this couldn't be tested live yet.

A cloud-based "schedule" skill routine was attempted first to
auto-run this Monday morning, but was the WRONG tool - cloud routines
run in an isolated Anthropic-cloud sandbox with no access to the
user's local SSH key needed to reach the VPS. Backed out of that and
instead added a ONE-TIME VPS crontab entry directly (same working SSH
access already used all session):

  50 3 24 8 * cd /opt/turion/TURION_AI_Trader && venv/bin/python
  verify_depth_websocket.py >> /var/log/turion-depth-verify.log 2>&1

- fires once at 03:50 UTC = 09:20 IST on 24-Aug-2026 (Monday), 5
minutes after NSE's 09:15 IST open. User confirmed they keep this chat
open indefinitely, so a future message in this same conversation
("check the results") is how the follow-up will happen - no automated
report-back exists.

==================================================

BACKTESTED (NOT BUILT) TWO MORE STRATEGY-IMPROVEMENT CANDIDATES
AGAINST REAL DATA - both explicitly deferred by the user to next
week's larger dataset, same as the circuit-breaker parameter and Kelly
sizing.

TRAILING STOP-LOSS - ported concept from fyers_options_engine.py's
`trailing_min_pct` / `TRAIL_PCT=0.30` mechanism (peak-tracking: once a
trade's peak Net PnL % first reaches 2%, a trailing floor at 70% of
that peak takes over, replacing the fixed Target entirely; the
original Stop-Loss stays active throughout). That mechanism was NEVER
retrospectively backtestable in the polling engine (needs each trade's
own intraday PEAK premium, which historical Entry/Exit-Premium-only
records don't capture) - but this project now has something the
polling engine never had: a real tick-by-tick archive (data/ticks/
ticks_210826.jsonl.gz) for the exact day (21-Aug) all the event-driven
trades happened.

Built a real backtest: for each of the 4 RSI-momentum books' real
Closed Trades (st2_threshold_eventdriven 81, simple_st1_threshold_
eventdriven 106, st2_threshold_lock_eventdriven 1, simple_st1_
threshold_lock_eventdriven 1), replayed the REAL tick sequence for
that trade's exact symbol starting at its real Entry Time, tracking
peak Net PnL % and applying the exact same formula.

Result: trailing-stop made the two whipsaw books MEANINGFULLY WORSE
(st2: actual -Rs 44,142 -> simulated -Rs 59,872; simple_st1: actual
-Rs 49,783 -> simulated -Rs 58,622) because most trades (51/79
matched, 65/104 matched) never even reached the 2% trailing-activation
threshold before getting stopped out by the ordinary Stop-Loss -
trailing-stop doesn't address the actual problem (the whipsaw itself,
already handled by the circuit breaker). Roughly neutral/mixed on the
two single-trade "_lock" books (st2_threshold_lock: +Rs 5,013 actual
-> +Rs 3,818 simulated; simple_st1_threshold_lock: +Rs 3,283 actual ->
+Rs 3,818 simulated - same simulated outcome for both since trailing
ignores their different target_net_pct settings, both governed purely
by the same real price path).

Caveat stated to the user: this backtest only changes exit logic while
keeping real recorded entry times fixed - a fully faithful simulation
would need to also re-simulate entry timing, since a different real
exit time would shift when the book goes flat again. NOT BUILT - user
agreed to defer to next week's larger dataset.

--------------------------------------------------

IV-FILTER - the exact `MAX_IV_RV_RATIO=1.5` mechanism from
strategy/fyers_options_oi_iv_combo.py (skip entry if the leg's implied
volatility exceeds 1.5x the underlying's 10-day trailing realized
volatility) - that module's own docstring already documents this was
retrospectively backtested twice before: near-free-lunch for
oi_footprint/NIFTY, but "ran BACKWARDS (removed their best trades
instead)" when tested on the RSI-threshold family - the SAME family
st2_threshold/simple_st1_threshold belong to. Surfaced this documented
prior finding to the user immediately before running anything new.

Then built a real backtest anyway against 21-Aug's actual trade data:
implied vol solved via indicators/black_scholes.py's implied_
volatility() (Black-Scholes, using each trade's real Entry Premium/
Entry Spot/strike/expiry), realized vol via yfinance's ^NSEI daily
closes (fyers_download() couldn't be used - no valid Fyers token
available on a Saturday; yfinance was already an existing project
dependency, used only for this one-off research script, no production
code touched) - a real 10-day trailing realized vol of 5.24% as of
20-Aug's close (no look-ahead).

Result: DOUBLE-EDGED, confirming both historical findings
simultaneously on this same day's data - the filter would have
skipped 49/81 and 58/106 trades on the whipsaw books, and those
skipped trades accounted for nearly ALL of that day's real losses
(st2: kept-only total -Rs 1,450 vs actual -Rs 44,142; simple_st1:
kept-only -Rs 4,892 vs actual -Rs 49,783) - but the filter would ALSO
have skipped the ONE real profitable trade both "_lock" books caught
that same day (turning +Rs 5,013/+Rs 3,283 into Rs 0), directly
reproducing the "removed their best trades" pattern already on record.
NOT BUILT - same "need more days of data" deferral.

Side-finding, NOT fixed (flagged only): strategy/fyers_options_oi_
iv_combo.py's `_realized_volatility()` calls `fyers_download(cfg[
"index_symbol_for_rsi"], period="30d", interval="1d")` - "30d" is not
a valid key in strategy/fyers_data.py's PERIOD_TO_DAYS dict (only
5d/7d/10d/60d/1mo/3mo/6mo/1y/2y/5y exist) - that function would raise
ValueError immediately if ever actually invoked live. Left as-is (out
of scope for today), worth a real fix later.

==================================================

SESSION-CONTINUITY NOTE - this session continued directly from
21-Aug's real depth-slippage work (same conversation, spanning into
22-Aug). No separate `git fetch` / `git log HEAD..origin/main` session-
start check was performed as a discrete step at the start of THIS
calendar day's work (the conversation was already mid-flow) - worth a
future session doing that check explicitly per CLAUDE.md's own rule if
this transcript is picked up cold.

--------------------------------------------------

FINAL REPO STATE - all work is on `main` (no side branches used),
fully pushed to origin AND deployed to the VPS (confirmed via
`git log --oneline -1` on both). Full test suite: 566/566 passing.
Commits this session, in order: 7c6de64fa, 473d05653, 3a0231b9f,
4f091b582, 855d2d611, 0c313ca35.

--------------------------------------------------

Next Session

1. Monday 24-Aug (next trading day): check the results of the
   one-time DepthUpdate WebSocket verification cron job (fires 09:20
   IST, writes data/depth_websocket_verification.jsonl on the VPS) -
   no automated report-back exists, this requires an explicit ask in
   this same conversation.

2. Monday 24-Aug, during real market hours: verify the chart
   timeframe selector, volume bars, and full-day candle history
   (400-candle cap) all work against real live data (21-Aug's own
   verification was blocked by repeated same-day deploys and Fyers
   going silent late in the day - see doc/21aug26_SESSION_LOG.md).

3. Revisit the consecutive-loss circuit breaker's N=2 parameter, the
   trailing-stop-loss idea, and the IV-filter idea once more real
   trading days have accumulated on the 6 new quote-based lock books
   plus the existing 2%-lock books - all three explicitly deferred
   this session for lack of data (3-4 trades / 1-2 trades is too few
   to trust any of these numbers yet).

4. Depth-based slippage finding from 21-Aug (LTP-based PnL overstating
   real fills by ~87-91%, round-trip spread ~19x the configured
   SPREAD_COST_PCT_NIFTY = 0.26%) is still an ESTIMATE resting on
   stale 5-min depth snapshots - the DepthUpdate WebSocket research
   above is the path to a real verified number; revisit once real-time
   depth data starts flowing.

5. Confirm NIFTY oi_footprint eventually takes a real trade (BANKNIFTY
   already has).

6. Compare the two original 2%-lock books, plus the 6 new quote-based
   lock books, against their unlocked siblings after a few more real
   trading days.

7. GitHub Actions queue-backlog finding (documented 21-Aug, not
   fixed) - revisit only if the user wants to; needs cron-job.org
   dashboard changes, out of scope for VPS work.

8. All items from doc/21aug26_SESSION_LOG.md's own "Next Session"
   list not already superseded above (sync_ticks_from_vps.py
   end-to-end exercise, off-machine backup, end-Sep-2026
   statistical-tools checkpoint).

9. strategy/fyers_options_oi_iv_combo.py's `_realized_volatility()`
   uses an invalid `period="30d"` key (not in fyers_data.py's
   PERIOD_TO_DAYS) - would raise ValueError if ever actually invoked
   live. Flagged this session, not fixed - worth a real fix.

==================================================

END OF SESSION
