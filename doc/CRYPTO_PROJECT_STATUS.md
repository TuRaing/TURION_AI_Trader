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
  - `turion-crypto-options-btc-profitlock` / `-eth-profitlock` — added
    30-Aug-2026, see "Profit-lock books" below. Separate books, not a
    change to the two above.
  - `turion-crypto-options-btc-rsi70` / `-eth-rsi70` — added
    31-Aug-2026, RSI 70/30 conviction threshold. See "RSI 70/30
    threshold books" below.
  - `turion-crypto-options-btc-rsi70-lock` — added 01-Sep-2026, RSI
    70/30 + `daily_loss_lock` (max 2 consecutive losses), BTC only.
    See "Combo sweep" below.

  All seven confirmed live and holding positions normally (no repeat
  of the stop-loss loop below) right after their own deploys.
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

  **Installed and verified on a real phone, same session** (Motorola
  Edge 20 Fusion, `adb install` over USB) - release APK size cut from
  140MB (debug) to 13-17MB via `flutter build apk --release
  --split-per-abi`. Found and fixed a real bug live: the release build
  loaded but every network call failed ("Failed host lookup") - the
  release `AndroidManifest.xml` was missing `<uses-permission
  android.permission.INTERNET/>` (debug builds get it automatically
  via a Flutter tooling manifest overlay; release needs it declared).

  **Candlestick chart + trade-detail sheet added same day**, at the
  user's own follow-up ask ("tick by tick candlestick सुद्धा दिसू दे").
  Position/closed-trade cards are now tappable -> a detail sheet
  (entry/exit/lots, a real cost breakdown using Deribit's actual 0.03%
  taker fee - NOT the main app's Rupee/NIFTY cost model) -> "View
  Chart" -> a live candlestick chart (Entry/Target/SL lines for the
  open position, Entry/Exit for a closed trade). Backend: `strategy/
  deribit_data.py`'s `connect_and_run()` gained an `on_tick` callback
  (fires on every CE/PE ticker message, independent of `on_action`);
  `run_crypto_options_engine.py` uses it to sync per-leg tick/candle
  history to the same `strategy_ticks`/`strategy_candles` Firebase
  paths the NIFTY side already uses, via a `ThreadPoolExecutor` so a
  blocking Firebase call never stalls the WebSocket loop at Deribit's
  100ms tick rate. `crypto_app` has no live Firebase Stream (see its
  own `api.dart`), so the chart polls the tick endpoint every 3s and
  client-side-aggregates the current forming candle, same bucket-merge
  logic the main app's Stream-based screen uses. Deployed to the VM
  (both systemd units restarted) and verified live: `strategy_ticks`
  confirmed populating for both BTC and ETH via a direct curl.

## Real finding: LTP overstates real PnL by ~90-95% (spread, not a bug)

Same class of gap the NIFTY side found on 21-Aug-2026, now confirmed
for crypto too. `analyze_crypto_slippage.py` (new script) compares two
fields already recorded on every closed trade - "Net PnL" (LTP-based,
what the live engine reports) against "Net PnL (Quote)" (real bid/ask
fill, reporting-only, already computed by `_rsi_momentum_decide()` but
never used to drive real decisions) - no new data collection needed.

Result on the first ~1.5 days of real live trading:

| | BTC (83 trades) | ETH (77 trades) |
|---|---|---|
| Net PnL (LTP) | -$2,628.68 | -$579.85 |
| Net PnL (Quote, real fill) | **-$51,464.47** | **-$5,583.79** |
| LTP overstates by | +94.9% | +89.6% |

**Root cause:** the ATM weekly Deribit options book is thin - the real
bid-ask spread is wide enough that crossing it (buying at the real
ask, selling at the real bid) costs far more than the LTP-based
numbers ever showed.

**Tested the fix, then rolled it back (same day):** wired
`rsi_momentum_quote_decide_fn` (already existed - the exact fix the
NIFTY side used for its own 21-Aug version of this problem) into two
NEW, separate books (`rsi_momentum_crypto_btc_quote` / `_eth_quote`,
`CRYPTO_QUOTE_BASED=1`, own systemd units
`turion-crypto-options-{btc,eth}-quote`) rather than changing the
original LTP books - confirmed live: BOTH immediately fell into a
rapid open/close stop-loss loop (BTC ~-$635/cycle, ETH ~-$59.77/cycle,
about once a second) - not a bug, the real spread genuinely triggers
the stop-loss cap on nearly every single entry. **Stopped and disabled
both quote-based units** (user's own call, "थांबव") once the
conclusion was clear - running them further would only keep burning
paper cash to no new insight. The two original LTP books were left
running unchanged throughout.

**Where this leaves the project:** the RSI-momentum signal itself may
have real edge, but at the CURRENT position size / instrument
liquidity (ATM weekly, `lot_size=1`), the real bid-ask spread alone
appears to make this book unviable - a materially different
conclusion from what the LTP-based numbers alone would suggest. A real
Deribit order-book depth collector (mirroring `strategy/depth_
collector.py`'s NIFTY equivalent) was discussed as a way to explore
this further (does a more liquid strike/expiry help? does smaller size
help?) but explicitly NOT built yet - the top-of-book bid/ask already
gave a clear, decisive answer to the immediate question ("is this
viable right now"), so the added infra wasn't justified yet.

## Profit-lock books (BTC/ETH), 30-Aug-2026

Separate follow-up experiment, same session: real trade analysis found
both LTP books whipsawing well under their own breakeven win rate
(BTC 23.3% vs 31.8% needed, ETH 18.1% vs 29.0% needed), median ~9-min
holds - re-entering right after almost every stop-loss. Backtested
`daily_profit_lock` (already existed in `make_st2_threshold_event_cfg`,
unused by crypto until now) as the fix, using a genuinely **rolling**
window instead of that field's normal UTC-calendar-day boundary (a
24/7 market has no real "today" - see `strategy/crypto_tick_runner.py`'s
new `_realized_pnl_within_hours()`).

**`daily_loss_lock`/`max_consecutive_losses` was tried FIRST and
rejected** - made BTC notably worse in a proper apples-to-apples
backtest (a first, flawed comparison had wrongly suggested it helped -
each variant was independently refetching "the last 7 days from right
now" from a live API, so time moving forward between calls meant every
variant silently ran on different data; fixed by fetching data_points
once and reusing them - see `run_for()`'s own note in `crypto_options_
backtest.py`).

**`daily_profit_lock` DOES help, but needs a per-currency-tuned
window** - a full parameter sweep (0.5-3% x 1-8h, two different real
7-day windows each) found:
- **BTC: 1% / 2h window** - the ONLY window where both tested real
  windows improved over baseline (recent: -$3,391 -> +$3,620; older:
  +$9,045 -> +$9,758). Every other window (1h/3h/4h/6h/8h) helped one
  window while making the OTHER one worse than baseline - not a robust
  choice.
- **ETH: 0.5% / 3h window** - the 2h window that worked for BTC was
  actually one of the WORSE choices for ETH (its much smaller average
  win, ~$56 vs BTC's ~$528, means the exact window length matters more
  than the exact %, which barely matters at all above ~0.5% since a
  single win crosses every threshold from 0.5-3% at once).
- A trailing-stop was also tried stacked on the 12h BTC variant
  (`trailing_min_pct=3.0`) - made things dramatically worse (9 trades,
  -$7,021 vs the 12h-alone -$2,585) - not pursued further.
- Went looking for an even OLDER real window to triple-check
  consistency - not possible: Deribit's public API only retains
  already-expired instruments for `settlement_period="day"`, not
  `"week"` - last week's weekly BTC contract's real trade history is
  already gone entirely. The two windows tested (recent + `offset_
  days=3`) are close to the full real range this specific weekly
  contract has ever had.

**Deployed as two NEW, separate books** (not a change to the original
LTP books, same "never silently change a running book" rule as the
quote-based experiment) - `rsi_momentum_crypto_btc_profitlock` /
`_eth_profitlock`, via `CRYPTO_PROFIT_LOCK_PCT`/`CRYPTO_PROFIT_LOCK_
WINDOW_HOURS` env vars, `deploy/turion-crypto-options-{btc,eth}-
profitlock.service`. `crypto_app` gained two matching tabs (now 4
total, TabBar made scrollable) - the original BTC/ETH tabs are
unchanged, per the user's explicit "old strategy चालू राहू द्या" ask.

**Trailing-stop capability added to the shared engine** (`strategy/
event_driven_engine.py`'s new opt-in `trailing_min_pct`, ported from
`strategy/fyers_options_engine.py`'s own NIFTY version) as a side
effect of testing it above - unlike the NIFTY version (which couldn't
be backtested at all - Entry/Exit-only historical records), this DOES
work in `crypto_options_backtest.py` since `rsi_momentum_decide_fn`
already runs against every intermediate 5-min data point. Not
currently used by any live crypto book (the one combination tried made
things worse) - kept as a real, reusable, tested capability for future
experiments, not dead code.

### [FIXED, 30-Aug-2026] Both profit-lock books crashed within minutes of deploy

**Symptom:** `turion-crypto-options-btc-profitlock` and `-eth-profitlock`
both went to systemd `failed` state (exhausted their 5-restarts/300s
limit) within ~10-15 minutes of first going live - silently down for
~2.5 hours before being noticed via a direct `systemctl status` check.

**Root cause:** `TypeError: can't compare offset-naive and offset-aware
datetimes` inside the brand-new `_realized_pnl_within_hours()`.
`CryptoTickRunner.on_tick()` receives a timezone-AWARE timestamp on the
real Deribit path (`strategy/deribit_data.py`'s `connect_and_run()`
builds it via `datetime.fromtimestamp(..., tz=utc)`), but every stored
Entry/Exit Time string is naive - comparing the two raises immediately.
Never caught in `crypto_options_backtest.py`'s own testing (all its
timestamps are naive, via `strptime()`), so the bug only existed on
the live path, invisible to every backtest run this session already
did.

**Fix:** strip `tzinfo` at the top of `_realized_pnl_within_hours()`,
matching the already-live-proven `_today_consecutive_losses()`'s own
naive convention. Added `tests/test_crypto_tick_runner.py`'s
`test_profit_lock_gate_works_with_a_timezone_aware_timestamp()` - the
only test in that file that deliberately builds an aware timestamp -
so this exact class of bug can't silently regress again.

**Deployed and verified, 30-Aug-2026:** `sudo systemctl reset-failed`
+ restart on both units, confirmed active and holding positions
normally afterward. Checked both ETH books directly via Firebase
shortly after: original ETH book at 111 closed trades (continuing its
known whipsaw pattern, unlocked - expected, not a bug), profit-lock
ETH book showing exactly 1 real closed trade from before the crash
(-$26.14, ~14.5min hold - normal, not a loop) plus a fresh position
opened cleanly right after the restart.

**Lesson worth remembering:** a live crypto WebSocket path and this
project's own backtest replay do NOT automatically exercise the same
timestamp representation (aware vs naive) even when they call the
exact same shared decide_fn - any new helper that touches `timestamp`
directly (not just cfg/data_point fields) needs to be checked against
BOTH paths, not just backtested, before it's trusted live.

## RSI 70/30 threshold books (BTC/ETH), 31-Aug-2026

Real finding: a plain `RSI>=50` midpoint split fires on every marginal
RSI wobble on a choppy day - a real 31-Aug session showed this
disproportionately hurts PE (down-direction) entries (BTC profit-lock
book that day: PE -$3,991 net vs CE -$130 net). New opt-in
`rsi_ce_threshold`/`rsi_pe_threshold` in `event_driven_engine.py`
(both default 50 - byte-identical split, no neutral zone, for every
existing book). A backtest sweep found `CE>=70`/`PE<=30` (genuine
conviction required for either side) flips both BTC and ETH from a
real backtest loss to a real profit, and critically PE trades
THEMSELVES turn profitable too (not just filtered out) - ETH:
+$2,064/+$2,067 across two different real windows, near-identical;
BTC: +$11,157 on the one window with enough real liquidity to test.
Deployed as two new, separate books
(`rsi_momentum_crypto_{btc,eth}_rsi70`) via `CRYPTO_RSI_CE_THRESHOLD`/
`CRYPTO_RSI_PE_THRESHOLD` env vars.

## [FOUND, 04-Sep-2026] Near-expiry lot-size blowup - a real risk, not a bug

**Symptom:** BTC's plain LTP book showed one single trade worth
+$16,722.17 (56 lots!) among a 320-trade, +$23,193 day - a wildly
larger swing than any prior day.

**Root cause:** ATM is picked ONCE at each book's own startup, never
re-derived as the contract approaches its own expiry (a documented
limitation since Phase 2). The currently-held contract
(`BTC-4SEP26-81000-P`) was expiring THAT SAME DAY. As real expiry
nears, an option's time value collapses toward zero - and lot sizing
(`lots = initial_capital // (entry_premium * lot_size)`) is inversely
proportional to premium, so a crashing premium makes lot counts
balloon (56, 94, 123, 136, 153 lots seen live, vs the normal 5-20).
Every subsequent % move now swings a proportionally huge dollar
amount - both wins (+$16,722 on one trade) and losses (~$1,000-1,100
per Stop-Loss, vs the normal ~$200) blow up together, right at the
point in a contract's life where this is least expected.

**Not fixed yet** - flagged live, user asked about immediate stop vs
riding out the ~6 hours to real expiry; no code change made this
session. A real fix would need either (a) re-deriving/rolling ATM to
a fresh, longer-dated contract as expiry approaches (mirrors
`event_driven_runner.py`'s own documented ATM-drift limitation on the
NIFTY side), or (b) a hard cap on lots/notional regardless of how
cheap premium gets. Carried to next session.

## [ADDED, 01-Sep-2026] Stop new entries once a book's capital hits zero

User's own explicit ask - "balance minus मध्ये जातायत... zero झालं की
stop व्हायला हवं". Position sizing has always used the FIXED
`initial_capital`, never the live shrinking Cash (deliberate "paper
bookkeeping, not a real spending constraint" choice already used
elsewhere in this project), so without a gate a book keeps opening
full-size positions forever even once its own realized Cash has gone
deeply negative - confirmed live: BTC at -$5,791, ETH at -$688 before
this was added.

New opt-in `stop_at_zero_capital` in `event_driven_engine.py`/
`make_st2_threshold_event_cfg` (default `False` - every existing
NIFTY/BankNifty book unchanged). Only blocks NEW entries - an
already-open position still runs to its own Target/Stop-Loss.
`strategy/crypto_tick_runner.py` now always includes `current_cash` in
the live `data_point`. Enabled unconditionally for ALL crypto books
(not opt-in per book like the performance experiments) - this is a
risk-control fix, not something to A/B test.

**Manually topped up once, same day** - after the gate correctly
stopped BTC/ETH (plain) and BTC profit-lock (which itself later fell
from +$6,775 all-time to -$10,080 after a single -$16,197 day, then
hit the zero-capital stop too), the user asked to refill the ones that
had run out. Reused the NIFTY side's own established `_maybe_top_up_
capital()` record shape (`portfolio["Capital Top-ups"]`: Time, Cash
Before, Topped Up To) for consistency/transparency, applied as a
one-time manual edit to each VM portfolio JSON (services stopped,
`sudo python3` edit needed - the JSON files are root-owned since the
systemd units run as root, `python3` edit, services restarted). NOT
an automatic recurring top-up - the zero-capital stop gate stays as
the real safety net; this was a one-off "let me watch it again"
refill, not a policy change.

## Combo sweep (RSI threshold x daily_loss_lock x trend confirmation), 01-Sep-2026

Real trigger: BTC RSI-70/30 took 9 consecutive PE Stop-Losses in 12
minutes on 4-Sep - spot trending steadily UP while RSI kept reading
oversold on the fast (5-min) view ("RSI divergence"), so even the
70/30 conviction gate didn't prevent every single entry from being
wrong in the same direction.

Three candidate fixes were built and swept, separately and combined,
across two real windows per currency:
1. **`daily_loss_lock`** (already existed, max 2 consecutive losses,
   UTC-calendar-day) stacked on RSI 70/30.
2. **RSI 80/20** (even more conviction required) alone.
3. **New: `require_trend_confirmation`** (`event_driven_engine.py`,
   opt-in) - CE only if spot is above its own EMA, PE only if below.
   `crypto_options_backtest.py` computes a 1-hour spot EMA
   (`spot_ema`, `EMA_PERIOD=12` at 5-min resolution) for this.

**Result: `RSI 70/30 + daily_loss_lock` was the ONLY variant positive
in BOTH tested real windows for BTC** (recent: -$1,172 -> +$5,189;
older: still +$10,525, from +$12,902 baseline). RSI 80/20 alone was
wildly inconsistent (as good as +$1,637/64.7% win on ETH, as bad as
-$6,223/0% win on BTC's thin recent window - only 3 trades, not a
trustworthy sample either way). **`require_trend_confirmation` showed
close to NO effect in the tested windows** - several results were
byte-identical to the same run without it, meaning the EMA gate
rarely actually blocked anything in this specific data - built for a
real problem, but not validated as the fix by this particular
backtest. ETH did not show the same loss-lock benefit BTC did.

Deployed BTC-only: new `rsi_momentum_crypto_btc_rsi70_lock` book via
`CRYPTO_DAILY_LOSS_LOCK`/`CRYPTO_MAX_CONSECUTIVE_LOSSES` on top of the
existing RSI-70/30 env vars, alongside (not replacing) the plain
RSI-70/30 book. `require_trend_confirmation` was added as real,
tested, reusable capability (own regression tests) but is NOT used by
any live book yet - the sweep didn't show it earning its complexity
for this problem.

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

1. Decide what to do about the LTP-vs-real-spread gap above - options
   discussed but not decided: try a more liquid strike/expiry, reduce
   position size, or accept this book as LTP-only-for-signal-research
   (not a realistic paper P&L) until spread is addressed.
2. Let the two original (LTP) BTC/ETH books keep running live and
   watch real paper results now that the cost-model bug is fixed -
   still useful as an RSI-signal-quality signal even though the
   Quote-based PnL is what would actually happen.
3. User is testing the installed phone app (candlestick chart, trade
   detail sheet, now 4 tabs including the two new profit-lock books)
   live - no reported issues yet, follow up next session if any come
   back.
4. Let the two new profit-lock books run live for a few weeks and see
   if the backtest-tuned improvement holds up on real forward data,
   same "single-window backtest isn't proof" caution as everywhere
   else in this doc.
5. **Not yet fixed:** the near-expiry lot-size blowup (see that
   section above) - BTC's plain LTP book is currently exposed to it
   right now, live. Needs a real decision: re-derive ATM as expiry
   nears, or cap lots/notional outright.
6. Watch whether BTC RSI-70/30+lock actually holds up forward - the
   backtest evidence is real but from a small sample (same caution as
   everywhere else). ETH still has no loss-lock variant (didn't help
   in the sweep).
7. Now 7 live books total (2 plain, 2 profit-lock, 2 RSI-70/30, 1
   RSI-70/30+lock) + matching `crypto_app` tabs - the app is getting
   crowded; consider whether some early/weaker variants (e.g. plain
   BTC/ETH, which exist mainly for LTP-vs-Quote comparison research at
   this point) should eventually be trimmed from the app view, once
   there's enough live history to not need them for reference anymore.

## Note on dates in this doc and its commits

CORRECTED - the note previously here was itself wrong. Checked against
real `git log` timestamps: everything through the candlestick-chart
work genuinely happened on **29-Aug-2026** (commits up to and
including `63969f714`, 15:48) - correctly dated throughout. Only the
LATER work - `analyze_crypto_slippage.py`, the quote-based book
experiment/rollback, and this doc's own completion pass (commits
`fbfe0786a` onward, starting ~18:36) - happened after the session
carried past midnight into **30-Aug-2026**. That's a real, correct
calendar-day rollover mid-session, not a labeling mistake - so text
in this file describing that later work should say 30-Aug-2026, not
29-Aug-2026, if it names a date at all.
