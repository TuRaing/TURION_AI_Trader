# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260820-001

--------------------------------------------------

Date

20-Aug-2026

--------------------------------------------------

HEALTH-CHECK SCHEDULING - TRIED SESSION-CRON, THEN GITHUB ACTIONS,
THEN PAUSED PENDING VPS - continuation of 19-Aug's report/market_
checks.py build (see doc/19aug26_SESSION_LOG.md). Today's session
tried actually running it on demand and hit a real gap: run_pre_
market_check.py's Fyers-token check needs a LOCAL desktop login
(`python -m strategy.fyers_auth`, writes to this machine's own .env) -
completely separate from the mobile app's login, which updates the
FYERS_ACCESS_TOKEN GitHub Actions secret instead (confirmed by reading
strategy/github_secrets.py) and never touches local .env. Neither
local .env token had ever been read before today, because every one
of this project's 60+ modules runs on GitHub Actions, never on this
desktop - this was the first thing that needed live data run locally,
which is why the gap never surfaced before.

While checking GitHub for whether the morning's mobile login had
worked, found (and flagged, not fixed - see below) a real unrelated
bug: the "Fyers Login Trigger" workflow's retry-rebase logic breaks
when a push conflict retry hits leftover unstaged changes ("cannot
pull with rebase: You have unstaged changes"), losing that run's
secondary state commit even though the actual Fyers login step itself
succeeded fine. Filed as a background task rather than fixed inline
(out of scope for the health-check work) - fix is `git pull --rebase
--autostash` instead of the current plain `git pull --rebase`, same
pattern likely duplicated across other workflow YAML files.

Considered moving the check to run AS a GitHub Actions workflow
instead of locally (reuses the existing secret, no separate login,
survives this session closing) - user initially agreed, started
reading existing workflow YAML (.github/workflows/fyers_trigger.yml,
fyers_scheduled_check.yml) as a template, then the user reconsidered
mid-build and asked to just wait for the VPS instead of building
either the session-cron or the GitHub-Actions version.

RESULT: all 4 of yesterday's CronCreate jobs deleted. report/market_
checks.py + run_pre_market_check.py + run_market_check.py remain
committed, tested (17/17), and working when run directly - but NOTHING
IS SCHEDULED anywhere. Real scheduling stays parked until the VPS
(10-Sep track) exists. doc/PROJECT_STATUS.md's health-check entry
updated to reflect this explicitly, so a future session doesn't assume
these checks are still running or try to rebuild the GitHub-Actions
version without asking first.

Also same session: made a local backup of the repo (excluding
regenerable build/dist/mobile_app-build output, ~286MB of the real
~1.4GB folder) to D:\TURION_AI_Trader_19082026_backup_1 - confirmed
.env is included. Off-machine copy (OneDrive/USB) deferred - OneDrive
on this machine is installed but not signed in, and the user doesn't
have a spare pendrive on hand right now.

--------------------------------------------------

OVERNIGHT-CARRY PATTERN - CONFIRMED ACROSS ALL BOOKS, ONE SEPARATE
NEW FINDING - user asked to verify the known simple_st1_slcap_nifty
-Rs 1,23,027.15 trade (18-Aug entry 14:56:05, 19-Aug exit 08:33:03,
Stop Loss, 61.5x the intended cap - the date-blind-squareoff bug's
signature case, fixed 19-Aug) and check every other book for the same
pattern. Scanned every reports/*_portfolio.json's Closed Trades for
Entry-date != Exit-date, then ran report/market_checks.py's
detect_unusual_trade() on each.

CONFIRMED: exactly 10 OTHER books hit the identical 18-Aug-evening ->
19-Aug-08:31-08:33-exit pattern, matching 19-Aug's session log claim
of "10 other books" exactly - simple_st1_banknifty (-3,478, 4.1x),
simple_st1_slcap_banknifty (-10,912, 5.5x), st2_banknifty (-4,270,
5.0x), st2_nifty (-17,538, 50.1x), st2_slcap_banknifty (-5,284, 3.8x),
st2_slcap_nifty (-16,960, 50.1x), st3_banknifty (-11,056, 9.8x),
st3_nifty (-11,096, 50.2x), st3_slcap_banknifty (-6,494, 3.9x),
st3_slcap_nifty (-45,202, 50.0x). All already covered by the 19-Aug
squareoff.py fix - no new action needed on these.

NEW, SEPARATE FINDING - reports/fyers_options_portfolio.json (the
original single-strategy prototype, strategy/fyers_options_paper_
trading.py, "Strategy"/"Index" fields empty unlike every newer book):
one closed trade, Entry 2026-08-08 17:38:18 (a SATURDAY) -> Exit
2026-08-11 09:17:03, Net PnL -Rs 56,097.46 (30.3x the intended cap).
Checked further: this book's Entry Times on 6-Aug range from 14:41 to
20:58 IST (NSE closes 15:30) and include a second Saturday entry
(15-Aug 23:33). strategy/fyers_options_paper_trading.py has NO
day-of-week or market-hours gating anywhere in the module (confirmed
by reading it) - unlike every newer strategy module. This is a
DIFFERENT, NOT-YET-FIXED bug (the engine can apparently open/manage
positions from stale data outside real trading hours entirely,
not just fail to detect an already-past squareoff time) - NOT covered
by the 19-Aug squareoff.py fix, since that fix only addresses
DETECTING a past squareoff, not preventing entries when the market is
closed to begin with. Flagged as a background task, not fixed inline
(this old engine may be deprecated/superseded by fyers_multi_strategy_
options.yml - worth confirming that before spending fix effort on it).

CONFIRMED DEPRECATED, SAME SESSION: queried the GitHub API for
fyers_options_watch.yml's run history - last actual run was
2026-08-06T09:59:14Z, nothing since (14 days dead as of today).
cron-job.org's external trigger for it was evidently removed around
06-Aug when fyers_multi_strategy_options.yml took over. No fix needed
on dead code - added deprecation comments to both strategy/fyers_
options_paper_trading.py and .github/workflows/fyers_options_watch.yml
instead, left in place (not deleted) since reports/fyers_options_
portfolio.json is still real historical data. Background task
dismissed.

--------------------------------------------------

VPS ACTUALLY PROVISIONED + FIREBASE PART A COMPLETED - SAME DAY,
TIMELINE ACCELERATED FROM 10-Sep TO 20-Aug: user changed their mind
mid-session (after initially declining, twice, to accelerate VPS/
GitHub-Actions work earlier today) and decided to just do the real
Vultr signup + VPS setup + Firebase Part A right now, walked through
live, screenshot by screenshot.

VULTR SIGNUP (real money, user's own clicks throughout - Claude never
touched payment fields, per this project's own safety rules):
- Card linking hit two real errors: "$0 deposit" linking denied (many
  Indian cards reject zero-value auth), then a genuine $5 charge also
  denied ("denied by the credit card issuer") even with international
  transactions enabled on a debit card - root cause never fully
  confirmed (likely bank-side 3D-Secure/OTP handling gap with Vultr's
  gateway), worked around by using PayPal instead - succeeded.
- Plan: Shared CPU -> High Performance -> AMD, vhp-1c-1gb-amd, $6/mo,
  Mumbai. Automatic Backups disabled (server is fully disposable - all
  real state lives in GitHub/Firebase, not on the VPS disk - saves
  $1.20/mo for zero real risk).
- SSH key UI moved since the Go-Live Runbook artifact was written -
  not under Account or the instance-creation dropdown, actually under
  Orchestration -> SSH Keys (console.vultr.com/sshkeys/). Runbook is
  now further out of date than previously known (see below).
- OS: Ubuntu 26.04 LTS (newer than the runbook's 22.04 - fine, deploy/
  files are generic systemd/apt, no version-specific assumptions).
- Server created (65.20.78.253, Mumbai), came up "Stopped" initially
  in the dashboard (which was also generally slow/laggy) - verified
  directly via SSH instead of trusting the dashboard, which already
  showed it fully booted and reachable.

RUNBOOK ARTIFACT CONFIRMED STALE IN TWO PLACES, same session (28b820c3
-da1b-4060-836b-4112991569e7, "Engine Go-Live Runbook"): (1) Part B
still named DigitalOcean/AWS Lightsail as the provider, when Vultr
Mumbai was already decided 18-Aug - corrected live rather than
followed. (2) Part A's "you already have a Firebase project... 
FIREBASE_SERVICE_ACCOUNT is already a GitHub secret" line was
MISLEADING - a project did already exist (turion-ai-trader), reused
correctly, but the user had never actually touched Firebase Console
before and said so - real GitHub Actions log evidence (see below)
showed only FIREBASE_DATABASE_URL was actually missing at the time,
not both, contradicting an earlier same-session guess that both were
missing. The artifact itself was NOT edited this session - flagging
here so a future session double-checks it before trusting it again
rather than re-discovering the same two staleness gaps.

FIREBASE PART A - DONE: reused the existing "TURION AI Trader" project
(turion-ai-trader) rather than creating a new one. Realtime Database
created - Mumbai (asia-south1) is not an available RTDB region,
Singapore (asia-southeast1) is the closest real option and was used
(matches the runbook's own hedge about this). Locked-mode security
rules published from firebase/database.rules.json unchanged. Database
URL: https://turion-ai-trader-default-rtdb.asia-southeast1.
firebasedatabase.app - added as the FIREBASE_DATABASE_URL GitHub
Actions secret (user's own manual step, Claude has no secrets-write
PAT locally). Generated a NEW service account private key (Project
Settings -> Service Accounts) specifically for the VPS's local .env,
rather than trying to recover the existing GitHub-secret one (which
can never be read back - write-only by design).

REAL BUG FOUND AND FIXED - systemd EnvironmentFile mangles embedded
`\n` escapes in unquoted values: the service-account JSON's private_
key field contains ~28 literal `\n` escape sequences (PEM line
breaks). Writing `KEY=<raw minified JSON>` into a systemd
EnvironmentFile= target caused systemd's own parser to silently
convert each into a real newline byte, corrupting the value by
exactly 28 characters (confirmed via a live diagnostic: `systemd-run`
with the same EnvironmentFile, printing os.environ length/content
directly - 2318 chars delivered vs 2346 in the source file) - this
surfaced as a cryptography/PEM parse error ("InvalidData, offset
1652"), not a JSON parse error, which was the confusing part.
FIX: wrap the whole value in single quotes in the .env file
(`KEY='<json>'`) - systemd's parser does not interpret escapes inside
single-quoted values (matches POSIX shell single-quote semantics).
Re-verified via the same systemd-run diagnostic: exact length
preserved (2346), valid JSON, project_id readable. Not a bug in any
of this repo's own Python code - purely a systemd EnvironmentFile
quoting gotcha, worth remembering for any future secret with embedded
newlines delivered this way.

FYERS DAILY LOGIN/AUTH RATE LIMIT DISCOVERED (real, not code): Fyers'
own generate-authcode/access-token exchange has a per-day cap. Today's
morning mobile-app login (before Firebase was configured, so it never
synced to Firebase) plus a same-day re-login attempt (after Firebase
was configured, meant to complete the sync) together hit "API Limit
exceeded per day" (Fyers error -353) - the re-login's own auth
exchange failed outright. A third attempt (this session's own local
desktop login via `python -m strategy.fyers_auth`, needed separately
since the local .env token store is completely independent from both
the GitHub-secret and Firebase-synced tokens) DID succeed for the
auth-code exchange itself, but the subsequent verify_connection()
profile-endpoint call hit the SAME daily limit on a different Fyers
endpoint - confirms local desktop and mobile-app logins are genuinely
separate credential paths that can independently succeed/fail.
NET RESULT: local desktop Fyers checks now work (today's date). The
VPS still has NO live token today - Firebase-side sync needs
TOMORROW's first mobile login of the day to actually go through
cleanly (Firebase is now properly configured, so it should sync on
the very first attempt rather than needing a second one).

VPS SETUP COMPLETED (Runbook Part B, B6-B16) - all done live via SSH,
verified after each step:
- B6-B9: prerequisites, `turion` service user (nologin), repo clone,
  venv + all dependencies (92 packages, clean imports).
- B10-B11: .env (fixed per the systemd bug above), ownership, 600
  permissions.
- B12: scoped passwordless sudo - exactly 2 systemctl commands,
  syntax-verified with visudo -c.
- B13: both systemd units installed + enabled. Manually started once
  to confirm the "no token yet -> clean exit 0" path works exactly as
  designed (not a crash) - this is expected/correct given no VPS
  token exists yet, not a failure.
- B14: verified via systemctl status + journalctl output directly.
- B15: both cron entries added for the `turion` user (08:00 IST daily
  deploy, 08:00-09:59 IST 5-min retry-start window).
- B16: deploy.sh dry-run succeeded as the `turion` user (deploy.sh
  itself needed `chmod +x` first - wasn't executable after git clone,
  fixed inline).
- B17 (crash-alert live test) and B18 (real live run) explicitly NOT
  done yet - both need a real access_token, which needs tomorrow's
  first login. Do not skip these once a token is available - they're
  the only remaining unverified pieces of the whole event-driven/VPS
  build.

VPS SECURITY HARDENING - user's own follow-up ask, same session, done
proactively rather than left as a known gap:
- Found via direct inspection (not assumed): password SSH auth was
  ENABLED (Vultr's own cloud-init default, sshd_config.d/50-cloud-
  init.conf) and root permitted full password login
  (sshd_config's PermitRootLogin yes) - a real, meaningful gap since
  Vultr also displays a root password in its own dashboard.
  ufw (port 22 only) and unattended-upgrades were ALREADY on by
  Vultr's own defaults - not this session's doing, just verified.
- FIXED: PermitRootLogin -> prohibit-password (key-only root login,
  not password), PasswordAuthentication -> no (key-only for every
  user). Verified live key-based access still worked immediately
  after `systemctl reload ssh` - before considering it safe, not
  after, to avoid a real lockout risk.
- Installed and enabled fail2ban with a basic sshd jail (5 attempts /
  10 min window -> 1 hour ban) - confirmed active and monitoring via
  fail2ban-client status.

--------------------------------------------------

ATM TICK-BY-TICK COLLECTOR BUILT AND DEPLOYED - follow-up to 15-Aug's
"TICK-BY-TICK DATA STORAGE" research (discussion only, no code at the
time) - now buildable since a real VPS exists to hold the persistent
WebSocket. User's own explicit scope choice: ATM only (not OTM, not
the full chain) - confirmed this matches every live strategy in the
project (all trade ATM), and walked through the ATM-vs-ITM-vs-OTM
reasoning (Gamma/% sensitivity, capital efficiency) as part of that
discussion.

strategy/tick_collector.py (pure, tested - atm_has_drifted(),
tick_log_filename(), format_tick_record(), filter_completed_
filenames()) + run_tick_collector.py (VPS WebSocket entry point,
subscribes to spot/ATM-CE/ATM-PE for both indices via event_driven_
runner.py's existing pick_atm_symbols(), re-picks ATM every 15 min and
re-subscribes on drift - improves on the trading engine's own known
"ATM picked once at startup" limitation, just for this collector).
Estimated size worked through with the user: ~40-100 MB/day, ~1-2.4
GB/month at real narrow-scope tick rates - comfortably fits the VPS's
own 25GB disk for many months even with no upload at all.

STORAGE DESTINATION - user's own choice, deliberately deferred cloud
spend: skip Backblaze B2 for now (run_tick_upload.py exists, gracefully
no-ops until B2 credentials exist), instead sync_ticks_from_vps.py
pulls each completed day down to THIS laptop over SCP (verifies file
size before deleting the VPS copy) - free for as long as it's needed,
matches [[feedback_data_driven_patience]]. Both destinations share one
rule (filter_completed_filenames()) for "what counts as a completed
day" so they can never drift apart if B2 is added later.

Deployed: deploy/turion-tick-collector.service added (mirrors turion-
event-driven.service), deploy.sh updated to restart BOTH services on
every daily deploy (SERVICE_NAMES, was a single SERVICE_NAME). Pulled
onto the VPS, installed, enabled, started - confirmed the exact same
clean "no token yet, exiting" behavior as the trading engine (correct,
not a failure).

HEALTH-CHECK SCRIPTS ALSO DEPLOYED TO THE VPS - completing what was
explicitly paused 19-Aug pending the VPS. Real gap found and fixed
first: run_pre_market_check.py/run_market_check.py's _headers() only
knew how to read a LOCAL .env token (get_access_token()) - the VPS has
no local Fyers login of its own, only a Firebase-sourced one. Added
_resolve_access_token() to both files (tries report/firebase_realtime_
sync.py's fetch_access_token() first, falls back to the local .env
token) so the exact same files work unchanged on both the VPS and this
desktop. Also added FYERS_APP_ID to the VPS's .env (needed for the
Authorization header regardless of token source - not sensitive, the
same client_id already visible in the plain-text OAuth login URL).

Verified manually on the VPS before trusting the cron: run_pre_market_
check.py correctly showed "token NOT ready" (accurate - no login yet),
run_market_check.py correctly fell back to scanning real reports/*.json
data (already present via the VPS's own git checkout) and found the
same real unusual-trade pattern this session found earlier by hand.

Cron installed for the `turion` user (all times IST, converted to the
VPS's UTC clock, Mon-Fri): pre-market 08:43, running-market every 30
min 08:45-15:15, closing checks at 15:30 AND 15:45 (user's own explicit
ask for the second one, added after the rest was already running).
This is now FULLY independent of any desktop session - the exact
limitation flagged in yesterday's (19-Aug) health-check entry no longer
applies once the VPS took over.

--------------------------------------------------

Next Session

1. FIRST THING once the user has done today's/tomorrow's morning Fyers
   login: check GitHub Actions' "Fyers Login Trigger" run for "Shared
   today's token via Firebase Realtime Database." (not the generic
   skip message), then SSH to 65.20.78.253 and check `systemctl status
   turion-event-driven` / `journalctl -u turion-event-driven -f` -
   this is B17 (crash-alert test, `systemctl kill --signal=SIGKILL`)
   and B18 (real live run) from the Go-Live Runbook, still the only
   unverified pieces of the whole VPS build. Same first-login moment
   also unblocks and should be checked for: `systemctl status turion-
   tick-collector` (should start producing real ticks in data/ticks/)
   and the health-check crons' /var/log/turion-health-check.log
   (should start showing "token ready" instead of "NOT ready").

2. Once a few real days of tick data exist: run sync_ticks_from_vps.py
   from this laptop to pull them down, confirm the size-check/delete
   logic actually works end-to-end (not yet exercised - no real files
   existed on the VPS when it was written). Revisit whether/when to
   set up Backblaze B2 (run_tick_upload.py already exists, unused).

3. The Go-Live Runbook artifact (28b820c3-da1b-4060-836b-4112991569e7)
   is now confirmed stale in the two places noted above (provider
   name, Firebase-already-configured claim) - worth a proper update
   pass once the VPS is fully live-verified, rather than patching it
   piecemeal mid-walkthrough again next time.

4. Off-machine backup copy (OneDrive sign-in, or a USB/pendrive once
   the user has one) - still open, unchanged from earlier today.

5. Low-priority, still flagged not fixed: the git-rebase-retry bug in
   .github/workflows/fyers_trigger.yml (`git pull --rebase` ->
   `--rebase --autostash`) - a background task was spawned for this
   earlier same session, check if it was picked up.

6. DONE, same session - see "VPS ACTUALLY PROVISIONED", "VPS SECURITY
   HARDENING", "ATM TICK-BY-TICK COLLECTOR", and "HEALTH-CHECK SCRIPTS
   ALSO DEPLOYED" above. The VPS itself (Runbook Part B, B6-B16),
   Firebase Part A, the tick collector, and all 3 daily health checks
   are ALL live and cron-scheduled on the VPS now - fully independent
   of any desktop session. Only B17/B18 (needs a live token) remain.

==================================================

END OF SESSION
