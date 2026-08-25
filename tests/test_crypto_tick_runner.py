import datetime
import json
import os
import shutil
import tempfile

from strategy.event_driven_engine import rsi_momentum_decide_fn, make_st2_threshold_event_cfg
from strategy.live_tick_harness import MIN_CANDLES_FOR_RSI
from strategy.crypto_tick_runner import CryptoTickRunner, load_portfolio, save_portfolio
import strategy.crypto_tick_runner as crypto_tick_runner_module

import pandas as pd


def _ts(minute, second=0, hour=9, day=24):
    return datetime.datetime(2026, 8, day, hour, minute, second)


def _seeded_candles(n, start_price=100.0):
    """n closed candles, mildly uptrending - same fixture shape as
    tests/test_live_tick_harness.py's own _seeded_candles()."""
    rows = []
    idx = []
    price = start_price
    base = datetime.datetime(2026, 8, 24, 0, 0)
    for i in range(n):
        price += 1
        rows.append({"Open": price, "High": price + 0.5, "Low": price - 0.5, "Close": price})
        idx.append(base + datetime.timedelta(minutes=5 * i))
    return pd.DataFrame(rows, index=idx)


class _SpyBackend:
    def __init__(self):
        self.opens = []
        self.closes = []

    def on_open(self, cfg, position):
        self.opens.append((cfg, position))

    def on_close(self, cfg, trade_record):
        self.closes.append((cfg, trade_record))


def _runner(execution_backend=None, closed_trades=None):
    cfg = make_st2_threshold_event_cfg(index="BTC", lot_size=1, initial_capital=10000)
    portfolio = {"Cash": 10000, "Position": None, "Closed Trades": closed_trades or []}
    seeded = _seeded_candles(MIN_CANDLES_FOR_RSI + 5)  # RSI ready from tick 1

    return CryptoTickRunner(
        decide_fn=rsi_momentum_decide_fn,
        cfg=cfg,
        portfolio=portfolio,
        underlying_index_name="BTC",
        ce_symbol="BTC-25AUG26-68000-C",
        pe_symbol="BTC-25AUG26-68000-P",
        initial_candles=seeded,
        execution_backend=execution_backend,
    )


def test_tick_for_untracked_symbol_is_ignored():
    runner = _runner()

    result = runner.on_tick("ETH", _ts(20), 3000.0)

    assert result is None
    assert runner.portfolio["Position"] is None


def test_ce_tick_before_any_underlying_tick_is_held_back():
    runner = _runner()

    result = runner.on_tick(runner.ce_symbol, _ts(20), 0.001)

    assert result is None  # no spot/RSI context yet


def test_underlying_tick_with_seeded_rsi_can_open_a_position():
    runner = _runner()

    # Seeded candles are a steady uptrend -> RSI comfortably >= 50 -> CE.
    runner.on_tick(runner.underlying_index_name, _ts(20), 79000.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert action is not None
    assert "OPENED CE" in action
    assert runner.portfolio["Position"]["Option Type"] == "CE"


def test_full_open_then_target_close_sequence_via_ticks():
    runner = _runner()

    runner.on_tick(runner.underlying_index_name, _ts(20), 79000.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE

    action = runner.on_tick(runner.ce_symbol, _ts(21), 115.0)  # jumps to Target

    assert "CLOSED (Target)" in action
    assert runner.portfolio["Position"] is None
    assert len(runner.portfolio["Closed Trades"]) == 1
    assert runner.portfolio["Cash"] > 10000


def test_open_and_close_notify_execution_backend():
    backend = _SpyBackend()
    runner = _runner(execution_backend=backend)

    runner.on_tick(runner.underlying_index_name, _ts(20), 79000.0)
    runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)  # opens CE
    runner.on_tick(runner.ce_symbol, _ts(21), 115.0)  # Target close

    assert len(backend.opens) == 1
    assert backend.opens[0][1]["Option Type"] == "CE"
    assert len(backend.closes) == 1
    assert backend.closes[0][1]["Exit Reason"] == "Target"


def test_runner_without_a_backend_defaults_to_a_working_no_op():
    runner = _runner()

    runner.on_tick(runner.underlying_index_name, _ts(20), 79000.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "OPENED CE" in action


def test_data_point_never_marks_past_squareoff_or_before_market_open():
    # Crypto is 24/7 - a tick at any hour, including deep "after hours"
    # for the NIFTY engine, must never be skipped/force-closed on either
    # gate (see strategy/event_driven_engine.py's rsi_momentum_decide_fn
    # - both gates only ever fire when the data_point sets them True).
    runner = _runner()

    runner.on_tick(runner.underlying_index_name, _ts(0, hour=2), 79000.0)  # 02:00 - "before market open" for NIFTY
    action = runner.on_tick(runner.ce_symbol, _ts(1, hour=2), 100.0)

    assert "SKIPPED (before market open)" not in action
    assert "SKIPPED (past square-off time)" not in action


def test_today_consecutive_losses_gates_new_entries_via_daily_loss_lock():
    # Confirms the shared _today_consecutive_losses (imported unchanged
    # from live_tick_harness.py) actually reaches decide_fn through
    # CryptoTickRunner's own data_point assembly.
    cfg = make_st2_threshold_event_cfg(
        index="BTC", lot_size=1, initial_capital=10000, daily_loss_lock=True, max_consecutive_losses=2,
    )
    todays_losses = [
        {"Entry Time": "2026-08-24 09:00:00", "Exit Time": "2026-08-24 09:05:00", "Net PnL": -50},
        {"Entry Time": "2026-08-24 09:06:00", "Exit Time": "2026-08-24 09:10:00", "Net PnL": -30},
    ]
    portfolio = {"Cash": 10000, "Position": None, "Closed Trades": todays_losses}
    seeded = _seeded_candles(MIN_CANDLES_FOR_RSI + 5)

    runner = CryptoTickRunner(
        decide_fn=rsi_momentum_decide_fn, cfg=cfg, portfolio=portfolio,
        underlying_index_name="BTC", ce_symbol="BTC-25AUG26-68000-C", pe_symbol="BTC-25AUG26-68000-P",
        initial_candles=seeded,
    )

    runner.on_tick(runner.underlying_index_name, _ts(20), 79000.0)
    action = runner.on_tick(runner.ce_symbol, _ts(20, 1), 100.0)

    assert "SKIPPED (today already has 2+ consecutive losses" in action


# --- load_portfolio / save_portfolio (atomic write, graceful degradation) ---

def test_save_then_load_round_trips():
    tmp_dir = tempfile.mkdtemp()
    old_dir = crypto_tick_runner_module.PORTFOLIO_DIR
    crypto_tick_runner_module.PORTFOLIO_DIR = tmp_dir
    try:
        portfolio = {"Cash": 12345.0, "Position": None, "Closed Trades": [{"Net PnL": 1.0}]}
        save_portfolio("rsi_momentum_crypto_btc", portfolio)

        loaded = load_portfolio("rsi_momentum_crypto_btc")

        assert loaded == portfolio
    finally:
        crypto_tick_runner_module.PORTFOLIO_DIR = old_dir
        shutil.rmtree(tmp_dir)


def test_load_missing_file_returns_a_fresh_portfolio():
    tmp_dir = tempfile.mkdtemp()
    old_dir = crypto_tick_runner_module.PORTFOLIO_DIR
    crypto_tick_runner_module.PORTFOLIO_DIR = tmp_dir
    try:
        loaded = load_portfolio("nonexistent_book", initial_capital=5000)

        assert loaded == {"Cash": 5000, "Position": None, "Closed Trades": []}
    finally:
        crypto_tick_runner_module.PORTFOLIO_DIR = old_dir
        shutil.rmtree(tmp_dir)


def test_load_corrupt_file_degrades_gracefully_instead_of_raising():
    tmp_dir = tempfile.mkdtemp()
    old_dir = crypto_tick_runner_module.PORTFOLIO_DIR
    crypto_tick_runner_module.PORTFOLIO_DIR = tmp_dir
    try:
        path = os.path.join(tmp_dir, "crypto_broken_portfolio.json")
        with open(path, "w") as f:
            f.write("{not valid json")

        loaded = load_portfolio("broken", initial_capital=5000)

        assert loaded == {"Cash": 5000, "Position": None, "Closed Trades": []}
    finally:
        crypto_tick_runner_module.PORTFOLIO_DIR = old_dir
        shutil.rmtree(tmp_dir)


def test_load_empty_file_degrades_gracefully_instead_of_raising():
    tmp_dir = tempfile.mkdtemp()
    old_dir = crypto_tick_runner_module.PORTFOLIO_DIR
    crypto_tick_runner_module.PORTFOLIO_DIR = tmp_dir
    try:
        path = os.path.join(tmp_dir, "crypto_empty_portfolio.json")
        open(path, "w").close()  # simulates a killed process mid-write

        loaded = load_portfolio("empty", initial_capital=5000)

        assert loaded == {"Cash": 5000, "Position": None, "Closed Trades": []}
    finally:
        crypto_tick_runner_module.PORTFOLIO_DIR = old_dir
        shutil.rmtree(tmp_dir)
