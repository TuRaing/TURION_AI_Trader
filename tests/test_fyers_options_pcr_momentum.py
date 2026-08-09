from strategy.fyers_options_pcr_momentum import make_pcr_momentum_config, _classify_pcr_momentum


def test_make_pcr_momentum_config_nifty():
    cfg = make_pcr_momentum_config("NIFTY")

    assert cfg["lot_size"] == 75
    assert cfg["strike_step"] == 50
    assert cfg["portfolio_file"] == "reports/fyers_options_pcr_momentum_nifty_portfolio.json"


def test_make_pcr_momentum_config_banknifty():
    cfg = make_pcr_momentum_config("BANKNIFTY")

    assert cfg["lot_size"] == 30
    assert cfg["strike_step"] == 100
    assert cfg["portfolio_file"] == "reports/fyers_options_pcr_momentum_banknifty_portfolio.json"


def test_classify_pcr_momentum_none_without_previous_snapshot():
    current = {"spot": 24600, "pcr": 1.10, "total_volume": 500000}

    assert _classify_pcr_momentum(None, current) is None


def test_classify_pcr_momentum_bullish_when_pcr_rises_with_volume_confirmation():
    # PCR rises ~9% (more put-writing than call-writing) with volume
    # up 50% - both conditions met -> bullish (CE).
    previous = {"spot": 24500, "pcr": 1.00, "total_volume": 400000}
    current = {"spot": 24550, "pcr": 1.09, "total_volume": 600000}

    assert _classify_pcr_momentum(previous, current) == "CE"


def test_classify_pcr_momentum_bearish_when_pcr_falls_with_volume_confirmation():
    # PCR falls ~9% (more call-writing than put-writing) with volume
    # up 50% - bearish (PE).
    previous = {"spot": 24500, "pcr": 1.00, "total_volume": 400000}
    current = {"spot": 24450, "pcr": 0.91, "total_volume": 600000}

    assert _classify_pcr_momentum(previous, current) == "PE"


def test_classify_pcr_momentum_none_when_change_too_small():
    # Only ~2% PCR change - below MIN_PCR_CHANGE_PCT (5%), treated as noise.
    previous = {"spot": 24500, "pcr": 1.00, "total_volume": 400000}
    current = {"spot": 24520, "pcr": 1.02, "total_volume": 600000}

    assert _classify_pcr_momentum(previous, current) is None


def test_classify_pcr_momentum_none_when_volume_not_confirming():
    # PCR change is large enough (10%) but volume barely moved (only
    # 1.05x, below MIN_VOLUME_RATIO 1.2) - not trusted as a real signal.
    previous = {"spot": 24500, "pcr": 1.00, "total_volume": 400000}
    current = {"spot": 24550, "pcr": 1.10, "total_volume": 420000}

    assert _classify_pcr_momentum(previous, current) is None


def test_classify_pcr_momentum_none_when_previous_pcr_is_zero():
    previous = {"spot": 24500, "pcr": 0.0, "total_volume": 400000}
    current = {"spot": 24550, "pcr": 1.10, "total_volume": 600000}

    assert _classify_pcr_momentum(previous, current) is None


def test_classify_pcr_momentum_none_when_previous_volume_is_zero():
    previous = {"spot": 24500, "pcr": 1.00, "total_volume": 0}
    current = {"spot": 24550, "pcr": 1.10, "total_volume": 600000}

    assert _classify_pcr_momentum(previous, current) is None
