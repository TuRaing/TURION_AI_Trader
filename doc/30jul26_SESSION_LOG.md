# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260730-001 (local machine session - Claude Code
Desktop, D:\TURION_AI_Trader)

--------------------------------------------------

Date

30-Jul-2026

--------------------------------------------------

Version

v0.0.14 (no version bump - research/analysis-only
additions, no live-engine changes)

==================================================

Today's Achievements

✅ Diagnosed "app not displaying" report: adb was
   unauthorized (fixed by re-accepting the USB debugging
   prompt), then a fresh logcat capture around a real app
   launch showed no FATAL EXCEPTION / crash - likely a
   transient glitch (stale state or a mid-load moment),
   resolved on its own once re-authorized. No code change
   needed.

✅ Answered "how much data do we have, how much more do we
   need" with real numbers: Watchlist (Swing) 8 closed
   trades since 11-Jul, Best Trade (Intraday) 18 closed
   trades since 21-Jul - both well short of the ~30-50
   trades usually needed for statistical confidence.
   Intraday accumulates ~2 trades/day (30-50 reachable in
   1.5-2 weeks); Swing accumulates far slower (months to
   reach the same count) given its hold times.

✅ Suggested and got approval on four August research
   candidates (see PROJECT_STATUS.md Priority 2), then
   tested all four the same day:

   1. DONE, PROMISING: India VIX regime filter applied to
      strategy/multi_timeframe_backtest.py's *equity*
      entries (new require_vix_in_band parameter), reusing
      the 22-Jul BANKNIFTY-options percentile-band
      methodology. VIX 30-70 band: -Rs 115.37 net vs -Rs
      614.57 baseline (81% reduction), 6 trades, 50% win
      rate - landing within noise of the independently-
      found ADX>25 result (-Rs 99.33). Stacking VIX+ADX
      over-restricts to 1 trade, don't combine. Still
      net-negative/small-sample, not wired into live paper
      trading.

   2. NOT TESTABLE: option chain PCR/Max Pain as equity
      support/resistance. Confirmed NSE's option chain API
      has no historical archive (only today's live
      snapshot) - genuinely cannot be backtested the way
      VIX/price data can, regardless of network access.
      Also re-confirmed the live fetch itself is currently
      failing - 403 even from the user's own home network
      (not just the previously-documented datacenter-IP
      block), consistent with the current live shortlist's
      "option chain data unavailable" reason string.
      Investigated further: the response carries an AKA_A2
      cookie (Akamai edge), suggesting NSE's bot protection
      may now be fingerprinting the HTTP client itself, not
      only the source IP - a broader block than previously
      understood. Discussed next steps with the user
      (curl_cffi-style browser-fingerprint client, a real
      headless browser, or waiting for Broker Integration
      for a proper paid data source) - no code change made,
      shelved pending a decision.

   3. TESTED, INCONCLUSIVE: time-of-day entry filter on the
      Daily-aligned NIFTY baseline (22 trades bucketed into
      first-90-min/midday/last-stretch, 5-11 trades each) -
      all three landed within a similar -Rs 25 to -Rs 35
      net-per-trade range, no bucket stood out. Also
      surfaced that this combo's 31.82% gross win rate is
      0% once real per-trade transaction costs are applied
      - the tight 0.5x-ATR stop makes individual wins
      smaller than the round-trip cost on an index-sized
      position. Sample too small to be conclusive either
      way; not pursued further.

   4. DONE, REJECTED: partial profit booking on the Daily-
      timeframe strategy (new strategy/
      daily_partial_booking_backtest.py, analysis-only,
      same entry signal as the live/proven strategy for a
      fair comparison) - book half at a nearer 1x-ATR
      target, trail the rest, instead of the live 1.5x SL/
      3x Target all-or-nothing exit. Worse than baseline in
      3 of 4 tested symbols (NIFTY, ICICIBANK, RELIANCE),
      notably halving the gain on RELIANCE, the one case
      where baseline was actually profitable. Win rate rose
      everywhere but is a vanity metric here - booking
      early caps upside on exactly the trades that would
      have made real money. Not adopted.

✅ User laid out a staged real-capital plan (August tuning
   -> broker API -> another month of paper trading on the
   broker's real feed -> Rs 10,000 -> Rs 1,00,000 if
   profitable) - recorded in PROJECT_STATUS.md's LONG TERM
   ROADMAP along with process/risk-management suggestions
   raised alongside it (gate stages on trade count not
   calendar time, start Rs 10,000 with one engine not both,
   define a stop/rollback rule up front, validate real
   broker slippage against the modeled cost, ramp into
   Rs 1,00,000 gradually, keep signals mechanical through
   the real-money stages). Explicitly not financial advice -
   process/engineering suggestions only, and Claude still
   never executes a real trade at any stage.

==================================================

Bugs Fixed

(None - the "app not displaying" report turned out to be a
transient/adb-authorization issue, not a code bug.)

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data. Report
Engine displays. Excel Engine stores history. Options
logic kept fully separate from normal NIFTY/stock trading
logic.

Claude never executes a real trade - final action is
always the user's, at every stage of the capital plan
above.

==================================================

Next Session

1. Let August's data accumulate (Watchlist and Best Trade
   Engine both still well short of a statistically
   confident sample) - no new strategy work needed, just
   time and monitoring.

2. Confirm the new Square-Off cron-job.org trigger
   (29-Jul) fired correctly during a real 14:40-15:15 IST
   window - still only smoke-tested as of 29-Jul.

3. Decide on a path forward for option chain data (Priority
   2 candidate #2): try a browser-fingerprint HTTP client,
   a real headless browser, or shelve until Broker
   Integration provides a paid data source instead.

4. Apply strategy/transaction_costs.py's real cost model
   to the Watchlist and Best Trade Engine's own live
   evaluations (carried over from 23-Jul, still not done).

5. Commit Desktop App (PySide6), package as .exe (carried
   over).

6. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

END OF SESSION
