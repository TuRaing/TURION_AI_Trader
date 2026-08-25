# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260825-001

--------------------------------------------------

Date

25-Aug-2026

--------------------------------------------------

REAL BUG - build_android_apk.yml ALSO MISSING --dart-define=GITHUB_PAT
(commit 13af3c667, "Fix build_android_apk.yml missing --dart-define=
GITHUB_PAT") - a THIRD build path hit by the same recurring class of
bug (previously only known to affect local `flutter build apk`
invocations, see 24-Aug's log). Claude triggered the GitHub Actions
workflow to build a fresh APK (containing yesterday's oi_footprint
quote-fix), downloaded the artifact, and installed it on the user's
phone via `adb install -r` - the user then reported the Fyers-login
screen showing "App was built without a GITHUB_PAT (--dart-define) -
the trigger cannot be sent." Root cause: `build_android_apk.yml` had
always run a plain `flutter build apk --release`, never passing the
token - unlike every local build this project has done, which always
remembered the flag. Fixed by adding
`--dart-define=GITHUB_PAT=${{ secrets.REPO_ADMIN_PAT }}` (reusing the
same fine-grained PAT secret `fyers_trigger.yml`'s own dispatch call
already uses, rather than creating a second secret for the same
token). Re-triggered the workflow, downloaded the new artifact,
reinstalled on the phone - user confirmed the error banner was gone.
Saved as a permanent memory (feedback_apk_build_dart_define.md) -
user's own explicit ask ("हे कायम लक्षात ठेव") after this bit a third
independent build path.

==================================================

CRYPTO (DERIBIT) OPTIONS PAPER-TRADING - SCOPED AND PLANNED, NOT YET
BUILT. User asked whether the bot could paper-trade BTC/ETH options
(Deribit) the same way it live-paper-trades NIFTY/BankNifty. Walked
through legality (no FEMA/tax exposure for paper trading, since no
real money/foreign account is involved) and technical feasibility
before any building. User's explicit constraints: (1) completely
separate from the existing NIFTY/BankNifty VPS - no new always-on
service on that 1vCPU/1GB machine until real-money trading starts
there (an already-established rule), and (2) reuse the EXISTING
RSI-momentum decide_fn unchanged first, only design a new signal if
that genuinely fails.

Entered plan mode; explored via a Plan agent and direct reads which
existing modules are genuinely asset-agnostic and reusable as-is
(backtest_live_engine.py's run_backtest()/run_live_check(),
event_driven_engine.py's rsi_momentum_decide_fn, live_tick_harness.
py's CandleAggregator for RSI, execution_backend.py, report/
firebase_realtime_sync.py's sync_portfolio()) vs what's genuinely new
(a Deribit REST/WebSocket data module with coin-to-USD premium
conversion, since Deribit quotes option premiums in BTC/ETH not USD;
a simpler CryptoTickRunner with no squareoff_time concept, since
crypto trades 24/7; a new mobile screen, since the existing VPS tab
hardcodes ₹ formatting and a Fyers-login button). Plan approved and
saved to a plan file for future reference.

Verified Deribit's real public API schema live (not guessed, matching
this project's established discipline) via direct REST calls:
`/public/get_index_price` (result.index_price, USD), `/public/get_
instruments` (real instrument_name/strike/option_type/expiration_
timestamp/quote_currency="BTC" fields), `/public/ticker` (mark_price/
best_bid_price/best_ask_price in BTC + index_price in USD in one
response).

Mid-session the user asked that this NOT live inside D:\TURION_AI_
Trader at all - cloned the same GitHub repo into a fresh, separate
local folder (D:\TURION_Crypto_Trader) instead, intending a new
`crypto-paper-trading` branch (not yet created). User then asked to
move this work to a NEW chat entirely, so a full copy-paste briefing
(plan-file location, folder, verified API facts, next step) was
handed off. No crypto code has been written yet.

==================================================

REAL LIVE INCIDENT - VPS OWNERSHIP BUG BLOCKED TODAY'S 08:00 IST
AUTO-DEPLOY, ~2 HOURS OF NO TRADING AT MARKET OPEN. User asked for a
market-open (9:16 IST) health check of the whole VPS - scheduled via
this session's own ScheduleWakeup (a cloud "schedule" routine was
tried first and abandoned again as the wrong tool - cloud routines
have no access to the local SSH key needed to reach the VPS, the same
constraint already documented 22-24-Aug).

Found live: all 3 systemd services showed "active" (not crash-looped,
0 restarts) but were functionally dead - journalctl showed a "Token
is expired" WebSocket disconnect at 07:47 IST (before market open),
followed by continuous "Please provide valid token" errors on every
retry through 09:17 IST. All 14 event-driven books showed 0 trades,
depth collection had stopped since ~07:22 IST.

User pointed out they had logged into Fyers at 7:00 AM - correctly.
Investigating why that fresh token never reached the running
processes surfaced the REAL root cause: `/var/log/turion-deploy.log`
showed today's scheduled 08:00 IST cron run of deploy.sh (which exists
specifically to restart all 3 services and pick up the morning's
login) had failed outright - "insufficient permission for adding an
object to repository database .git/objects" and finally "Permission
denied" trying to execute deploy.sh itself. `find /opt/turion/
TURION_AI_Trader -not -user turion` showed 319 files/directories had
become root-owned (including deploy.sh itself, which had also lost
its executable bit) - caused by Claude running git/deploy commands
directly as `root` over SSH throughout the prior day's session instead
of as the `turion` user the daily cron actually runs as. The `turion`
cron user could not write to those root-owned files, so every
scheduled deploy.sh run today failed silently until Claude's manual
intervention.

Fixed: `chown -R turion:turion /opt/turion/TURION_AI_Trader` + `chmod
+x deploy/deploy.sh`, manually restarted all 3 services (one transient
Fyers "request limit reached" 429 crash during the simultaneous
restart, self-recovered via the existing Restart=on-failure retry
within 10 seconds - no action needed), verified fixed by having
`turion` (not root) successfully `git pull` cleanly. All 3 services
confirmed active with zero errors since, depth collector back to
sub-2-second gaps within minutes. Saved as a permanent memory
(feedback_vps_root_ssh_ownership.md) - future VPS git/deploy
operations should run as `sudo -u turion` or re-chown after any manual
root-SSH session, and this class of symptom (token-expiry-looking
errors) should prompt checking file ownership/`turion-deploy.log`
FIRST, not just assuming a simple re-login will fix it.

==================================================

TICK LATENCY INVESTIGATED END-TO-END - REAL ROOT CAUSE FOUND, NOT A
SYSTEM PROBLEM. User asked for a full VPS status table (all 14 books'
today/total PnL, position) plus real measured latency, using the
existing tick_latency_ms() tool (strategy/tick_collector.py, built
20-Aug) against today's real tick archive: median 1,177 ms, P95
1,683 ms, max 2,157 ms, min 321 ms (exchange exch_feed_time to VPS
received_at).

User then asked WHY the number is this large. Investigated
systematically rather than guessing: (1) confirmed `received_at` is
captured at the very top of the raw WebSocket on_message() callback,
before any of this project's own processing - ruled out own-code
overhead; (2) confirmed via IP geolocation the VPS is physically in
Mumbai (Vultr) - same city as NSE, ruling out geography; (3) measured
raw ping VPS-to-Fyers at ~0.6 ms - ruling out network transit; (4)
captured a live raw Fyers SymbolUpdate WebSocket message directly
(not from memory/docs) and found `exch_feed_time`/`last_traded_time`
are BOTH whole-second Unix epochs with no sub-second field anywhere in
the message - confirmed across all 11,354 of today's archived ticks,
every single "timestamp" ends in ".000". Concluded the measured 1.2s
median is substantially a measurement artifact from this second-level
rounding, not real pipeline slowness - a statistical correction
(subtracting the ~500ms expected mean rounding bias from median/
percentile figures, not from min/max) puts the real median latency
closer to ~677 ms.

Web research (not part of this repo, informational) found Fyers'
marketing claims <10ms exchange-to-app latency - but this appears to
refer to their separate "TBT" (Tick-by-Tick) feed, not the standard
SymbolUpdate feed this project uses. Further research suggests TBT is
free (not paid, correcting an initial guess) and is currently
available specifically for NFO (NSE F&O) instruments - i.e. exactly
what this project trades - via a different WebSocket endpoint
(wss://rtsocket-api.fyers.in/versova, Protobuf-based). NOT YET
VERIFIED against Fyers' own official docs or this account's real
access - flagged as a real, worthwhile-but-unstarted follow-up, not
acted on this session (per this project's "verify before building"
rule, same discipline as the Deribit schema check above).

==================================================

FRESH DEPTH-BASED SLIPPAGE RE-CHECK (25-Aug, post-incident-fix) - ran
analyze_realtime_depth_slippage.py again on today's real trades: 34
matched, blended 11.1% overstatement (Rs -41,450 recorded vs
Rs -46,049 realistic). Broken out by category to avoid a misleading
single headline number (matching this project's established
discipline): oi_footprint_nifty (still LTP-based, not yet on the
24-Aug quote-fix) showed the same large/sign-flipping gap as previous
days (14 trades, Rs 9,859 swing, profit->loss sign flip); the 4 plain
RSI books showed a small, consistent ~13% gap; the 6 quote-based lock
books showed the gap DIRECTION REVERSED today (recorded losses worse
than realistic) - flagged explicitly as small-sample noise (only 2
trades/book today), not a contradiction of the established finding,
consistent with the project's ongoing "need ~1 week of data before
trusting a daily number" position.

==================================================

Status

🟢 Stable

Current Version

v0.0.61

Next Version

v0.0.62

--------------------------------------------------

Next Session

1. Verify Fyers' TBT (Tick-by-Tick) feed against official docs/real
   account access (myapi.fyers.in) - if genuinely free and available
   for NFO options, it could fix both today's rounding-artifact
   measurement problem and the real ~700ms latency itself. Not started
   this session beyond web research.

2. Crypto (Deribit) paper-trading - plan approved and saved, repo
   cloned to D:\TURION_Crypto_Trader, Deribit's real API schema
   verified - but the actual `crypto-paper-trading` branch, strategy/
   deribit_data.py, and CryptoTickRunner have NOT been started. Continue
   in the new chat the user asked for, using the handoff briefing
   already given.

3. Port the oi_footprint quote-fix (built 24-Aug, oi_footprint_quote_
   decide_fn) results once the 2 new books (oi_footprint_quote_
   eventdriven_nifty/banknifty) accumulate real trades - 0 so far as of
   this session, since oi_footprint's OI-buildup signal hadn't fired
   for either new book yet.

4. Re-run the depth-slippage analysis after ~1 week of data (per the
   project's own repeated conclusion) before trusting any single day's
   quote-based-books percentage - today's reversed-direction result on
   the quote-lock books is exactly the kind of noise this rule exists
   to catch.

5. Consider chown-ing the VPS repo (or switching to `sudo -u turion`
   for all future manual git/deploy operations) as a standing habit,
   not a one-off fix - see feedback_vps_root_ssh_ownership.md.

6. Carried over from 24-Aug, still open: turion-tick-collector lacks
   turion-event-driven's auto-retry cron lines; sync_ticks_from_vps.py
   off-machine backup exercise never run; end-Sep-2026 statistical-
   tools checkpoint still ~5 weeks out.

==================================================
