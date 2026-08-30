# 30-Aug-2026 — Crypto Paper-Trading Session Log (continued)

Continuation of the same running conversation as
`doc/29Aug26_CRYPTO_SESSION_LOG.md` (that file's steps 13-15 already
cover the LTP-vs-spread slippage finding and the quote-based book
rollback, both genuinely 30-Aug-2026 work per `git log` - see that
file's own corrected date note). This file picks up from there: the
`daily_profit_lock` investigation, trailing-stop capability, and a
real live crash + fix. See `doc/CRYPTO_PROJECT_STATUS.md` for the
current standing state - this file is the narrative only.

## What happened

1. **Real trade analysis** on the two original (LTP) BTC/ETH books -
   both whipsawing well under their own breakeven win rate (BTC 23.3%
   vs 31.8% needed, ETH 18.1% vs 29.0% needed), median ~9-min holds,
   PE trades performing far worse than CE (ETH PE: 0% win over 22
   trades) - a real directional-bias signature, not yet acted on.

2. **`daily_loss_lock` backtested first - rejected.** A first
   comparison wrongly suggested BTC flipped to profit (+$1,702) -
   turned out to be a real methodology bug: each backtest variant was
   independently refetching "the last 7 days from right now" from a
   live API, so real time moving forward between calls meant every
   variant silently ran on different underlying data. Fixed by
   fetching `data_points` once per currency and reusing the same
   object across every variant (`run_for()`'s own note in
   `crypto_options_backtest.py`). Re-run properly: `daily_loss_lock`
   made BTC notably WORSE in both a 24h and a 12h rolling window - not
   pursued further.

3. **`daily_profit_lock` backtested next - this one actually helped.**
   Built as a rolling window (not the field's normal UTC-calendar-day
   boundary - a 24/7 market has no real "today"; see `strategy/
   crypto_tick_runner.py`'s new `_realized_pnl_within_hours()`). A full
   parameter sweep (0.5-3% x 1-8h windows, two different real 7-day
   windows each) found BTC needs 1%/2h and ETH needs a DIFFERENT
   setting, 0.5%/3h - the 2h window that worked for BTC was actually
   one of the worse choices for ETH, because ETH's much smaller average
   win means the exact window length matters far more than the exact
   percentage (which barely matters above ~0.5%, since a single win
   crosses every threshold from 0.5-3% at once).

4. **Tried extending the consistency check further back - hit a real
   data ceiling.** Deribit's public API only retains already-expired
   instruments for `settlement_period="day"`, not `"week"` - last
   week's weekly BTC contract's real trade history is already gone
   entirely from their API. The two windows already tested (recent +
   `offset_days=3`) are close to the full real range this specific
   weekly contract has ever had - no way to test further back with
   real (non-fabricated) data.

5. **Tried a trailing-stop on top of the losing 12h-window BTC
   variant** (`trailing_min_pct=3.0`, ported from `strategy/fyers_
   options_engine.py`'s own NIFTY version into `strategy/event_driven_
   engine.py` as a new opt-in `trailing_min_pct` cfg field) - made
   things dramatically worse (9 trades, -$7,021 vs the 12h-alone
   -$2,585). Not pursued further for crypto, but the capability itself
   is real, tested, and reusable - unlike the NIFTY version (which
   could never be backtested at all, only Entry/Exit historical
   records), this one DOES work in `crypto_options_backtest.py` since
   `rsi_momentum_decide_fn` already runs against every intermediate
   5-min data point.

6. **Deployed the winning profit-lock settings as two NEW, separate
   live books** - `rsi_momentum_crypto_btc_profitlock` (1%/2h) and
   `_eth_profitlock` (0.5%/3h), via new `CRYPTO_PROFIT_LOCK_PCT`/
   `CRYPTO_PROFIT_LOCK_WINDOW_HOURS` env vars and two new systemd
   units - the two original LTP books were left completely unchanged,
   per the user's explicit "old strategy चालू राहू द्या" ask.

7. **Updated `crypto_app`** to a 4-tab layout (BTC, ETH, BTC Profit
   Lock, ETH Profit Lock), TabBar made scrollable to fit. Rebuilt and
   reinstalled the release APK on the user's phone (same real device
   as before), confirmed the new tabs load real live data via a web
   build sanity check first.

8. **Both new profit-lock services crashed within ~10-15 minutes of
   going live** - silently down for ~2.5 hours before being noticed
   via a direct status check (`systemctl status` showed `failed`,
   restart-limit exhausted). Root cause: `_realized_pnl_within_hours()`
   compared a timezone-AWARE live timestamp against naive stored Exit
   Time strings - `TypeError`. Never caught by any backtest run this
   session, since the backtest script's timestamps are always naive -
   the bug only existed on the live path. Fixed by stripping `tzinfo`
   up front; added a regression test that deliberately builds an aware
   timestamp so this can't silently reappear. Deployed the fix,
   `systemctl reset-failed` + restart on both units, verified both
   active and trading normally (checked real Firebase state directly:
   the ETH profit-lock book had exactly 1 real trade from before the
   crash, then a fresh clean position after the restart - no loop, no
   further crash).

## Real lesson from this session

A live crypto WebSocket path and this project's own backtest replay do
NOT automatically exercise the same timestamp representation (aware
vs naive) even when they call the exact same shared `decide_fn` - any
new helper that touches a raw `timestamp` object directly (not just
cfg/data_point fields already validated elsewhere) needs to be
exercised against BOTH the backtest AND a live-shaped input before
being trusted live. A clean backtest run is not sufficient proof by
itself.

## Carried to next session

- Let all 4 live books (2 LTP, 2 profit-lock) run for a few weeks and
  watch real forward results - single-window backtests, even sweep-
  tuned ones, are not proof by themselves (documented in `doc/
  CRYPTO_PROJECT_STATUS.md`'s own repeated caution).
- The LTP-vs-real-spread gap (BTC/ETH original books' Quote-based PnL
  showing ~90-95% worse than what's reported) is still unresolved -
  see `doc/CRYPTO_PROJECT_STATUS.md`'s own "Real finding" section for
  the options discussed but not decided.
- The CE-vs-PE performance gap found in step 1 above (PE trades
  performing far worse, especially ETH's 0% win rate over 22 PE
  trades) was noted but not investigated further this session.
