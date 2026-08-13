from strategy.fyers_options_pcr_vix_combo import make_pcr_vix_combo_config


def test_make_pcr_vix_combo_config_nifty():
    cfg = make_pcr_vix_combo_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_pcr_vix_combo_nifty_portfolio.json"


def test_make_pcr_vix_combo_config_banknifty():
    cfg = make_pcr_vix_combo_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_pcr_vix_combo_banknifty_portfolio.json"


def test_make_pcr_vix_combo_config_custom_name():
    cfg = make_pcr_vix_combo_config("NIFTY", name="pcr_vix_combo_custom")

    assert cfg["name"] == "pcr_vix_combo_custom"
    assert cfg["portfolio_file"] == "reports/fyers_options_pcr_vix_combo_custom_nifty_portfolio.json"
