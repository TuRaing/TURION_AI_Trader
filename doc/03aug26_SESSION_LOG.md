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

Next Session

1. Let August's data keep accumulating (carried over from
   02-Aug - Watchlist and Best Trade Engine both still well
   short of the ~30-50 trades usually needed for statistical
   confidence).

2. Backtest require_no_crash_state on the best-known combos
   found so far (carried over from 02-Aug).

3. Decide on a path forward for option chain data (carried
   over from 30-Jul).

4. Apply strategy/transaction_costs.py's real cost model to
   the Watchlist and Best Trade Engine's own live
   evaluations (carried over from 23-Jul, still not done).

5. Commit Desktop App (PySide6), package as .exe (carried
   over).

6. Fix TATAMOTORS / LTIM ticker symbols (carried over).

==================================================

END OF SESSION
