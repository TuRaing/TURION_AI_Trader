from strategy.fyers_options_gapfill import make_gapfill_config, _target_hit, _stop_loss_hit


def test_make_gapfill_config_nifty():
    cfg = make_gapfill_config("NIFTY")

    assert cfg["name"] == "gapfill"
    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_gapfill_nifty_portfolio.json"


def test_make_gapfill_config_banknifty():
    cfg = make_gapfill_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_gapfill_banknifty_portfolio.json"


def test_make_gapfill_config_defaults_no_daily_profit_lock():
    cfg = make_gapfill_config("NIFTY")

    assert cfg["daily_profit_lock"] is False


def test_make_gapfill_config_threshold_variant():
    cfg = make_gapfill_config("NIFTY", name="gapfill_threshold", daily_profit_lock=True, group="threshold")

    assert cfg["name"] == "gapfill_threshold"
    assert cfg["daily_profit_lock"] is True
    assert cfg["group"] == "threshold"
    assert cfg["portfolio_file"] == "reports/fyers_options_gapfill_threshold_nifty_portfolio.json"


def test_target_hit_pe_reverts_down_to_prev_close():
    # Gap up -> PE -> target is spot falling back down to prev close.
    assert _target_hit("PE", current_spot=24500, target_spot=24500) is True
    assert _target_hit("PE", current_spot=24600, target_spot=24500) is False


def test_target_hit_ce_reverts_up_to_prev_close():
    # Gap down -> CE -> target is spot rising back up to prev close.
    assert _target_hit("CE", current_spot=24500, target_spot=24500) is True
    assert _target_hit("CE", current_spot=24400, target_spot=24500) is False


def test_stop_loss_hit_pe_gap_widens_further_up():
    assert _stop_loss_hit("PE", current_spot=24700, stop_loss_spot=24650) is True
    assert _stop_loss_hit("PE", current_spot=24600, stop_loss_spot=24650) is False


def test_stop_loss_hit_ce_gap_widens_further_down():
    assert _stop_loss_hit("CE", current_spot=24300, stop_loss_spot=24350) is True
    assert _stop_loss_hit("CE", current_spot=24400, stop_loss_spot=24350) is False
