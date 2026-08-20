import datetime

from strategy.tick_collector import atm_has_drifted, tick_log_filename, format_tick_record

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def test_atm_has_drifted_false_when_spot_still_rounds_to_same_strike():
    # NIFTY strike_step 50 - strike 24200, spot moved to 24215 (still
    # rounds to 24200).
    assert atm_has_drifted(current_strike=24200, spot=24215, strike_step=50) is False


def test_atm_has_drifted_true_when_spot_crosses_into_the_next_strike():
    # 24230 rounds to 24250, not 24200 anymore.
    assert atm_has_drifted(current_strike=24200, spot=24230, strike_step=50) is True


def test_atm_has_drifted_true_for_banknifty_downward_move():
    # BANKNIFTY strike_step 100 - strike 57600, spot dropped to 57530
    # rounds to 57500.
    assert atm_has_drifted(current_strike=57600, spot=57530, strike_step=100) is True


def test_tick_log_filename_format():
    now = datetime.datetime(2026, 8, 20, 10, 30, tzinfo=IST)

    assert tick_log_filename(now) == "ticks_20260820.jsonl"


def test_format_tick_record_spot_leg():
    message = {"exch_feed_time": 1787209200, "ltp": 24213.05, "bid_price": None,
               "ask_price": None, "vol_traded_today": 0}

    record = format_tick_record("NIFTY", "SPOT", "NSE:NIFTY50-INDEX", message)

    assert record["index"] == "NIFTY"
    assert record["leg"] == "SPOT"
    assert record["symbol"] == "NSE:NIFTY50-INDEX"
    assert record["ltp"] == 24213.05
    assert record["bid"] is None
    assert record["ask"] is None
    assert record["timestamp"].startswith("2026-08-20 ")


def test_format_tick_record_ce_leg_with_bid_ask():
    message = {"exch_feed_time": 1787209200, "ltp": 37.3, "bid_price": 37.2,
               "ask_price": 37.4, "vol_traded_today": 152300}

    record = format_tick_record("NIFTY", "CE", "NSE:NIFTY2681824200CE", message)

    assert record["leg"] == "CE"
    assert record["ltp"] == 37.3
    assert record["bid"] == 37.2
    assert record["ask"] == 37.4
    assert record["volume"] == 152300


def test_format_tick_record_falls_back_to_last_traded_time_if_no_exch_feed_time():
    message = {"last_traded_time": 1787209200, "ltp": 100.0}

    record = format_tick_record("BANKNIFTY", "PE", "NSE:BANKNIFTY26AUG57600PE", message)

    assert record["timestamp"].startswith("2026-08-20 ")
