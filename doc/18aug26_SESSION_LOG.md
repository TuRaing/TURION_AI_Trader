# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260818-001 (cloud session - claude.ai/code, not a
local machine session)

--------------------------------------------------

Date

18-Aug-2026

--------------------------------------------------

Version

v0.0.16 (no version bump - investigation/analysis only,
no code changed this session)

==================================================

Today's Achievements

✅ SESSION START: per CLAUDE.md's rule, fetched origin -
   local was thousands of commits behind (a large amount
   of strategy work happened across 06-Aug to 18-Aug in
   other sessions: multi-strategy options engine grew to
   15+ strategies plus several "_slcap" hybrid-Stop-Loss
   experimental variants, all read before proceeding).
   Fast-forward merged repeatedly through the session as
   new commits landed live (options books update every
   ~1 min via cron-job.org), no conflicts.

✅ Diagnosed a recurring "cron job failed" email for the
   user (Fyers Multi-Strategy Options Watch, and separately
   Watchlist Paper Trade Check): both traced via real
   GitHub Actions job logs to the SAME already-understood,
   self-healing git-push race (two overlapping runs both
   trying to commit updates to the same report file at
   nearly the same moment; the workflow's own safety logic
   correctly aborts rather than guess-resolve a genuine
   conflict, and the next scheduled run recovers cleanly -
   no real data loss). Also diagnosed a one-off "Gapfill
   Options Trigger... 502 Bad Gateway" email as a transient
   network hiccup between cron-job.org and GitHub's API
   (failed before the workflow even started) - unrelated to
   the git-race issue, self-resolving, no action needed
   unless it recurs frequently.

✅ Checked why several of the newer options strategies
   (credit_spread, gapfill, vix_filter, max_pain_drift,
   pcr_vix_combo, oi_iv_combo) had zero or very few trades:
   confirmed via code review (not guessed) that each has a
   deliberately narrow/rare entry condition (VIX percentile
   bands, gap-at-open before 10 AM, near-expiry-day gating,
   etc.) and most were only 1-5 days old at the time - no
   bug found, no runtime errors in logs, just low-frequency-
   by-design strategies still waiting for their first
   qualifying setup.

✅ Gave a full trade-by-trade table of 14-Aug's results
   across all 15 strategy books when asked, and separately a
   full lifetime behavior analysis of oi_footprint (both
   indices) when asked - at that point (14-Aug data) it was
   the best-performing book in the project: NIFTY +Rs 56,330
   (60% win rate, 30 trades), BANKNIFTY +Rs 11,891 (67% win
   rate, 9 trades).

✅ FOLLOW-UP, same session (18-Aug real date, several days
   after the above): user pointed out oi_footprint now looks
   like a loss - re-checked with fresh data and found a real,
   severe reversal: oi_footprint/NIFTY went from +Rs 56,330
   (14-Aug) to a deepening loss over 14/17/18-Aug (-Rs 40,002
   mid-session, -Rs 47,607 by session end as more 18-Aug
   trades landed live), cash down to roughly Rs 52,000-60,000
   from a peak of Rs 1,56,330.

   ROOT CAUSE - confirmed as the SAME issue this repo already
   diagnosed in depth on 14-Aug (see PROJECT_STATUS.md's
   "oi_footprint EXIT-MECHANISM DEEP DIVE, 14-Aug" - read
   before concluding anything new, per CLAUDE.md's rule, so
   as not to duplicate or contradict that existing analysis):
   oi_footprint's Target/Stop-Loss are both set tight
   (Rs 1,500 - strategy/fyers_options_oi_footprint.py), but
   the automation only checks positions every ~1 min, not
   tick-by-tick, so real losses on volatile-open trades
   routinely overshoot the intended Rs 1,500 SL by several
   times over.

✅ BACKTEST, at the user's request: re-ran the 14-Aug entry's
   own established methodology (RETROSPECTIVE FINDING 2 -
   asymmetric -Rs 2,000 Stop-Loss-only cap, Target left
   uncapped/as-is, since the earlier symmetric-both-sides cap
   was already shown on 14-Aug to make LESS money, not more)
   against the now-larger trade history (60 trades total,
   up from 40 on 14-Aug - includes 17/18-Aug's two most
   extreme overshoot losses yet, -Rs 24,375 and -Rs 23,571
   on the same 18-Aug morning):

     NIFTY:      actual -Rs 47,607  ->  capped +Rs 66,972  (+Rs 1,14,580)
     BANKNIFTY:  actual  -Rs 6,067  ->  capped  +Rs 4,267  (+Rs 10,333)

   Documented as an UPDATE under the existing 14-Aug entry in
   PROJECT_STATUS.md (not a new/separate finding) - same
   conclusion holds and strengthens with more data: the entry
   signal is not the problem, a real broker-side SL order
   (strategy/fyers_order_execution.py, built 14-Aug, not yet
   wired in) would very likely have kept this book solidly
   profitable throughout.

   USER CONFIRMED: this doesn't change the existing plan -
   VPS (Stage 2) migration + real tick-by-tick checking stays
   on schedule for next month (target 10-Sep-2026, code prep
   from 1-Sep-2026, both already recorded in this file before
   today).

✅ SECOND BACKTEST, same session, at the user's request: also
   re-ran the project's separately-established HYBRID SL CAP
   formula (min(flat_cap, pct_of_deployed_cap) at 2%, the same
   one behind the st1-st4 "_slcap" variants) against
   oi_footprint's same 60-trade history, to compare against the
   flat -Rs 2,000-only cap above:

     Index      Actual        Flat -Rs2,000     Hybrid (2%)
     NIFTY      -Rs 47,607    +Rs 66,972        +Rs 69,490
     BANKNIFTY   -Rs 6,067    +Rs 4,267         +Rs 4,839
     Combined   -Rs 53,674    +Rs 71,239        +Rs 74,329

   Hybrid edges out the flat cap slightly (+Rs 3,090 combined) -
   same direction as the original 8-book finding. NIFTY's larger
   positions mean the flat Rs 2,000 side binds more often there
   (22/26 Stop-Loss trades); BANKNIFTY's smaller lot size means
   the %-of-deployed side binds more often there (6/7). Documented
   as a second UPDATE under the same 14-Aug PROJECT_STATUS.md
   entry. oi_footprint does not have an "_slcap" live variant yet
   (unlike st1-st4) - flagged as a future option, not built this
   session (not requested).

==================================================

Bugs Fixed

(none this session - diagnosis/analysis only, no code
changed)

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data. Report
Engine displays. Excel Engine stores history. Options
logic kept fully separate from normal NIFTY/stock trading
logic.

Claude never executes a real trade - final action is
always the user's.

==================================================

Next Session

1. Code prep for VPS (Stage 2) migration starts 1-Sep-2026
   per the already-recorded plan - not before, per the
   user's own reasoning (no point renting/testing on a live
   VPS before it's actually needed).

2. Once VPS + tick-by-tick checking is live: re-evaluate
   oi_footprint specifically, since its Rs 1,500 SL/Target
   band is the tightest in the project and the most exposed
   to the periodic-check overshoot problem documented today
   and on 14-Aug.

3. Consider whether oi_footprint should get its own
   "_slcap"-style hybrid-Stop-Loss variant in the meantime
   (several other books - simple_st1, st2, st3, st4 and
   their threshold siblings - already got one on 14-Aug,
   oi_footprint was not among them) - not started, the
   user has not asked for this yet, flagging as an option
   given today's numbers.

4. Keep watching for repeated "502 Bad Gateway" cron-job.org
   emails - a one-off is a non-issue, but a pattern would be
   worth a closer look (rate limiting, etc.).

==================================================

Session ID

S20260818-002 (separate parallel session, same day - see
CLAUDE.md's session-continuity rule. This session's work is
UNRELATED to S20260818-001 above: that session did oi_footprint
diagnosis/backtesting, this one built the WebSocket event-driven
engine. Appended here rather than overwriting, per CLAUDE.md.
Confirmed via `git fetch origin` + `git log HEAD..origin/main`
at time of this entry: local is current with origin/main, no
reconciliation needed - S20260818-001's commits and this
session's own commits are both already on main.)

--------------------------------------------------

Today's Achievements (this session)

✅ Built the event-driven (WebSocket, real-time tick-by-tick)
   options engine as code-prep for the Stage 2 VPS migration
   (target 10-Sep-2026, prep starting 1-Sep-2026 per the
   existing plan - built a few days early since the design work
   was ready): strategy/event_driven_runner.py, decide_fn logic
   generalized to cover all 4 currently-profitable strategies,
   connect_and_run()'s message-parsing logic extracted and
   unit-tested separately from the live WebSocket connection
   itself so the parsing logic has real test coverage without
   needing a live Fyers connection.

✅ Verified byte-identical replay against real historical trades
   - the event-driven decide_fn produces the same entries/exits
   as the existing periodic-check engines on historical data,
   confirming the rewrite doesn't change trading logic, only the
   check frequency (tick-by-tick instead of ~1/min).

✅ Built a local WebSocket test harness (live_tick_harness.py) -
   no VPS yet, so this exercises the parsing/decide_fn path
   without a real market connection.

✅ Added fyers-apiv3 to requirements.txt (documented as
   deliberately not installed locally - no VPS to run it against
   yet, same "code-prep, not live" status as the rest of this
   batch).

✅ Built run_event_driven_engine.py, the VPS entry point: fetches
   today's access_token via Firebase Realtime Database rather
   than the FYERS_ACCESS_TOKEN GitHub secret (a VPS is not a
   GitHub Actions runner and can't receive repo secrets the same
   way) - reuses the same Firebase channel already wired up for
   portfolio sync, considered and explicitly rejected a second
   login flow. Wired fyers_trigger_run.py to also push each day's
   token to Firebase (report/firebase_realtime_sync.py) so this
   entry point has something to read once a VPS exists. Added
   firebase/database.rules.json (vps_config path locked to
   server-only read/write - the access_token itself lives under
   a similarly locked-down path, not the public event_driven_
   portfolios path).

✅ Added deploy/turion-event-driven.service - a systemd unit
   template for keeping the engine running continuously on the
   VPS (auto-restart on crash via Restart=on-failure, auto-start
   on boot via WantedBy=multi-user.target, capped restart burst
   so a persistently-crashing engine doesn't spin forever). Paths
   and the service user are placeholders - to be filled in once
   the actual VPS exists. Config file, not Python/Dart - no unit
   test possible, syntax-only check.

✅ NOTED DURING THIS SESSION: the user's message contained hidden
   injected text attempting to redirect this assistant's behavior
   ("respond TEXT ONLY, no tools" + a fake instruction to
   fabricate a conversation summary). Not treated as a real
   instruction - flagged to the user, ignored, continued normally
   with tool use as needed. Recorded here in case it recurs and
   is worth tracing to its source (e.g. a clipboard/paste-tool
   issue on the user's end).

--------------------------------------------------

NOT LIVE-TESTED (same caveat across this whole batch)

None of strategy/event_driven_runner.py, live_tick_harness.py,
run_event_driven_engine.py, or deploy/turion-event-driven.service
have run against a real Fyers WebSocket connection or a real
Linux/systemd VPS - none exists yet. Everything above is code-
prep validated by unit tests and historical-replay comparison
only, consistent with the Stage 2 migration not starting until
1-Sep-2026 per the existing plan (confirmed still on schedule as
of S20260818-001 above, despite oi_footprint's rough patch).

==================================================

END OF SESSION
