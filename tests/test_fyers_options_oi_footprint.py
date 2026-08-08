from strategy.fyers_options_oi_footprint import make_oi_footprint_config, _classify_buildup


def test_make_oi_footprint_config_nifty():
    cfg = make_oi_footprint_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_oi_footprint_nifty_portfolio.json"


def test_make_oi_footprint_config_banknifty():
    cfg = make_oi_footprint_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_oi_footprint_banknifty_portfolio.json"


def test_classify_buildup_none_without_previous_snapshot():
    current = {"spot": 24600, "strike": 24600, "ce_oi": 100000, "pe_oi": 100000}

    assert _classify_buildup(None, current) is None


def test_classify_buildup_none_when_strike_changed():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24650, "strike": 24650, "ce_oi": 120000, "pe_oi": 100000}

    assert _classify_buildup(previous, current) is None


def test_classify_buildup_long_buildup_price_up_oi_up():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24550, "strike": 24500, "ce_oi": 115000, "pe_oi": 100000}

    assert _classify_buildup(previous, current) == "CE"


def test_classify_buildup_short_buildup_price_down_oi_up():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24450, "strike": 24500, "ce_oi": 100000, "pe_oi": 115000}

    assert _classify_buildup(previous, current) == "PE"


def test_classify_buildup_short_covering_price_up_oi_down():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24550, "strike": 24500, "ce_oi": 85000, "pe_oi": 90000}

    assert _classify_buildup(previous, current) == "CE"


def test_classify_buildup_long_unwinding_price_down_oi_down():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24450, "strike": 24500, "ce_oi": 85000, "pe_oi": 90000}

    assert _classify_buildup(previous, current) == "PE"


def test_classify_buildup_none_when_change_too_small():
    # Only ~2% combined OI change - below MIN_OI_CHANGE_PCT (5%), treated as noise.
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24550, "strike": 24500, "ce_oi": 102000, "pe_oi": 100000}

    assert _classify_buildup(previous, current) is None


def test_classify_buildup_none_when_price_flat():
    previous = {"spot": 24500, "strike": 24500, "ce_oi": 100000, "pe_oi": 100000}
    current = {"spot": 24500, "strike": 24500, "ce_oi": 120000, "pe_oi": 100000}

    assert _classify_buildup(previous, current) is None
