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

## Not yet done (carried to next session)

- Local fix is NOT yet committed to git.
- The live VM is still running the OLD buggy code, with the corrupted
  (-$26,545 Cash) portfolio state from the loop — needs: stop the
  service, reset the portfolio state file, deploy the fixed code,
  restart.
- Whether to push these two new doc files (and the code fix) to
  `main` or keep them on `crypto-paper-trading` was raised but not
  resolved — the user's own repeated hard constraint is to never touch
  `main` (the branch the live NIFTY VPS deploys from), which is in
  tension with CLAUDE.md's general "docs live on main" rule. Punted to
  keeping crypto docs on `crypto-paper-trading` for now, given the
  user's explicit separate-file ask this session.
- ETH's own systemd unit not created yet (BTC-only live so far).
- Phase 5 (mobile `crypto_screen.dart`) not started.
