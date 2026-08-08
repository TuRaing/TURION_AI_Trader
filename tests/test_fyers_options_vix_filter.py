from strategy.fyers_options_vix_filter import make_vix_filter_config, _target_hit, _stop_loss_hit


def test_make_vix_filter_config_is_banknifty_only():
    cfg = make_vix_filter_config()

    assert cfg["index"] == "BANKNIFTY"
    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_vix_filter_banknifty_portfolio.json"


def test_make_vix_filter_config_custom_name():
    cfg = make_vix_filter_config(name="vix_filter_custom")

    assert cfg["name"] == "vix_filter_custom"
    assert cfg["portfolio_file"] == "reports/fyers_options_vix_filter_custom_banknifty_portfolio.json"


def test_target_hit_ce_needs_spot_to_rise():
    assert _target_hit("CE", current_spot=58500, target_spot=58500) is True
    assert _target_hit("CE", current_spot=58400, target_spot=58500) is False


def test_target_hit_pe_needs_spot_to_fall():
    assert _target_hit("PE", current_spot=58500, target_spot=58500) is True
    assert _target_hit("PE", current_spot=58600, target_spot=58500) is False


def test_stop_loss_hit_ce_on_spot_falling_below_sl():
    assert _stop_loss_hit("CE", current_spot=58200, stop_loss_spot=58250) is True
    assert _stop_loss_hit("CE", current_spot=58300, stop_loss_spot=58250) is False


def test_stop_loss_hit_pe_on_spot_rising_above_sl():
    assert _stop_loss_hit("PE", current_spot=58800, stop_loss_spot=58750) is True
    assert _stop_loss_hit("PE", current_spot=58700, stop_loss_spot=58750) is False
