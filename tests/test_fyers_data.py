import datetime

from strategy.fyers_data import symbol_to_fyers, PERIOD_TO_DAYS, parse_option_expiry, time_to_expiry_years


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


def test_parse_option_expiry_weekly_format_real_symbol():
    # Real symbol observed live, 10/11-Aug-2026 trades.
    assert parse_option_expiry("NSE:NIFTY2681124600PE") == datetime.date(2026, 8, 11)


def test_parse_option_expiry_weekly_format_another_real_symbol():
    assert parse_option_expiry("NSE:NIFTY2681824300CE") == datetime.date(2026, 8, 18)


def test_parse_option_expiry_monthly_format_real_symbol():
    # Real symbol observed live - BANKNIFTY has been monthly-only since
    # weekly options were discontinued (SEBI/NSE, Nov-2024). Monthly
    # index-derivatives expiry moved Thursday -> Tuesday effective
    # 01-Sep-2025, so August 2026's expiry is its last TUESDAY.
    assert parse_option_expiry("NSE:BANKNIFTY26AUG57200CE") == datetime.date(2026, 8, 25)


def test_parse_option_expiry_weekly_format_handles_oct_nov_dec_month_codes():
    # NSE's single-character month code for weekly symbols uses O/N/D
    # for Oct/Nov/Dec instead of a 2-digit number (which would be
    # ambiguous with the day). NIFTY26O0524600PE -> 2026-10-05.
    assert parse_option_expiry("NSE:NIFTY26O0524600PE") == datetime.date(2026, 10, 5)


def test_parse_option_expiry_returns_none_for_unparseable_symbol():
    assert parse_option_expiry("NSE:RELIANCE-EQ") is None


def test_parse_option_expiry_returns_none_for_junk_input():
    assert parse_option_expiry("garbage") is None


def test_time_to_expiry_years_is_positive_before_expiry():
    from_dt = datetime.datetime(2026, 8, 10, 9, 30, 0)
    expiry = datetime.date(2026, 8, 11)

    years = time_to_expiry_years(from_dt, expiry)

    assert 0 < years < (5 / 365)  # a bit over a day away, well under a week


def test_time_to_expiry_years_is_zero_after_expiry():
    from_dt = datetime.datetime(2026, 8, 15, 9, 30, 0)
    expiry = datetime.date(2026, 8, 11)

    assert time_to_expiry_years(from_dt, expiry) == 0
