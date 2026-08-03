# TURION AI Trader

SESSION LOG

==================================================

Session ID

S20260803-001 (cloud session - claude.ai/code, not a
local machine session - see 25-Jul/28-Jul/29-Jul logs
for why that distinction matters for this repo)

--------------------------------------------------

Date

03-Aug-2026

--------------------------------------------------

Version

v0.0.14 -> v0.0.15

==================================================

Today's Achievements

✅ User asked to confirm the app's total capital, believing
   it was a shared Rs 10 lakh pool split across Swing and
   Intraday. Checked strategy/paper_trading.py and
   strategy/best_trade_paper_trading.py: both engines
   independently start from their own INITIAL_CAPITAL =
   100000 - two separate Rs 1,00,000 paper accounts, not
   one Rs 10 lakh pool (combined starting capital is
   actually Rs 2,00,000). Confirmed the app's Portfolio/
   History "Cash" figure was Swing-only by design (matches
   the project's long-standing rule that Intraday and Swing
   logic/state stay fully separate) - not a bug, but the
   Intraday section had no equivalent Cash figure of its own
   visible anywhere, which was confusing.

✅ Added a Cash StatPill to History's Intraday section,
   mirroring the one Swing already had (mobile_app/lib/
   screens/history_screen.dart) - defaults to Rs 100,000 if
   best_trade_portfolio.json doesn't exist yet, same
   fallback pattern the screen already uses for Swing.

✅ FOUND AND FIXED a real, systematic bug the user noticed
   independently: every trade timestamp shown in the app
   (Entry/Exit time, chart "Updated ..." caption) was
   ~5.5 hours earlier than the real IST time it happened at.

   ROOT CAUSE: every "Entry Time"/"Exit Time"/"Generated At"
   field in reports/*.json is plain Python datetime.now() on
   a GitHub Actions runner - i.e. UTC. Every engine's
   IST-aware datetime (the `IST = timezone(timedelta(hours=5,
   minutes=30))` pattern used throughout daily_best_trade.py
   etc.) is only ever used internally for market-hours
   gating (ENTRY_START/LAST_ENTRY_CUTOFF checks) - never for
   what actually gets persisted to the JSON files the app
   reads. mobile_app's formatBackendTimestamp()
   (widgets/common.dart) parsed that raw UTC string and
   displayed it completely as-is, with no timezone
   conversion - confirmed against a real stored value
   ("2026-08-03 04:36:01" UTC, i.e. 10:06 AM IST, was
   displaying as "4:36 AM").

   FIX: parse the raw string as UTC (DateFormat.parseUtc)
   and add the +5:30 IST offset before formatting. One
   shared function, so it fixed every screen that shows a
   trade timestamp at once (Portfolio, History, the
   trade-detail bottom sheet) plus a second, related bug
   found along the way in chart_screen.dart - its "Updated
   ..." caption was interpolating the raw backend string
   directly with no formatting at all (not even
   formatBackendTimestamp), now routed through the same
   fixed function.

   SCOPE NOTE: deliberately a display-only fix. The
   backend's stored timestamps are still raw UTC (an
   internal implementation detail, consistent everywhere in
   the Python codebase) - no data migration, no risk to
   already-written history. The one place that reads two
   raw timestamps directly (the trade-detail sheet's
   holding-duration calculation) was checked and confirmed
   unaffected - the UTC-vs-IST offset cancels out in a
   difference between two timestamps that both carry the
   same (wrong) offset.

==================================================

Bugs Fixed

• mobile_app/lib/widgets/common.dart -
  formatBackendTimestamp() displayed raw UTC backend
  timestamps as if they were already IST, ~5.5 hours off on
  every trade time shown in the app since the feature was
  first built. Fixed at the single shared formatting
  function, not per-screen.

• mobile_app/lib/screens/chart_screen.dart - the "Updated
  ..." caption interpolated the raw, completely unformatted
  backend timestamp string directly (in addition to being in
  the wrong timezone) - now goes through
  formatBackendTimestamp() like every other timestamp in the
  app.

==================================================

Development Rule

No engine should directly make trading decisions in
isolation. Every engine returns structured data. Report
Engine displays. Excel Engine stores history. Options logic
kept fully separate from normal NIFTY/stock trading logic.

Claude never executes a real trade - final action is always
the user's.

==================================================

UPDATE (same day, local Claude Code Desktop session)

✅ DONE: built the release APK locally (`flutter build apk
   --release`, mobile_app/) and installed it on the user's
   phone via `adb install -r` - no uninstall needed first,
   confirming the signing-consistency fix from a prior
   session (see 25/28/29-Jul logs re: the debug-keystore
   mismatch that used to force an uninstall every time) is
   still holding. Both of today's changes verified live by
   the user on-device: History's Intraday Cash stat shows,
   and trade timestamps now display correctly in IST (the
   ~5.5-hour-early display bug is gone).

==================================================

UPDATE (same day) - NIFTY/BANKNIFTY options money-management
research

User asked to design and test a specific options money-
management strategy: deploy the FULL Rs 1,00,000 capital into
one ATM option per day, book a fixed % NET (after real costs)
profit target, cut losses at a fixed % Stop-Loss, guarantee at
least one trade per day. Analysis only, per this repo's rule
that options logic stays separate from equity/index logic - new
files strategy/nifty_options_backtest.py,
indicators/black_scholes.py, strategy/options_transaction_costs.py,
plus 8 new unit tests (tests/test_black_scholes.py,
tests/test_options_transaction_costs.py), all passing.

CAVEAT, upfront and unavoidable: no real historical NIFTY/
BANKNIFTY option premium data exists (confirmed 30-Jul - NSE's
option chain API only serves today's live snapshot), so premium
is ESTIMATED via Black-Scholes off spot + India VIX (as an
implied-vol proxy) - a theoretical approximation, not a real
traded price. Every number below inherits that limitation.

✅ FOUND AND FIXED a real modeling bug along the way: an early
   version repriced the option off the LIVE, continuously-
   updating VIX every candle. This made Stop-Loss exits
   overshoot their nominal threshold by 4-9x (a nominal -0.5%
   SL realizing -4.48% avg / -13.76% worst at 5m candles, still
   -2.20% avg / -3.92% worst even at 1m candles) - traced to the
   raw VIX index's own tick-to-tick calculation noise, not a
   real market dynamic. Fixed by freezing IV at entry_time's VIX
   reading for the rest of that day (hold_iv_fixed_at_entry=True,
   default) - re-tested and the overshoot did NOT shrink
   (-4.76% avg, near-identical), which disproved the VIX-noise
   hypothesis and pointed to the REAL cause instead: short-dated
   (3-day) ATM options are simply extremely leveraged by nature -
   a routine 0.1% NIFTY move can swing an ATM option's value
   ~8%, so a tight SL expressed as a % of total capital gets
   blown through by ordinary market moves, not a bug. The
   overshoot gap stayed roughly constant (~4 percentage points)
   regardless of the nominal SL tested (0.5% up to 5%) - useful
   for real risk-sizing (expect worst-case loss on a "Stop Loss"
   day to run ~4 points past the nominal SL, whatever it's set
   to).

✅ Widened target/SL to realistic multiples (2-5% instead of the
   original 0.5-2% idea, to actually contain the leverage found
   above) and swept combos on NIFTY, forcing a trade every day
   (direction: RSI >= 50 -> CE else PE, no VIX gate, guarantees
   daily entry). Result: broadly positive across most combos
   (best: Target 5%/SL 5%, 106% total return over 57 trading
   days, 56% win rate) - BUT this direction-picking rule is NOT
   this repo's actual tested signal, just an always-fire tie-
   break invented for this task. Flagged as likely a fit to this
   one 60-day window, not a real edge, before testing further.

   Full sweep (57 trading days, forced-entry mode) with a
   simple (non-compounding - same fixed Rs 1,00,000 capital
   reused every day, one day's PnL never feeds the next day's
   position size) x21-trading-day monthly projection for
   reference:

   Target% | SL% | Avg %/day | Projected %/month | Projected Rs/month
   2  | 3  | 0.754% | 15.8% | Rs 15,840
   2  | 5  | 1.064% | 22.3% | Rs 22,340
   2  | 8  | 0.736% | 15.5% | Rs 15,460
   2  | 10 | 0.436% |  9.2% | Rs  9,160
   3  | 3  | 0.474% | 10.0% | Rs  9,950
   3  | 5  | 0.843% | 17.7% | Rs 17,700
   3  | 8  | 0.486% | 10.2% | Rs 10,210
   5  | 3  | 1.290% | 27.1% | Rs 27,090
   5  | 5  | 1.862% | 39.1% | Rs 39,100
   5  | 8  | 1.498% | 31.5% | Rs 31,460
   5  | 10 | 1.187% | 24.9% | Rs 24,930

   Best: Target 5%/SL 5%, ~Rs 39,100/month projected. Same
   caveats as everything else in this section apply (Black-
   Scholes-estimated premium, no bid-ask spread modeled, one
   60-day window, forced-entry signal not the tested one) -
   not tradeable as-is, kept for reference only.

✅ Re-ran using the REAL tested signal instead
   (strategy/momentum_vix_backtest.py's 22-Jul Momentum(RSI>60/
   <40)+VIX-percentile-band filter, added as
   use_momentum_vix_filter=True - trades less than once/day,
   unlike the forced version). Result on NIFTY: INCONSISTENT
   across combos - Target 3%/SL 5% alone lost Rs 13,219 while
   neighboring combos (2%/5%, 5%/5%) were positive - confirms
   the 30-Jul finding that this signal has no reliable edge on
   NIFTY specifically (that test found only 9/42 combos
   positive on directional accuracy alone).

✅ Re-ran the same real signal + real premium/cost model on
   BANKNIFTY (symbol="^NSEBANK", lot_size=30, strike_step=100)
   - the one index where the original 22-Jul test found a
   strong directional edge (38/42 combos positive). Result:
   CONSISTENTLY and substantially NEGATIVE across every combo
   tested (worst: Target 1%/SL 1%, -Rs 1,14,539 / -114.5% over
   52 trading days). This is an important finding on its own:
   correct DIRECTION (what the 22-Jul test measured) does not
   equal real option PROFIT once premium decay/leverage/costs
   are modeled - exactly the gap that test's own caveat warned
   about ("still needs a real option-premium/theta-decay cost
   model... directional accuracy is necessary but not
   sufficient"). CAVEAT: BANKNIFTY's weekly expiry was
   discontinued Nov-2024 (monthly only now), so this backtest's
   fixed days_to_expiry=3 assumption is considerably less
   realistic for BANKNIFTY than for NIFTY (which still has
   weekly expiry) - some of this negative result may be an
   artifact of assuming more leverage/gamma than a real
   monthly-cycle BANKNIFTY option usually carries, not pure
   proof the idea can't work.

OVERALL CONCLUSION: across all three tested variants (NIFTY
forced-entry, NIFTY real-signal, BANKNIFTY real-signal), no
combination showed a reliable, trustworthy edge once real
premium economics were modeled - the one variant with clean
positive numbers (NIFTY forced-entry) is built on a
direction-picking rule known to have no real edge. Leaning
REJECTED / not tradeable as currently designed, same rigor as
every other rejected candidate in this project - not wired into
any paper trading.

==================================================

Next Session

1. Decide whether to pursue the BANKNIFTY monthly-expiry
   modeling gap further (a real expiry-calendar instead of the
   fixed days_to_expiry=3 approximation) before treating the
   negative BANKNIFTY options result as final, or shelve this
   options money-management idea entirely (see today's
   OVERALL CONCLUSION above).

2. Let August's data keep accumulating (carried over from
   02-Aug - Watchlist and Best Trade Engine both still well
   short of the ~30-50 trades usually needed for statistical
   confidence).

3. Backtest require_no_crash_state on the best-known combos
   found so far (carried over from 02-Aug).

4. Decide on a path forward for option chain data (carried
   over from 30-Jul).

5. Apply strategy/transaction_costs.py's real cost model to
   the Watchlist and Best Trade Engine's own live
   evaluations (carried over from 23-Jul, still not done).

6. Commit Desktop App (PySide6), package as .exe (carried
   over).

7. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

END OF SESSION
