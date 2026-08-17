from strategy.fyers_depth_collector import _parse_depth_response, INDEX_STRIKE_STEP


def test_parse_depth_response_extracts_matching_symbol_fields():
    symbol = "NSE:NIFTY2681724550CE"
    data = {
        "s": "ok",
        "d": [
            {"n": symbol, "v": {
                "totalbuyqty": 12000, "totalsellqty": 9500,
                "bids": [{"price": 100.0, "volume": 75, "ord": 3}],
                "ask": [{"price": 100.2, "volume": 150, "ord": 5}],
                "ltp": 100.1,
            }},
        ],
    }

    fields = _parse_depth_response(data, symbol)

    assert fields is not None
    assert fields["totalbuyqty"] == 12000
    assert fields["totalsellqty"] == 9500
    assert fields["bids"][0]["price"] == 100.0
    assert fields["ask"][0]["volume"] == 150


def test_parse_depth_response_none_when_status_not_ok():
    data = {"s": "error", "message": "Could not authenticate the user"}

    assert _parse_depth_response(data, "NSE:NIFTY2681724550CE") is None


def test_parse_depth_response_none_when_d_missing():
    data = {"s": "ok"}

    assert _parse_depth_response(data, "NSE:NIFTY2681724550CE") is None


def test_parse_depth_response_none_when_symbol_not_in_d():
    data = {"s": "ok", "d": [{"n": "NSE:NIFTY2681724600CE", "v": {"ltp": 90}}]}

    assert _parse_depth_response(data, "NSE:NIFTY2681724550CE") is None


def test_parse_depth_response_none_when_entry_has_no_v_key():
    # Defends against an unexpected shape (e.g. "v" renamed/missing) -
    # skip cleanly rather than KeyError, per the module's verification
    # caveat (real response shape unconfirmed at write time).
    data = {"s": "ok", "d": [{"n": "NSE:NIFTY2681724550CE"}]}

    assert _parse_depth_response(data, "NSE:NIFTY2681724550CE") is None


def test_index_strike_step_matches_engine_config():
    # Same values as strategy/fyers_options_engine.py's INDEX_CONFIG -
    # not imported directly to avoid coupling this collector to the
    # live engine module, but must stay numerically consistent.
    assert INDEX_STRIKE_STEP["NSE:NIFTY50-INDEX"] == 50
    assert INDEX_STRIKE_STEP["NSE:NIFTYBANK-INDEX"] == 100
