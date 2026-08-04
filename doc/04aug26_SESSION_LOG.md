# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260804-001 (local machine session - Claude Code
Desktop, D:\TURION_AI_Trader)

--------------------------------------------------

Date

04-Aug-2026

--------------------------------------------------

Version

v0.0.15 (no version bump - new integration work,
not yet wired into any live/paper trading)

==================================================

Today's Achievements

✅ Broker decision finalized (started 03-Aug, completed
   today): Fyers (free API tier), over Upstox/Angel One/
   Zerodha - see doc/03aug26_SESSION_LOG.md and
   PROJECT_STATUS.md Priority 6 for the full comparison
   and reasoning. User already holds an unused Angel One
   account, kept in reserve as a free secondary data
   source only, not for execution.

✅ Fyers account opened and activated by the user
   (KYC + income-proof, done by the user themselves -
   Claude does not handle personal/financial documents).
   API app created on Fyers' developer dashboard
   (App ID format: XXXXXXXXXX-200), Primary IP whitelisted
   (flagged to the user as likely a dynamic home-ISP IP -
   may need updating later if it changes).

✅ Built strategy/fyers_auth.py - Fyers login/access-token
   flow implemented against their raw REST API, NOT the
   official fyers-apiv3 SDK. The SDK's aiohttp dependency
   failed to build on this machine (Python 3.14.6, no
   prebuilt wheel yet, no MS C++ Build Tools installed) -
   raw `requests`-based HTTP calls avoid that dependency
   entirely, needing nothing beyond what's already in
   requirements.txt. Ran the full login flow live: user
   opened the generated auth URL, logged into Fyers, pasted
   back the redirected URL's auth_code, exchanged it for an
   access_token (saved to .env, gitignored) - VERIFIED via
   Fyers' /profile endpoint, confirmed real account connection.
   IMPORTANT: this access_token is a DAILY token (Fyers
   invalidates it every trading day) - the login flow needs
   re-running each day before the integration can make
   authenticated calls. Not yet automated (deliberately -
   user chose "manual, test first" over automating this
   today).

✅ Systematically tested Fyers' real data coverage (the
   user asked to check intraday, swing, options, futures
   data, charges, and any AI-connection feature) - all
   against the LIVE API with the real access token, not
   guessed from docs:
   - 1-minute INDEX (NIFTY) data: real candles as far back
     as ~9 years (2017) tested and confirmed; 10 years
     (2016) returned no_data - real cutoff sits somewhere
     between. Per-request limit is exactly 100 days (tested
     100 ok, 120/150/200/300/366 all "Invalid input") -
     needs pagination to build a multi-year archive, which
     is straightforward to script.
   - Daily (swing) INDEX data: confirmed real data back to
     at least 2006 (20 years), no issues.
   - This is a MAJOR upgrade over yfinance's ~60-day
     intraday limit that constrained essentially every
     backtest finding recorded in this project to date (the
     recurring "small sample, one window" caveat).
   - Options data: real live bid/ask/LTP/OI/volume confirmed
     working via the options-chain-v3 endpoint - but
     CONFIRMED (not just suspected) that EXPIRED option
     contracts are unavailable. Fetched Fyers' public NSE F&O
     symbol master (public.fyers.in/sym_details/NSE_FO.csv,
     75k+ rows) and verified it contains ONLY current/future-
     expiry symbols - last week's already-expired NIFTY
     contract is nowhere in it, and a direct historical-data
     request for that symbol returned "Invalid symbol
     provided" (a symbol-doesn't-exist error, not a data-gap
     error). This is a hard, structural limitation (the
     symbol itself stops existing after expiry), not a
     Fyers-specific gap likely to differ at other brokers.
   - Futures: current-month contract data works fine, AND
     cont_flag=1 (continuous futures - stitches historical
     expired months into one series) gave real data back to
     at least Jan-2024 (1.5+ years) tested successfully -
     futures have real multi-year history available in a way
     options structurally cannot, since only the calendar
     month changes (no strike dimension).
   - Charges: no live charges/margin API endpoint found
     (two reasonable-guess paths both 404'd) - this is a
     published rate card, not an API, consistent with the
     existing approach (strategy/options_transaction_costs.py's
     modeled rates).
   - "AI connection" (MCP tab seen in the Fyers dashboard
     screenshot): could not check - Fyers' site is a JS-heavy
     SPA that WebFetch can't render, and the Browser tool is
     policy-blocked from trading-platform domains. Asked the
     user to check the tab directly - not yet resolved.

✅ Researched (via WebFetch, live) where OLD/historical
   option premium data could come from, since no broker
   provides it for expired contracts:
   - NSE Bhavcopy (free, nseindia.com archives) - real EOD
     (one price/day) data for expired F&O contracts, going
     back years. The only free source of genuinely real
     historical option data found, though EOD-only (no
     intraday).
   - TrueData - found real pricing (Velocity plans, Rs 1,440-
     2,796/month covering NSE F&O among other segments) but
     the exact historical-options-depth is NOT published on
     their site (gated behind a sales call) - could not
     verify precisely despite trying three of their pages.
   - Global Datafeeds, Sensibull - similarly, no historical-
     depth or pricing specifics found publicly on their sites.
   - Conclusion given to the user: don't spend on these yet -
     start with what's already free and working (our own
     Fyers-based collection going forward), revisit paid
     vendors only if that proves insufficient later.

✅ Built strategy/fyers_options_collector.py - a manual-run
   script that snapshots the LIVE NIFTY + BANKNIFTY option
   chain (5 strikes around ATM each, nearest expiry) via
   Fyers and appends every option leg as one JSON line to
   reports/options_premium_history.jsonl (real bid/ask/LTP/
   OI/volume, not estimated). This is the "build our own
   archive going forward" fallback, now actually running -
   first real snapshot taken and verified (44 option-leg
   records, real NIFTY quotes e.g. Strike 24350 CE Bid
   264.35/Ask 264.65). Deliberately MANUAL for now (not
   wired into GitHub Actions automation yet) - the user chose
   to test it by hand first before automating, given Fyers'
   daily-token requirement adds complexity to automating this
   compared to the existing yfinance-based workflows.

✅ Explained options vs. futures (right/obligation, margin vs.
   premium, unlimited vs. capped downside, theta decay,
   contract lifecycle) when the user asked, tying it back to
   why futures got years of real history via cont_flag=1 and
   options structurally cannot.

✅ CAUGHT AND FIXED a real security near-miss: Notepad saved
   the user's first attempt at editing .env as ".env.txt"
   (auto-appended extension) instead of ".env" - a duplicate
   file containing the same FYERS_APP_ID/FYERS_SECRET_KEY,
   sitting as an UNTRACKED file that `.gitignore`'s exact
   `.env` pattern does NOT match. Caught via `git status`
   before anything was staged/committed - deleted the
   duplicate (the real .env already had working credentials,
   confirmed via the live login flow) and added `.env.txt` to
   .gitignore as a safety net against this exact mistake
   recurring.

✅ BUILT AND TESTED Fyers-based Swing + Intraday paper trading
   engines (same day, after the user pushed back on an over-
   cautious multi-day time estimate and correctly pointed out
   most of the existing analysis logic is data-source-agnostic
   already - revised estimate down to ~4-6 hours, which held up):

   - strategy/fyers_data.py - the one new piece actually needed:
     an adapter returning Fyers candles in the exact shape
     yf.download() does (DatetimeIndex, Open/High/Low/Close/
     Volume, tz-aware Asia/Kolkata for intraday), paginating past
     Fyers' 100-day/request intraday limit automatically. Every
     existing analysis function (analyze_symbol, calculate_rsi,
     calculate_atr, get_market_structure, etc.) works completely
     unchanged against its output - verified directly.

   - strategy/fyers_watchlist_scanner.py + strategy/fyers_paper_
     trading.py: Fyers-sourced counterparts to the Swing engine,
     reusing analyze_symbol/process_signal/position-sizing logic
     as-is. Writes to reports/fyers_test_portfolio.json, never
     touching the live yfinance portfolio (existing files
     completely untouched, per this repo's engine-separation
     rule). TESTED on the full 52-symbol NIFTY watchlist - opened
     12 real BUY positions off real Fyers daily data. Same known
     TATAMOTORS/LTIM symbol issue as yfinance (pre-existing, not
     new - see Known Issues).

   - strategy/fyers_multi_timeframe_engine.py + strategy/fyers_
     best_trade_paper_trading.py + fyers_daily_best_trade.py:
     Fyers-sourced counterpart to the 15m/5m/1m alignment engine
     and Best Trade paper trading - deliberately SIMPLER than the
     original (direct NIFTY-50 scan, no shortlist/news/option-
     chain ranking, no Excel/Telegram) to test the core mechanism
     first. Options picks stay on the separate strategy/
     fyers_options_collector.py track, not merged into this.
     TESTED live - correctly found RELIANCE aligned Bearish
     (15m/5m/1m all agreeing) and correctly found no BUY-aligned
     candidate in a small sample.

   All new files, all existing yfinance-based engines completely
   untouched - runs fully in parallel. Not yet on GitHub Actions
   (same daily-token-refresh open question as the options
   collector - see Next Session).

==================================================

Bugs Fixed

• strategy/fyers_options_collector.py (same session, before
  first real commit): used the wrong Fyers API base path
  (`api/v3/options-chain-v3` instead of the correct
  `data/options-chain-v3`) - caused 404s that surfaced as a
  confusing JSONDecodeError instead of a clear HTTP error
  because response.json() was called before checking status.
  Fixed by using a separate DATA_BASE_URL constant.

• .env.txt duplicate-secrets file (see above) - not a code
  bug, but a real near-miss caught before any git operation
  touched it.

• strategy/fyers_data.py - scanning the full 52-symbol
  watchlist back-to-back hit Fyers' rate limit on one symbol
  (BAJAJFINSV, "request limit reached"). Fixed with a retry-
  with-backoff on rate-limit responses (fyers_data.py) plus a
  proactive 0.3s delay between symbols (fyers_watchlist_
  scanner.py) - re-ran clean afterward.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data. Report
Engine displays. Excel Engine stores history. Options
logic kept fully separate from normal NIFTY/stock trading
logic.

Claude never executes a real trade - final action is
always the user's. Fyers integration makes only read-only
market-data calls (profile check, historical candles, option
chain) plus PAPER (not real) position tracking in reports/
fyers_test_portfolio.json and reports/fyers_best_trade_
portfolio.json - no real order-placement code exists or has
been wired up.

==================================================

Next Session

1. Ask the user what they saw under Fyers' "MCP" dashboard
   tab (couldn't check it directly - site blocked/JS-heavy)
   and figure out if it's relevant to this project.

2. Decide whether/how to automate the daily options-chain
   snapshot (strategy/fyers_options_collector.py) AND the new
   Fyers Swing/Intraday engines (fyers_paper_trading.py,
   fyers_daily_best_trade.py) - all three currently manual by
   choice; automating any of them needs a plan for the daily
   access-token refresh (strategy/fyers_auth.py's login flow
   needs a human in the loop today). Discussed three options
   (full auto-login storing PIN+TOTP - real security risk since
   it grants full account access if leaked; a Telegram 1-tap
   reminder; an in-app WebView "Login" button that captures the
   OAuth redirect automatically, never handling PIN/password in
   our own code) - user hasn't picked one yet.

2b. Now that both new Fyers engines are built and tested: keep
   running them manually for a few weeks (per the already-
   agreed plan - a real proving period BEFORE any cutover from
   yfinance, not immediately after code works) and compare
   reports/fyers_test_portfolio.json / fyers_best_trade_
   portfolio.json against the live yfinance ones over time.

3. Once a few days/weeks of real options_premium_history.jsonl
   data exists: compare it against indicators/black_scholes.py's
   estimates (from 03-Aug's research) to see how far off the
   estimate was - the original motivation for collecting this.

4. Consider re-running existing index-based backtest findings
   (ADX filter, VIX filter, Daily-alignment, etc.) against
   Fyers' multi-year historical index data instead of
   yfinance's 60-day window, now that it's confirmed
   available - would finally remove the "small sample, one
   window" caveat attached to nearly every prior finding.

5. Consider a futures-based strategy angle, now that real
   multi-year futures history is confirmed available via
   cont_flag=1, unlike options.

6. Optionally download NSE Bhavcopy history for a free,
   EOD-level real options backtest in the meantime (see
   today's Achievements) - not started yet.

7. Let August's data keep accumulating (carried over from
   02-Aug/03-Aug).

8. Backtest require_no_crash_state on the best-known combos
   (carried over from 02-Aug).

9. Apply strategy/transaction_costs.py's real cost model to
   the Watchlist and Best Trade Engine's own live evaluations
   (carried over from 23-Jul, still not done).

10. Commit Desktop App (PySide6), package as .exe (carried
    over).

11. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

END OF SESSION
</content>
