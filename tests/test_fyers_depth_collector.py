from strategy import fyers_depth_collector
from strategy.fyers_depth_collector import _atm_ce_pe_symbols, _parse_depth_response, INDEX_STRIKE_STEP, snapshot


def test_atm_ce_pe_symbols_none_when_option_chain_response_is_not_a_dict(monkeypatch):
    # Added 19-Aug-2026 - the actual bug hit on the first live run:
    # _parse_depth_response()'s isinstance guard (fixed first) did NOT
    # stop the crash, because this earlier call site had the identical
    # unguarded data.get(...) bug.
    monkeypatch.setattr(fyers_depth_collector, "fetch_option_chain", lambda *a, **k: "some error text")

    result = _atm_ce_pe_symbols("NSE:NIFTY50-INDEX")

    assert result == (None, None, None, None)


def test_atm_ce_pe_symbols_none_when_inner_data_key_is_not_a_dict(monkeypatch):
    # Added 19-Aug-2026 - found after BOTH earlier fixes shipped and the
    # live crash still persisted unchanged: data.get("data", {}) only
    # falls back to {} when the "data" key is MISSING, not when it's
    # present but holds a non-dict value (e.g. a string) - chaining
    # .get("optionsChain", []) straight onto that crashed identically.
    data = {"s": "ok", "data": "some unexpected string value"}
    monkeypatch.setattr(fyers_depth_collector, "fetch_option_chain", lambda *a, **k: data)

    result = _atm_ce_pe_symbols("NSE:NIFTY50-INDEX")

    assert result == (None, None, None, None)


def test_atm_ce_pe_symbols_skips_non_dict_legs_in_the_options_chain(monkeypatch):
    # Added 19-Aug-2026 - even AFTER both isinstance fixes above shipped,
    # the live crash persisted unchanged - this is the next leading
    # theory: a stray non-dict entry inside optionsChain itself (not
    # `data` as a whole) would make leg.get(...) raise the identical
    # error, and neither earlier fix touches individual leg entries.
    data = {
        "s": "ok",
        "data": {"optionsChain": [
            "unexpected string entry",
            {"strike_price": -1, "ltp": 24500.0},
            {"strike_price": 24500, "option_type": "CE", "symbol": "NSE:NIFTY2681724500CE"},
            {"strike_price": 24500, "option_type": "PE", "symbol": "NSE:NIFTY2681724500PE"},
        ]},
    }
    monkeypatch.setattr(fyers_depth_collector, "fetch_option_chain", lambda *a, **k: data)

    spot, atm_strike, ce_symbol, pe_symbol = _atm_ce_pe_symbols("NSE:NIFTY50-INDEX")

    assert spot == 24500.0
    assert ce_symbol == "NSE:NIFTY2681724500CE"
    assert pe_symbol == "NSE:NIFTY2681724500PE"


def test_snapshot_continues_to_the_next_index_when_one_symbol_raises(monkeypatch, tmp_path):
    # Added 19-Aug-2026 - the broad per-symbol try/except: whatever the
    # real, still-not-fully-identified crash cause turns out to be, one
    # bad index must not lose the OTHER index's real data for the same
    # run - this is the safety net independent of any specific fix.
    archive_path = tmp_path / "options_depth_history.jsonl"
    monkeypatch.setattr(fyers_depth_collector, "ARCHIVE_PATH", str(archive_path))

    def fake_atm(underlying_symbol, strike_count=5):
        if underlying_symbol == "NSE:NIFTY50-INDEX":
            raise AttributeError("'str' object has no attribute 'get'")
        return 51000.0, 51000, "NSE:NIFTYBANK2681751000CE", "NSE:NIFTYBANK2681751000PE"

    monkeypatch.setattr(fyers_depth_collector, "_atm_ce_pe_symbols", fake_atm)
    monkeypatch.setattr(fyers_depth_collector, "fetch_depth", lambda symbol: {
        "s": "ok", "d": [{"n": symbol, "v": {"totalbuyqty": 1, "totalsellqty": 1, "bids": [], "ask": [], "ltp": 1.0}}],
    })

    written = snapshot(("NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX"))

    assert written == 2  # both BANKNIFTY legs written despite NIFTY raising
    assert archive_path.exists()


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


def test_parse_depth_response_none_when_response_is_not_a_dict():
    # Added 19-Aug-2026 - the real bug hit on the first live run: Fyers'
    # actual /depth response was a plain string, not a dict, and the
    # old code called data.get(...) before checking that, crashing with
    # 'str' object has no attribute 'get' instead of skipping cleanly.
    assert _parse_depth_response("some error text", "NSE:NIFTY2681724550CE") is None


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
