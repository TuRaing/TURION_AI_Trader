# TURION Crypto Paper-Trading — Project Status

Separate status file for the Deribit BTC/ETH options paper-trading
sub-project, kept apart from `doc/PROJECT_STATUS.md` (the NIFTY/
BankNifty live-trading system's own status file) on purpose — this
sub-project lives on the `crypto-paper-trading` branch, not `main`,
and the user's explicit ask is to avoid any merge conflict with the
NIFTY-side docs. Update THIS file for crypto work; leave the NIFTY
`PROJECT_STATUS.md` alone.

## What this is

Deribit (BTC/ETH options) paper-trading, fully separate from the
NIFTY/BankNifty live-trading system — reuses the existing, proven
RSI-momentum signal (`rsi_momentum_decide_fn`) unchanged, applied to
real Deribit market data instead of Fyers/NSE data.

## Phase status

- **Phase 1 (branch)** — done. `crypto-paper-trading` branch, pushed
  to origin.
- **Phase 2 (pure core + local backtest)** — done. Validated the
  existing RSI-momentum signal against real historical Deribit data
  before building anything new.
- **Phase 3 (live-wiring code-prep)** — done.
  `run_crypto_options_engine.py`, `sync_portfolio()` under key
  `rsi_momentum_crypto_<currency>`.
- **Phase 4 (standalone VM + deploy)** — done, 29-Aug-2026, BTC and
  ETH both live. Oracle Cloud Always Free VM: Ubuntu 26.04 aarch64,
  Ampere A1 (2 OCPU/12GB), India West (Mumbai), public IP
  `129.154.227.170`, hostname `turion-crypto-vm`. SSH as `ubuntu`, key
  at `C:\Users\TuriON\Downloads\ssh-key-2026-08-29.key` (dev machine).
  Code at `~/turion-crypto` (deployed via `git archive` + `scp`, not a
  git clone — the VM has no GitHub credentials by design). Two
  independent systemd units, one per currency (each its own WebSocket
  connection, portfolio file, and crash/restart lifecycle):
  - `turion-crypto-options` — BTC, `rsi_momentum_crypto_btc`, $10,000
    capital.
  - `turion-crypto-options-eth` — ETH, `rsi_momentum_crypto_eth`, Rs
    1,00,000-equivalent ($1,047.89) capital. Added 29-Aug-2026,
    `deploy/turion-crypto-options-eth.service` (mirrors the BTC unit,
    only `Description` and `Environment="CRYPTO_CURRENCY=ETH"` differ).

  Both confirmed live and holding positions normally (no repeat of the
  stop-loss loop below) right after deploy.
- **Phase 5 (mobile app)** — done differently than originally planned,
  29-Aug-2026: instead of adding a `crypto_screen.dart` tab to the
  main `mobile_app`, the user explicitly asked for a **separate,
  standalone Flutter app** — `crypto_app/` at the repo root, own
  `pubspec.yaml`/APK, same dark-neon theme as the main app but showing
  only the two crypto books (BTC/ETH), none of the ~60 NIFTY/BankNifty
  ones. Reads the same Firebase RTDB path
  (`event_driven_portfolios/{strategy_name}`) `run_crypto_options_
  engine.py` already writes to, via plain HTTPS REST polling (the
  RTDB's read rules are already public — confirmed live — so no
  `firebase_core`/`firebase_database` SDK or Firebase Console app
  registration needed). `flutter analyze` clean, `flutter test`
  passes, and a built web version was visually verified against the
  real live VM data (BTC open position, ETH's first closed trade) via
  the browser before committing.

## Redeploying code to the VM

```
git archive --format=tar.gz -o /tmp/x.tar.gz HEAD -- <paths>
scp /tmp/x.tar.gz ubuntu@129.154.227.170:~/
ssh ubuntu@129.154.227.170 "tar -xzf ~/x.tar.gz -C ~/turion-crypto && sudo systemctl restart turion-crypto-options"
```
`git archive` only picks up COMMITTED content — uncommitted local
changes are silently skipped.

## Known issues

### [FIXED, 29-Aug-2026] Rapid open/close stop-loss loop — wrong-currency transaction costs

**Symptom:** both the live VM engine and a clean local backtest got
stuck opening and immediately stop-lossing a position every single
5-min candle — 553 trades in 44 minutes live (portfolio Cash went to
-$26,545 on a $1,047.89 starting capital), 967 trades / 0.5% win rate
over a 7-day ETH backtest.

**Root cause:** `strategy/event_driven_engine.py`'s `_net_pnl()` was
calling `strategy/options_transaction_costs.py`'s
`calculate_options_round_trip_cost()` — a cost model calibrated in
**INR** for NIFTY/BankNifty (`BROKERAGE_PER_ORDER = Rs 20` flat, per
order) — directly on **USD** Deribit premiums, with no currency
conversion. A real ₹20 brokerage fee was being subtracted as **$20**,
~95x too large at the real USD/INR rate. On a small crypto position
(~$1,000-1,500 notional) this fixed cost alone was enough to force
almost every trade into a loss regardless of real price movement.

**Fix:** new `strategy/crypto_transaction_costs.py` with a
Deribit-realistic, USD-native cost model (percentage-of-premium taker
fee, no flat INR-denominated brokerage). `_net_pnl()` now accepts an
opt-in `cfg["cost_fn"]` override (default `None` → unchanged NIFTY
cost model, zero behavior change for the other 59 live books).
`make_st2_threshold_event_cfg()` gained a matching `cost_fn=None`
parameter. Both crypto call sites (`crypto_options_backtest.py`,
`run_crypto_options_engine.py`) now pass
`calculate_crypto_options_round_trip_cost`.

**Verified:** `tests/test_event_driven_engine.py` +
`tests/test_event_driven_runner.py` — 74/74 pass (no NIFTY
regression). Clean backtest re-run: ETH went from 967 trades/0.5% win
to 31 trades/35.5% win — same normal-looking behavior as BTC's 48
trades/41.7% win. Both currencies now show a realistic loss over this
particular 7-day window (BTC -$8,348, ETH -$1,301) — a genuine
strategy-performance result, not a bug (a prior backtest window
showed +$7,716 on the same signal — small-sample variance is expected
and already documented behavior for this signal).

**Deployed live, 29-Aug-2026:** stopped the BTC service, backed up
(not deleted) the corrupted portfolio state as
`reports/crypto_rsi_momentum_crypto_btc_portfolio.json.bak-buggy-loop-29aug26`
on the VM, deployed the fixed code, restarted with a clean $10,000
Cash. Confirmed live: position opens once and is HELD normally as the
real premium moves (no more instant-close loop). ETH's own systemd
unit was created the same session (see Phase 4 above) and came up
clean from the start, never having run the buggy cost model live.

## Architecture decisions on record

- **Standalone VPS, not GitHub Actions polling** — chosen for real
  tick-by-tick WebSocket precision (`connect_and_run()` in
  `strategy/deribit_data.py`), not 5-min-polling precision.
- **Oracle Cloud "Always Free" tier**, Ampere A1 shape — confirmed
  genuinely free indefinitely as long as the account is never manually
  upgraded to Pay-As-You-Go.
- **Firebase** — reuses the same Firebase project/credentials already
  configured for the NIFTY VPS, no new project needed.
- **Capital split (29-Aug-2026, user's explicit ask):** BTC at $10,000
  (an amount that can actually afford 1 lot at real BTC option
  premiums, $1,500-2,500+) and ETH at the Rs 1,00,000-equivalent
  ($1,047.89) separately — Deribit's `lot_size=1` means 1 contract =
  1 full coin notional, so one fixed capital figure doesn't fit both
  currencies' very different real contract economics.
- **Scope:** BTC first (validated), ETH as a deliberate fast-follow —
  both now live simultaneously as of 29-Aug-2026, each its own
  systemd unit (see Phase 4 above), not a single shared process.

## Next priorities

1. Let BTC and ETH run live for a while and watch real paper results
   (win rate, trade frequency) now that the cost-model bug is fixed.
2. Install `crypto_app`'s debug APK on a real phone and confirm it
   still renders correctly outside a browser (web build was the
   verification so far — see Phase 5 above).
