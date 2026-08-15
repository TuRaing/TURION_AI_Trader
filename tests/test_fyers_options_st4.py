from strategy.fyers_options_st4 import make_st4_config, _trailing_stop_hit


def test_make_st4_config_nifty():
    cfg = make_st4_config("NIFTY")

    assert cfg["name"] == "st4"
    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_st4_nifty_portfolio.json"


def test_make_st4_config_banknifty():
    cfg = make_st4_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_st4_banknifty_portfolio.json"


def test_make_st4_config_defaults_no_daily_profit_lock():
    cfg = make_st4_config("NIFTY")

    assert cfg["daily_profit_lock"] is False


def test_make_st4_config_threshold_variant():
    cfg = make_st4_config("NIFTY", name="st4_threshold", daily_profit_lock=True, group="threshold")

    assert cfg["name"] == "st4_threshold"
    assert cfg["daily_profit_lock"] is True
    assert cfg["group"] == "threshold"
    assert cfg["portfolio_file"] == "reports/fyers_options_st4_threshold_nifty_portfolio.json"
    # Threshold variant keeps the SAME lot/strike sizing as the original -
    # only the profit-lock gate differs.
    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50


def test_trailing_stop_hit_ce_pulls_back_from_peak():
    # CE trails below the highest spot seen since entry.
    assert _trailing_stop_hit("CE", current_spot=100, peak_spot=110, trail_distance=5) is True
    assert _trailing_stop_hit("CE", current_spot=106, peak_spot=110, trail_distance=5) is False


def test_trailing_stop_hit_pe_bounces_from_trough():
    # PE trails above the lowest spot seen since entry.
    assert _trailing_stop_hit("PE", current_spot=100, peak_spot=90, trail_distance=5) is True
    assert _trailing_stop_hit("PE", current_spot=94, peak_spot=90, trail_distance=5) is False


def test_make_st4_config_defaults_no_hybrid_sl_cap():
    cfg = make_st4_config("NIFTY")

    assert cfg["hybrid_sl_cap_pct"] is None


def test_make_st4_config_hybrid_sl_cap_variant():
    cfg = make_st4_config("NIFTY", name="st4_threshold_slcap", daily_profit_lock=True, group="threshold",
                           hybrid_sl_cap_pct=2.0)

    assert cfg["name"] == "st4_threshold_slcap"
    assert cfg["hybrid_sl_cap_pct"] == 2.0
    assert cfg["group"] == "threshold"
