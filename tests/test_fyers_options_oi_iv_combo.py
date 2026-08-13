from strategy.fyers_options_oi_iv_combo import make_oi_iv_combo_config, MAX_IV_RV_RATIO


def test_make_oi_iv_combo_config_nifty():
    cfg = make_oi_iv_combo_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["index_symbol_for_rsi"] == "^NSEI"
    assert cfg["portfolio_file"] == "reports/fyers_options_oi_iv_combo_nifty_portfolio.json"


def test_make_oi_iv_combo_config_banknifty():
    cfg = make_oi_iv_combo_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["index_symbol_for_rsi"] == "^NSEBANK"
    assert cfg["portfolio_file"] == "reports/fyers_options_oi_iv_combo_banknifty_portfolio.json"


def test_max_iv_rv_ratio_matches_the_backtested_threshold():
    # See PROJECT_STATUS.md's "IV vs REALIZED VOLATILITY
    # RETROSPECTIVELY TESTED" entry - 1.5 was the threshold found
    # near-free for oi_footprint/NIFTY's real closed trades.
    assert MAX_IV_RV_RATIO == 1.5
