import json

import strategy.paper_trading as pt
from strategy.paper_trading import (
    process_signal,
    load_portfolio,
    calculate_position_size,
    run_watchlist_paper_trading,
)
from strategy.delivery_transaction_costs import calculate_delivery_round_trip_cost


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
    # Gross PnL (unchanged field) vs real Cash impact (net of delivery
    # transaction costs - added 08-Aug-2026, see delivery_transaction_
    # costs.py) are now two different numbers.
    cost = calculate_delivery_round_trip_cost(800, 820, 1)
    assert p["Cash"] == 100000 + (820 - 800) - cost  # exits at target price, net of cost
    assert p["Closed Trades"][-1]["PnL"] == 20
    assert p["Closed Trades"][-1]["Net PnL"] == round(20 - cost, 2)
    assert p["Closed Trades"][-1]["Cost"] == round(cost, 2)


def test_stop_loss_hit_closes_with_loss():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, action = process_signal(p, "X", "NO TRADE", 785)  # below stop
    assert action == "CLOSED (Stop Loss)"
    cost = calculate_delivery_round_trip_cost(800, 790, 1)
    assert p["Cash"] == 100000 + (790 - 800) - cost  # exits at stop price, net of cost
    assert p["Closed Trades"][-1]["PnL"] == -10
    assert p["Closed Trades"][-1]["Net PnL"] == round(-10 - cost, 2)


def test_stcg_tax_applied_only_to_a_net_gain():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, _ = process_signal(p, "X", "NO TRADE", 825)  # above target - a win

    trade = p["Closed Trades"][-1]
    assert trade["STCG Tax"] == round(trade["Net PnL"] * 0.20, 2)
    assert trade["After-Tax PnL"] == round(trade["Net PnL"] - trade["STCG Tax"], 2)


def test_stcg_tax_is_zero_on_a_net_loss():
    p = _empty()
    p, _ = process_signal(p, "X", "BUY", 800, stop_loss=790, target=820)
    p, _ = process_signal(p, "X", "NO TRADE", 785)  # below stop - a loss

    trade = p["Closed Trades"][-1]
    assert trade["STCG Tax"] == 0.0
    assert trade["After-Tax PnL"] == trade["Net PnL"]


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


# ---------------- calculate_position_size ----------------

def test_position_size_at_floor_confidence_is_half_risk():
    # 60% confidence -> half of base_risk_pct (2%) of equity
    qty = calculate_position_size(60, price=100, equity=100000, base_risk_pct=2.0)
    assert qty == int((100000 * 0.02 * 0.5) // 100)  # 10


def test_position_size_at_full_confidence_is_full_risk():
    qty = calculate_position_size(100, price=100, equity=100000, base_risk_pct=2.0)
    assert qty == int((100000 * 0.02 * 1.0) // 100)  # 20


def test_position_size_scales_between_floor_and_ceiling():
    low = calculate_position_size(60, price=100, equity=100000)
    mid = calculate_position_size(80, price=100, equity=100000)
    high = calculate_position_size(100, price=100, equity=100000)
    assert low < mid < high


def test_position_size_never_zero_even_for_expensive_stock():
    # 2% of 100000 = 2000, far less than one SHREECEM-priced share
    qty = calculate_position_size(60, price=26515, equity=100000)
    assert qty == 1


def test_position_size_clamps_confidence_outside_expected_range():
    # Below the 60% floor or above 100 should clamp, not extrapolate/invert
    below = calculate_position_size(40, price=100, equity=100000)
    above = calculate_position_size(120, price=100, equity=100000)
    at_floor = calculate_position_size(60, price=100, equity=100000)
    at_ceiling = calculate_position_size(100, price=100, equity=100000)
    assert below == at_floor
    assert above == at_ceiling


# ---------------- MAX_CONCURRENT_POSITIONS ----------------

def _fake_frame():
    # analyze_symbol is monkeypatched below, so the frame content itself
    # is irrelevant - just needs len() >= MIN_CANDLES.
    return list(range(100))


def test_max_concurrent_positions_blocks_new_entries_at_cap(monkeypatch, tmp_path):

    symbols = {f"STOCK{i}": f"STOCK{i}.NS" for i in range(pt.MAX_CONCURRENT_POSITIONS + 3)}

    monkeypatch.setattr(pt, "download_watchlist", lambda syms, period, interval: {name: _fake_frame() for name in syms})
    monkeypatch.setattr(pt, "MIN_CANDLES", 1)
    monkeypatch.setattr(
        pt,
        "analyze_symbol",
        lambda frame: {"Price": 100, "Signal": "BUY", "Confidence": 80, "ATR": 2},
    )
    monkeypatch.setattr(pt, "PORTFOLIO_FILE", str(tmp_path / "portfolio.json"))

    portfolio, events = run_watchlist_paper_trading(symbols)

    assert len(portfolio["Positions"]) == pt.MAX_CONCURRENT_POSITIONS
    opened_events = [e for e in events if e["Action"] == "OPENED BUY"]
    assert len(opened_events) == pt.MAX_CONCURRENT_POSITIONS
