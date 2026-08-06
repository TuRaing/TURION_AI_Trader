from strategy.fyers_options_engine import make_strategy, _net_pnl


def test_make_strategy_nifty_uses_nifty_lot_and_strike():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["underlying_symbol"] == "NSE:NIFTY50-INDEX"
    assert cfg["portfolio_file"] == "reports/fyers_options_simple_st1_nifty_portfolio.json"


def test_make_strategy_banknifty_uses_banknifty_lot_and_strike():
    cfg = make_strategy("simple_st1", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["underlying_symbol"] == "NSE:NIFTYBANK-INDEX"
    assert cfg["portfolio_file"] == "reports/fyers_options_simple_st1_banknifty_portfolio.json"


def test_net_pnl_positive_when_premium_rises():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    pnl = _net_pnl(cfg, entry_premium=100, current_premium=110, lots=5)

    assert pnl > 0


def test_net_pnl_negative_when_premium_falls():
    cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    pnl = _net_pnl(cfg, entry_premium=100, current_premium=90, lots=5)

    assert pnl < 0


def test_net_pnl_uses_banknifty_lot_size():
    nifty_cfg = make_strategy("simple_st1", "NIFTY", target_net_pct=3.0, stop_loss_pct=3.0)
    banknifty_cfg = make_strategy("simple_st1", "BANKNIFTY", target_net_pct=3.0, stop_loss_pct=3.0)

    nifty_pnl = _net_pnl(nifty_cfg, entry_premium=100, current_premium=110, lots=1)
    banknifty_pnl = _net_pnl(banknifty_cfg, entry_premium=100, current_premium=110, lots=1)

    # Same premium move, but NIFTY's lot size (75) is larger than
    # BANKNIFTY's (30), so 1 NIFTY lot's gross P&L is bigger.
    assert nifty_pnl > banknifty_pnl
