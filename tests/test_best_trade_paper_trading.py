import json

import strategy.best_trade_paper_trading as bpt
from strategy.best_trade_paper_trading import (
    load_best_trade_portfolio,
    open_best_trade,
    square_off_best_trade,
)


def _empty():
    return {"Cash": 100000, "Position": None, "Closed Trades": []}


# ---------------- open ----------------

def test_open_best_trade_opens_when_none_open():
    p = _empty()
    p, action = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)

    assert action == "OPENED"
    assert p["Position"]["Name"] == "TCS"
    assert p["Position"]["Direction"] == "BUY"


def test_open_best_trade_skips_if_already_open():
    p = _empty()
    p, _ = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)
    p, action = open_best_trade(p, "INFY", "INFY.NS", "SELL", 1500, 1530, 1440)

    assert action == "ALREADY OPEN"
    assert p["Position"]["Name"] == "TCS"  # unchanged


# ---------------- square-off: BUY ----------------

def test_square_off_buy_hits_target():
    p = _empty()
    p, _ = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)
    p, action = square_off_best_trade(p, 3950)  # above target

    assert action == "CLOSED (Target)"
    assert p["Position"] is None
    assert p["Closed Trades"][-1]["Exit Price"] == 3900
    assert p["Closed Trades"][-1]["PnL"] == 100
    assert p["Cash"] == 100100


def test_square_off_buy_hits_stop_loss():
    p = _empty()
    p, _ = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)
    p, action = square_off_best_trade(p, 3700)  # below stop

    assert action == "CLOSED (Stop Loss)"
    assert p["Closed Trades"][-1]["Exit Price"] == 3760
    assert p["Closed Trades"][-1]["PnL"] == -40


def test_square_off_buy_forces_close_at_market_price():
    p = _empty()
    p, _ = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)
    p, action = square_off_best_trade(p, 3830)  # between SL and target

    assert action == "CLOSED (Intraday Square-Off)"
    assert p["Closed Trades"][-1]["Exit Price"] == 3830
    assert p["Closed Trades"][-1]["PnL"] == 30


# ---------------- square-off: SELL (short) ----------------

def test_square_off_sell_hits_target():
    p = _empty()
    p, _ = open_best_trade(p, "INFY", "INFY.NS", "SELL", 1500, 1530, 1440)
    p, action = square_off_best_trade(p, 1400)  # below target (favorable for short)

    assert action == "CLOSED (Target)"
    assert p["Closed Trades"][-1]["Exit Price"] == 1440
    assert p["Closed Trades"][-1]["PnL"] == 60  # entry 1500 - exit 1440


def test_square_off_sell_hits_stop_loss():
    p = _empty()
    p, _ = open_best_trade(p, "INFY", "INFY.NS", "SELL", 1500, 1530, 1440)
    p, action = square_off_best_trade(p, 1550)  # above stop (unfavorable for short)

    assert action == "CLOSED (Stop Loss)"
    assert p["Closed Trades"][-1]["Exit Price"] == 1530
    assert p["Closed Trades"][-1]["PnL"] == -30  # entry 1500 - exit 1530


def test_square_off_sell_forces_close_at_market_price():
    p = _empty()
    p, _ = open_best_trade(p, "INFY", "INFY.NS", "SELL", 1500, 1530, 1440)
    p, action = square_off_best_trade(p, 1480)  # between target and stop

    assert action == "CLOSED (Intraday Square-Off)"
    assert p["Closed Trades"][-1]["Exit Price"] == 1480
    assert p["Closed Trades"][-1]["PnL"] == 20  # entry 1500 - exit 1480


def test_square_off_with_no_position_is_a_no_op():
    p = _empty()
    p, action = square_off_best_trade(p, 1000)

    assert action == "NO POSITION"
    assert p["Closed Trades"] == []


# ---------------- file I/O ----------------

def test_load_missing_file_returns_fresh_portfolio(tmp_path, monkeypatch):
    monkeypatch.setattr(bpt, "PORTFOLIO_FILE", str(tmp_path / "does_not_exist.json"))
    p = load_best_trade_portfolio()

    assert p["Cash"] == bpt.INITIAL_CAPITAL
    assert p["Position"] is None
    assert p["Closed Trades"] == []


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    f = tmp_path / "best_trade_portfolio.json"
    monkeypatch.setattr(bpt, "PORTFOLIO_FILE", str(f))

    p = _empty()
    p, _ = open_best_trade(p, "TCS", "TCS.NS", "BUY", 3800, 3760, 3900)
    bpt.save_best_trade_portfolio(p)

    loaded = json.loads(f.read_text())
    assert loaded["Position"]["Name"] == "TCS"
