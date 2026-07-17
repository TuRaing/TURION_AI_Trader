# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260717-001

--------------------------------------------------

Date

17-Jul-2026

--------------------------------------------------

Version

v0.0.7 → v0.0.9

==================================================

Today's Achievements

✅ News Engine (strategy/news_engine.py) - free RSS
   feeds (Moneycontrol + Economic Times, no API key),
   keyword-lexicon sentiment scoring (same transparent
   rule-based philosophy as the AI Decision Engine)

✅ Option Chain Engine (strategy/option_chain_engine.py)
   - implements Engine 9 from the spec doc (PCR, Max
   Pain, Call/Put Writing, IV, Confidence) against the
   NSE public option-chain API. Degrades gracefully -
   returns {"Available": False, "Reason": ...} instead
   of crashing when NSE blocks the request (the
   long-documented datacenter-IP 403 block)

✅ Options Decision Engine (strategy/options_decision_engine.py)
   - decides BUY CE / BUY PE / NO TRADE for NIFTY /
   BANKNIFTY intraday by combining index price-action
   bias with the Option Chain Engine. Kept fully
   separate from equity signal_engine / paper_trading,
   per the project's options-isolation rule

✅ Best Trade Engine (strategy/best_trade_engine.py) -
   ranks every cleared Nifty 50 stock candidate and
   both index options candidates on one confidence
   scale (with a news-agreement bonus/penalty), then
   locks the single highest-probability intraday pick
   for the day, plus a top-5 shortlist for context

✅ daily_best_trade.py - new orchestration script
   wiring Watchlist Scanner + News Engine + Option
   Chain Engine + Options Decision Engine + Best
   Trade Engine → Report Engine → Telegram / Excel
   ("Best Trade" sheet, report/excel_report.save_best_trade)

✅ .github/workflows/best_trade_report.yml - new
   scheduled workflow, 10:00 IST Mon-Fri (45 min
   after NSE open)

✅ 29 new pytest unit tests (news_engine,
   option_chain_engine, options_decision_engine,
   best_trade_engine - all pure logic, fixture-driven,
   no network) - 74 total tests passing (was 45)

✅ Verified daily_best_trade.py runs end-to-end
   without crashing when both yfinance and the news/
   option-chain sources are blocked (this dev sandbox's
   proxy 403s Yahoo Finance, NSE, and the RSS feeds) -
   confirms the graceful-degradation design works as
   intended rather than assuming it would

✅ [Same day, follow-up] Best Trade Paper Trading
   (strategy/best_trade_paper_trading.py) - the daily
   locked pick, if it's an equity trade, now opens as a
   real intraday paper position (its own portfolio file,
   reports/best_trade_portfolio.json, kept fully separate
   from the existing swing-style watchlist paper trading
   in strategy/paper_trading.py - that working module was
   not touched) and force-closes before market shut via
   a new square_off_best_trade.py script + .github/
   workflows/best_trade_squareoff.yml (15:15 IST, 15 min
   before NSE close) - at Stop Loss/Target if already
   breached, otherwise at the current price ("Intraday
   Square-Off"). This was a direct fix to the gap the
   user flagged: without this, a locked pick would have
   silently carried over to the next day like the
   watchlist scanner's positions do. Index option (CE/PE)
   picks are still recommendation-only, by design - no
   reliable live premium feed exists to mark P&L against.

✅ 11 more pytest tests (test_best_trade_paper_trading.py,
   pure logic - open/square-off for both BUY and SELL
   directions, missing-file/round-trip file I/O) - 85
   total tests passing

✅ [Same day, second follow-up] Best Trade Report now
   runs every ~30 min through market hours (~09:35-14:05
   IST, offset :05/:35 past the hour) instead of once at
   10:00 IST - user asked "will it only check at 10, or
   during market hours?" and wanted the latter. Two
   guards keep this from being wasteful/spammy:
   1. If a Best Trade position is already open, the whole
      scan is skipped that run (one locked pick per day,
      unchanged).
   2. No new position opens within 14:45-15:15 IST of the
      square-off (LAST_ENTRY_CUTOFF in daily_best_trade.py)
      - not enough runway left to call it intraday.
   Every run still logs to the Excel "Best Trade" sheet
   (audit trail), but Telegram only fires when a position
   actually opens - otherwise 10 runs/day would mean 10
   near-identical "no trade yet" pings.

✅ [Same day, third follow-up] Live multi-timeframe entry
   scanning + a 45-min open/close buffer, replacing the
   30-min single-script design above. User wanted "check
   every candle live, analyze, and trade" with 1m/5m/15m
   combined (15m = trend, 5m = entry, 1m = timing - all
   three must agree), and confirmed a trade should open 45
   min after NSE opens and close 45 min before it shuts.

   First design considered: one long-lived GitHub Actions
   job per market-hours session (~6h, split into two since
   a single job caps at 6h) looping internally every 60s.
   Rejected after a validation pass found real problems:
   yfinance's "batch" download is actually one HTTP
   request per ticker, so a 60s loop across many symbols
   for hours risks tripping Yahoo's rate limiting on
   GitHub's shared runner IP range (breaking the *other*
   existing scheduled scripts too, not just this one);
   this repo's own workflow comments already document
   `schedule` triggers slipping under load; and committing
   mid-loop over several hours would need `git rebase`
   handling to avoid non-fast-forward push failures.

   Replaced with two cooperating stateless scripts instead
   (same proven pattern this repo already relies on -
   independent short runs handing off state via a
   committed file, like paper_portfolio.json already does):
   - refresh_shortlist.py (new) - the wide daily-interval
     scan + news + option chain/decision, still every 30
     min (+ one new pre-market run at 08:45 IST) via
     .github/workflows/best_trade_report.yml, writing
     reports/best_trade_shortlist.json.
   - daily_best_trade.py (rewritten) - every ~5 min (new
     .github/workflows/best_trade_entry_scan.yml - 5 min is
     GitHub Actions' actual schedule floor, and also the
     entry timeframe's own cadence, so there's no benefit
     to tighter polling anyway). Reads the shortlist, checks
     15m/5m/1m alignment per candidate
     (strategy/multi_timeframe_engine.py, new), and - the
     genuinely new capability - checks any already-open
     position's Stop Loss/Target every run
     (strategy/best_trade_paper_trading.check_open_position,
     new) instead of only at the final square-off.
   - ENTRY_START (10:00 IST) / LAST_ENTRY_CUTOFF (14:15
     IST) in daily_best_trade.py, and the square-off time
     itself moved from 15:15 to 14:45 IST (45 min before
     NSE's 15:30 close, matching what the user asked for) -
     analysis still runs and logs to Excel even before
     10:00, only the actual position-open waits.
   - All three Best Trade workflows now `git pull --rebase`
     before committing - cheap insurance now that three
     independently-scheduled workflows touch repo state
     close together in time.

✅ 11 more pytest tests (test_multi_timeframe_engine.py -
   7 cases, pure alignment logic, aligned/not-aligned/
   missing-data; 4 new cases in
   test_best_trade_paper_trading.py for
   check_open_position) - 96 total tests passing

✅ [Same day, fourth follow-up] Manually triggered all
   three Best Trade workflows via workflow_dispatch to
   verify them for real instead of waiting for Monday's
   first scheduled run - this immediately caught a real
   bug: Best Trade Entry Scan and Best Trade Square-Off
   both failed (Shortlist Refresh succeeded).

   Root cause: on a repo where no Best Trade position has
   ever been opened, reports/best_trade_portfolio.json
   genuinely doesn't exist yet (the Python scripts only
   call save_best_trade_portfolio() when there's actually
   something to open/close). The workflows' `git add
   reports/best_trade_portfolio.json` step had no guard
   for that, so it failed with "fatal: pathspec ... did
   not match any files" (exit 128) and took the whole job
   down with it. Shortlist Refresh didn't hit this because
   refresh_shortlist.py saves unconditionally every run.

   Fix: `git add <file> || true` in all three Best Trade
   workflows - a no-op when the file isn't there yet,
   unchanged behavior once it exists. Shipped as PR #4,
   merged, then re-triggered both previously-failed
   workflows manually to confirm - both now succeed.

✅ 11 more pytest tests
   (test_daily_best_trade_timing.py) - fixed-clock
   monkeypatch coverage for ENTRY_START/LAST_ENTRY_CUTOFF,
   which had no tests until this manual test pass
   surfaced the gap - 107 total tests passing

==================================================

Known Issues / Blockers

• RESOLVED (confirmed by the manual trigger above):
  both the Option Chain Engine and News Engine ran
  clean on the real GitHub Actions runner - the
  "Refresh best trade shortlist" job log shows
  "Shortlist saved: 6 stock candidates, 2 option
  candidates" with no fetch-failure lines for either
  news or option chain. This dev sandbox's proxy
  blocking those domains was a sandbox-only artifact,
  not representative of GitHub Actions' network - NSE
  is reachable from GitHub's runners after all, at
  least on this occasion. Worth re-confirming over a
  few real trading days since NSE's blocking behavior
  isn't perfectly consistent.

• TATAMOTORS.NS / LTIM.NS still return no data from
  Yahoo Finance ("Quote not found" / delisted) -
  confirmed again on the real GitHub Actions run,
  carried over, unresolved.

• Broker not yet selected - once chosen, its data API
  may be a more reliable Option Chain source than the
  free NSE scrape.

• Resolved by the third follow-up above: Best Trade
  positions now get checked every ~5 min all day (not
  just at open/close), so a Stop Loss/Target touch is
  caught close to when it happens instead of only being
  discovered at the final square-off.

• The rejected sleep-loop design's rate-limit math was
  reasoned about, not measured against a live GitHub
  Actions run - the shipped 5-min/30-min stateless design
  is far more conservative, but genuinely confirming
  yfinance behaves under the new schedule still needs a
  few real days of scheduled runs to watch.

• best_trade_shortlist.json (like the other two
  portfolio files) is committed to git every run - all
  three workflows were confirmed working individually via
  manual `workflow_dispatch` runs, but not yet observed
  running concurrently on their real overlapping cron
  schedules - worth watching the first few days for any
  git-rebase friction there.

• Neither manual test run actually opened or closed a
  Best Trade position (it was after both the 14:15 IST
  entry cutoff and outside market hours) - the git-add
  fix and the open/close code paths themselves are only
  verified by unit tests so far, not a real end-to-end
  open-then-close cycle on live data.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data.
Report Engine displays. Excel Engine stores history.
Options logic (Option Chain Engine, Options Decision
Engine) kept fully separate from normal NIFTY / stock
trading logic - only the Best Trade Engine reads both,
and only to rank/compare, never to alter either
engine's own math.

Claude never executes a real trade - the Best Trade
Engine only recommends; final action is always the
user's.

==================================================

Next Session

1. Watch the first few real trading days of all three
   Best Trade workflows on their actual cron schedules
   (Shortlist Refresh every 30 min + pre-market, Entry
   Scan every ~5 min, Square-Off at 14:45 IST) - manual
   workflow_dispatch runs already confirmed each one
   individually (including that GitHub Actions can reach
   both the RSS feeds and the NSE option chain), but
   still need to see: entries actually opening between
   10:00-14:15 IST on live data, a Stop Loss/Target hit
   getting caught intraday (not just at square-off), and
   that concurrent/overlapping cron runs across three
   workflows aren't hitting git-rebase conflicts

2. Commit Desktop App (PySide6) and Android App
   (Flutter, mobile_app/) to the repo (carried over)

3. Fix TATAMOTORS / LTIM ticker symbols (carried over)

4. Select broker (Upstox / Angel One) → Broker
   Integration (carried over)

5. Tune the News Engine keyword lexicon and Best
   Trade Engine weighting once real daily picks can
   be compared against outcomes

6. Once a few days of live 15m/5m/1m alignment picks
   exist, review how often the shortlist (from
   refresh_shortlist.py) actually produces an aligned
   candidate - the shortlist size (6 stocks) or
   alignment strictness may need tuning if entries are
   very rare or too frequent

==================================================

END OF SESSION
