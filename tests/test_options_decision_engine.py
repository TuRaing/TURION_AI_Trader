from strategy.options_decision_engine import get_options_decision


def _available_chain(bias, confidence):
    return {"Available": True, "Bias": bias, "Confidence": confidence}


def _unavailable_chain():
    return {"Available": False, "Reason": "NSE blocked this network (datacenter IP) or request failed"}


def test_bullish_confirmed_by_option_chain_gives_buy_ce():
    result = get_options_decision("Bullish", 80, _available_chain("Bullish", 70))

    assert result["Decision"] == "BUY CE"
    assert result["Confidence"] == 75.0


def test_bearish_confirmed_by_option_chain_gives_buy_pe():
    result = get_options_decision("Bearish", 90, _available_chain("Bearish", 50))

    assert result["Decision"] == "BUY PE"
    assert result["Confidence"] == 70.0


def test_conflicting_bias_gives_no_trade():
    result = get_options_decision("Bullish", 90, _available_chain("Bearish", 90))

    assert result["Decision"] == "NO TRADE"
    assert result["Confidence"] == 0.0


def test_neutral_option_bias_does_not_conflict():
    result = get_options_decision("Bullish", 80, _available_chain("Neutral", 40))

    assert result["Decision"] == "BUY CE"
    assert result["Confidence"] == 60.0


def test_option_chain_unavailable_falls_back_with_penalty():
    result = get_options_decision("Bullish", 90, _unavailable_chain())

    assert result["Decision"] == "BUY CE"
    assert result["Confidence"] == 63.0
    assert "unavailable" in result["Reason"]


def test_low_confidence_below_threshold_is_no_trade():
    result = get_options_decision("Bullish", 50, _available_chain("Bullish", 50))

    assert result["Decision"] == "NO TRADE"


def test_neutral_index_bias_is_no_trade():
    result = get_options_decision("Neutral", 80, _available_chain("Bullish", 80))

    assert result["Decision"] == "NO TRADE"
    assert result["Confidence"] == 0.0
