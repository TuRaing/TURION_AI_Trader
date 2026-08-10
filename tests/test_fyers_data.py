from strategy.fyers_data import symbol_to_fyers, PERIOD_TO_DAYS


def test_symbol_to_fyers_translates_equity_ns_suffix():
    assert symbol_to_fyers("RELIANCE.NS") == "NSE:RELIANCE-EQ"


def test_symbol_to_fyers_translates_nifty_index():
    assert symbol_to_fyers("^NSEI") == "NSE:NIFTY50-INDEX"


def test_symbol_to_fyers_translates_banknifty_index():
    assert symbol_to_fyers("^NSEBANK") == "NSE:NIFTYBANK-INDEX"


def test_symbol_to_fyers_translates_india_vix():
    assert symbol_to_fyers("^INDIAVIX") == "NSE:INDIAVIX-INDEX"


def test_symbol_to_fyers_tatamotors_uses_the_fo_eligible_demerged_entity():
    # TATAMOTORS demerged into TMCV (Commercial Vehicles) and TMPV
    # (Passenger Vehicles) - only TMPV is F&O-eligible, per Fyers'
    # public symbol master (see strategy/fyers_data.py's override note).
    assert symbol_to_fyers("TATAMOTORS.NS") == "NSE:TMPV-EQ"


def test_symbol_to_fyers_ltim_maps_to_renamed_ltm_symbol():
    assert symbol_to_fyers("LTIM.NS") == "NSE:LTM-EQ"


def test_symbol_to_fyers_passes_through_unrecognized_symbol():
    assert symbol_to_fyers("SOME_UNKNOWN_SYMBOL") == "SOME_UNKNOWN_SYMBOL"


def test_period_to_days_covers_10d():
    # Regression test - fyers_options_vix_filter.py and fyers_options_
    # credit_spread.py both call fyers_download(..., period="10d", ...)
    # for their RSI/VIX lookback, but "10d" was missing from this map -
    # every single live check for both strategies raised ValueError
    # ("Unsupported period '10d'") and was silently swallowed by
    # fyers_multi_strategy_options_run.py's per-strategy try/except,
    # so neither strategy ever evaluated an entry signal since going
    # live (caught 10-Aug via GitHub Actions job logs - zero trades,
    # zero errors visible anywhere except inside the run logs).
    assert PERIOD_TO_DAYS.get("10d") == 10
