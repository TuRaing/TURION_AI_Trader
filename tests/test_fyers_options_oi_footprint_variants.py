from strategy.fyers_options_oi_footprint_variants import (
    make_oi_footprint_variant_config,
    _partial_close,
    _close_position,
    HYBRID_SL_CAP_PCT,
    TARGET_RUPEES,
    LADDER_HALF_AT_PCT,
)


def _fake_portfolio(lots=20, entry_premium=100):
    return {
        "Cash": 100000,
        "Position": {
            "Symbol": "NSE:NIFTY2681824300CE",
            "Strike": 24300,
            "Option Type": "CE",
            "Entry Time": "2026-08-14 10:00:00",
            "Entry Spot": 24300,
            "Entry Premium": entry_premium,
            "Entry CE OI": 1000000,
            "Entry PE OI": 900000,
            "Lots": lots,
            "Quantity": lots * 75,
            "Capital Deployed": entry_premium * lots * 75,
        },
        "Closed Trades": [],
    }


def test_make_oi_footprint_variant_config_nifty_hybrid_only():
    cfg = make_oi_footprint_variant_config("NIFTY", "oi_hybrid_sl", extra_exit=None)

    assert cfg["name"] == "oi_hybrid_sl"
    assert cfg["hybrid_sl_cap_pct"] == HYBRID_SL_CAP_PCT
    assert cfg["extra_exit"] is None
    assert cfg["lot_size"] == 75
    assert cfg["portfolio_file"] == "reports/fyers_options_oi_hybrid_sl_nifty_portfolio.json"


def test_make_oi_footprint_variant_config_extra_exit_tag():
    cfg = make_oi_footprint_variant_config("BANKNIFTY", "oi_hybrid_sl_trailing", extra_exit="trailing")

    assert cfg["extra_exit"] == "trailing"
    assert cfg["lot_size"] == 30


def test_partial_close_reduces_lots_by_the_amount_closed():
    cfg = make_oi_footprint_variant_config("NIFTY", "oi_hybrid_sl_laddered", extra_exit="laddered")
    portfolio = _fake_portfolio(lots=20, entry_premium=100)

    portfolio = _partial_close(cfg, portfolio, exit_premium=115, exit_spot=24350, lots_to_close=10)

    assert portfolio["Position"]["Lots"] == 10
    assert portfolio["Position"]["Partial Booked"] is True


def test_partial_close_records_a_closed_trade_with_only_the_closed_lots():
    cfg = make_oi_footprint_variant_config("NIFTY", "oi_hybrid_sl_laddered", extra_exit="laddered")
    portfolio = _fake_portfolio(lots=20, entry_premium=100)

    portfolio = _partial_close(cfg, portfolio, exit_premium=115, exit_spot=24350, lots_to_close=10)

    assert len(portfolio["Closed Trades"]) == 1
    trade = portfolio["Closed Trades"][0]
    assert trade["Lots"] == 10
    assert trade["Exit Reason"] == "Partial Target"
    assert trade["Net PnL"] > 0  # premium rose from 100 to 115


def test_partial_close_credits_cash_for_only_the_closed_portion():
    cfg = make_oi_footprint_variant_config("NIFTY", "oi_hybrid_sl_laddered", extra_exit="laddered")
    portfolio = _fake_portfolio(lots=20, entry_premium=100)
    cash_before = portfolio["Cash"]

    portfolio = _partial_close(cfg, portfolio, exit_premium=115, exit_spot=24350, lots_to_close=10)

    assert portfolio["Cash"] > cash_before
    # remaining position's capital deployed is unchanged (still tracked at original entry)
    assert portfolio["Position"]["Quantity"] == 10 * 75


def test_close_position_clears_the_open_position():
    cfg = make_oi_footprint_variant_config("NIFTY", "oi_hybrid_sl", extra_exit=None)
    portfolio = _fake_portfolio(lots=20, entry_premium=100)

    portfolio, action = _close_position(cfg, portfolio, exit_premium=105, reason="Target", exit_spot=24320)

    assert portfolio["Position"] is None
    assert len(portfolio["Closed Trades"]) == 1
    assert "CLOSED (Target)" in action


def test_ladder_half_at_pct_is_half_of_target():
    assert LADDER_HALF_AT_PCT * TARGET_RUPEES == 750
