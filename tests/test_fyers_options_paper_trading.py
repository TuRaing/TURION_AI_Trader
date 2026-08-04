from strategy.fyers_options_paper_trading import _net_pnl


def test_net_pnl_positive_when_premium_rises():
    pnl = _net_pnl(entry_premium=100, current_premium=110, lots=5)

    assert pnl > 0


def test_net_pnl_negative_when_premium_falls():
    pnl = _net_pnl(entry_premium=100, current_premium=90, lots=5)

    assert pnl < 0


def test_net_pnl_accounts_for_costs_even_at_flat_premium():
    pnl = _net_pnl(entry_premium=100, current_premium=100, lots=5)

    assert pnl < 0  # gross is 0, so net must be negative (real costs)
