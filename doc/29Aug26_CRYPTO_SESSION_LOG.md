# 29-Aug-2026 — Crypto Paper-Trading Session Log

Separate log file for the crypto sub-project, kept apart from the
NIFTY side's own `doc/DDmonYY_SESSION_LOG.md` files by the user's
explicit ask, to avoid any merge conflict between sessions. See
`doc/CRYPTO_PROJECT_STATUS.md` for the current standing state — this
file is the day's narrative only.

## Context at session start

Machine had a Claude crash mid-session and needed a reinstall; this
session picked up on the `crypto-paper-trading` branch with two
uncommitted local changes already sitting in the working tree from
before the crash (`crypto_options_backtest.py`,
`run_crypto_options_engine.py` — the BTC $10,000 / ETH Rs 1,00,000
capital split, per the user's own prior explicit ask).

## What happened this session

1. **Access check** — confirmed both GitHub (fetch/push via HTTPS,
   `crypto-paper-trading` branch in sync with origin) and the Oracle
   VM (SSH key valid, `turion-crypto-options` systemd service
   reachable) were working.

2. **Found a live bug** — the deployed VM's `turion-crypto-options`
   service was stuck in a rapid open/close stop-loss loop: 553 trades
   in 44 minutes, portfolio Cash at -$26,545 (started at $1,047.89).

3. **Reproduced Python environment from scratch** — the post-crash
   reinstall had wiped installed packages (`ModuleNotFoundError:
   dotenv`, no venv). Reinstalled from `requirements.txt`.

4. **Reproduced the bug locally, isolated from infra** — ran
   `crypto_options_backtest.py` clean: BTC ($10,000) looked normal (48
   trades, 41.7% win, realistic multi-hour holds), but ETH
   (Rs 1,00,000 / $1,047.89) showed the same signature — 967 trades
   over 7 days, 0.5% win rate, every trade closing within one 5-min
   candle at a suspiciously uniform ~$47-51 loss. Confirmed this was
   NOT an infra/deployment issue — it reproduced in a pure local
   backtest with no network/VM involved.

5. **Found the root cause** — traced one ETH trade by hand: entry
   premium 61.4534, exit premium 61.2488 (a real move of only ~0.33%,
   gross PnL only -$3.48), but the recorded Net PnL was -$52.62. The
   ~$49 gap was transaction cost:
   `strategy/options_transaction_costs.py`'s `BROKERAGE_PER_ORDER =
   Rs 20` (an INR figure, from the NIFTY/BankNifty cost model) was
   being subtracted as **$20** from a USD-denominated crypto trade —
   no currency conversion at all. ~95x too large at the real USD/INR
   rate, and large enough on a ~$1,000 crypto position to force almost
   every trade into a loss by itself, independent of real price
   movement.

6. **Fixed it, scoped to crypto only** — per CLAUDE.md's own rule
   keeping options logic separate from the NIFTY/BankNifty logic:
   - New `strategy/crypto_transaction_costs.py`
     (`calculate_crypto_options_round_trip_cost`) — Deribit-realistic,
     USD-native, no flat INR brokerage.
   - `strategy/event_driven_engine.py`'s `_net_pnl()` gained an opt-in
     `cfg.get("cost_fn")` (default `None` → the exact existing
     NIFTY/BankNifty behavior, unchanged).
   - `make_st2_threshold_event_cfg()` gained a matching `cost_fn=None`
     parameter.
   - `crypto_options_backtest.py` and `run_crypto_options_engine.py`
     now pass the new crypto cost function.

7. **Verified** — `tests/test_event_driven_engine.py` +
   `tests/test_event_driven_runner.py`: 74/74 pass, confirming zero
   behavior change for the other 59 live NIFTY/BankNifty books.
   Backtest re-run: ETH went from 967 trades/0.5% win to 31 trades/
   35.5% win (same shape as BTC's 48/41.7%) — the loop is gone. Both
   currencies now show a realistic net loss for this particular
   7-day window (BTC -$8,348, ETH -$1,301), which is a genuine
   strategy-performance result on real market data, not a bug (a
   prior backtest window on the same signal showed +$7,716 — the
   signal's own small-sample variance was already known/documented).

8. **Created this doc pair** (`CRYPTO_PROJECT_STATUS.md` + this file)
   — the crypto sub-project previously had zero presence in `doc/`;
   all continuity was living only in the assistant's own memory,
   invisible to any other session/device. User asked for these to stay
   fully separate files from the NIFTY docs to avoid merge conflicts.

## What happened next, same session (continued)

9. **Committed and pushed the cost-model fix**, then **deployed it
   live**: stopped the BTC service, backed up (not deleted) the
   corrupted portfolio state as `...portfolio.json.bak-buggy-loop`,
   deployed the fixed code, restarted clean at $10,000 Cash - confirmed
   live, holding a position normally with no more instant-close loop.

10. **Added ETH's own systemd unit** (`turion-crypto-options-eth`,
    `CRYPTO_CURRENCY=ETH`) - both BTC and ETH now live simultaneously,
    each its own process/portfolio/crash lifecycle.

11. **Built `crypto_app`** - a separate, standalone Flutter app (own
    APK), at the user's explicit ask ("same app style, but only this
    one trade"), not a tab added to the main `mobile_app`. Reads the
    same Firebase RTDB path the engine already writes to, via plain
    REST polling (no `firebase_database` SDK needed - the RTDB's read
    rules are already public). Installed on a real phone (Motorola
    Edge 20 Fusion, USB `adb install`) - found and fixed a real bug
    live: the release APK's `AndroidManifest.xml` was missing the
    INTERNET permission (debug builds get it for free via a Flutter
    tooling overlay; release doesn't), so the app loaded but every
    network call failed.

12. **Added a live candlestick chart + trade-detail sheet** to
    `crypto_app`, at the user's follow-up ask. Backend: `connect_and_
    run()` gained an `on_tick` callback (fires on every CE/PE ticker
    message) so `run_crypto_options_engine.py` can sync per-leg tick/
    candle history to Firebase, off a `ThreadPoolExecutor` so it never
    blocks the WebSocket loop. App: position/closed-trade cards are now
    tappable, showing entry/exit/lots and a REAL Deribit-taker-fee cost
    breakdown (not the main app's Rupee/NIFTY one), with a "View Chart"
    button into a polling-based candlestick screen.

13. **Found a second, more serious real problem**: LTP overstates real
    PnL by ~90-95% (`analyze_crypto_slippage.py`, comparing the "Net
    PnL" vs the already-recorded "Net PnL (Quote)" field on every
    trade) - BTC reported -$2,628.68 but a real bid/ask fill would have
    been -$51,464.47; ETH reported -$579.85 vs a real -$5,583.79. Root
    cause: the ATM weekly Deribit book's real bid-ask spread is wide
    enough that crossing it costs far more than LTP-based numbers show
    - same class of gap the NIFTY side found on 21-Aug-2026.

14. **Tested the known fix, then rolled it back**: wired the
    already-existing `rsi_momentum_quote_decide_fn` (real ask at entry,
    real bid at exit) into two NEW, separate books/systemd units
    (`_btc_quote`/`_eth_quote`) rather than changing the originals.
    Confirmed live: both immediately fell into a rapid stop-loss loop
    (~once/second, -$635/cycle BTC, -$59.77/cycle ETH) - not a bug, a
    real demonstration that the spread alone makes this book
    unviable at its current size/liquidity. Stopped and disabled both
    once the conclusion was clear (user's own call) - the two original
    LTP books were left running unchanged throughout.

15. **Updated both doc files** (this one + `CRYPTO_PROJECT_STATUS.md`)
    to record all of the above.

## Note on the date in this file's own name

CORRECTED - the note previously here was wrong. Checked against real
`git log` timestamps: steps 1-8 above (access check through the
candlestick-chart work) genuinely happened on **29-Aug-2026**, matching
this file's own name - correctly dated. Only steps 13-15 (the slippage
finding, the quote-based book experiment/rollback, and this doc pass
itself) happened after the session carried past midnight into
**30-Aug-2026** - a real, correct calendar-day rollover mid-session,
not a labeling mistake. Left in this one file rather than split across
two, since it's one continuous session/narrative - but steps 13-15
should be understood as 30-Aug-2026 work.

## Carried to next session

- Undecided: what to do about the real LTP-vs-spread gap (try a more
  liquid strike/expiry, reduce size, or accept the LTP books as
  signal-quality research only, not realistic paper P&L) - see
  `CRYPTO_PROJECT_STATUS.md`'s own "Next priorities".
- A real Deribit depth collector (mirroring `strategy/depth_
  collector.py`) was discussed as a way to explore the spread question
  further, explicitly NOT built - top-of-book bid/ask already answered
  the immediate viability question.
- Phase 5's mobile app is done (as `crypto_app`, not `crypto_screen.
  dart`) but the user was still testing it live as this session ended.
