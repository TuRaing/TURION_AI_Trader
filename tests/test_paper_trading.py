import json

import strategy.paper_trading as pt
from strategy.paper_trading import process_signal, load_portfolio


def _empty():
    return {"Cash": 100000, "Positions": {}, "Closed Trades": []}


def test_open_buy_position():
    p = _empty()
    p, action = process_signal(p, "HDFCBANK", "BUY", 800, stop_loss=790, target=820)
    assert action == "OPENED BUY"
    assert "HDFCBANK" in p["Positions"]


def test_no_open_without_buy():
    p = _empty()
    p, action = process_signal(p, "HDFCBANK", "NO TRADE", 800)
    assert action == "HOLD"
    assert p["Positions"] == {}


def test_target_hit_closes_with_profit():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, action = process_signal(p, "X", "NO TRADE", 825)  # above target
    assert action == "CLOSED (Target)"
    assert "X" not in p["Positions"]
    assert p["Cash"] == 100000 + (820 - 800)  # exits at target price
    assert p["Closed Trades"][-1]["PnL"] == 20


def test_stop_loss_hit_closes_with_loss():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, action = process_signal(p, "X", "NO TRADE", 785)  # below stop
    assert action == "CLOSED (Stop Loss)"
    assert p["Cash"] == 100000 + (790 - 800)  # exits at stop price
    assert p["Closed Trades"][-1]["PnL"] == -10


def test_sell_signal_closes_open_position():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, action = process_signal(p, "X", "SELL", 810)
    assert action == "CLOSED (Signal Exit)"
    assert p["Closed Trades"][-1]["Exit Reason"] == "Signal Exit"


def test_positions_are_independent():
    p = _empty()
    p, _ = process_signal(p, "A", "BUY", 100, stop_loss=95, target=110)
    p, _ = process_signal(p, "B", "BUY", 200, stop_loss=190, target=220)
    p, _ = process_signal(p, "A", "NO TRADE", 111)  # A hits target
    assert "A" not in p["Positions"]
    assert "B" in p["Positions"]  # B untouched


def test_old_schema_migration(tmp_path, monkeypatch):
    old = {
        "Cash": 100000,
        "Position": {"Entry Time": "t", "Entry Price": 100, "Quantity": 1, "Stop Loss": 95, "Target": 110},
        "Closed Trades": [],
    }

    f = tmp_path / "portfolio.json"
    f.write_text(json.dumps(old))

    monkeypatch.setattr(pt, "PORTFOLIO_FILE", str(f))

    migrated = load_portfolio()

    assert "Positions" in migrated
    assert "Position" not in migrated
    assert "NIFTY 50" in migrated["Positions"]


def test_missing_file_returns_fresh_portfolio(tmp_path, monkeypatch):
    monkeypatch.setattr(pt, "PORTFOLIO_FILE", str(tmp_path / "does_not_exist.json"))
    p = load_portfolio()
    assert p["Cash"] == pt.INITIAL_CAPITAL
    assert p["Positions"] == {}
    assert p["Closed Trades"] == []
