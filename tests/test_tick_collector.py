import datetime

from strategy.tick_collector import (
    atm_has_drifted,
    tick_log_filename,
    format_tick_record,
    tick_latency_ms,
    summarize_tick_latency,
    candle_minute_key,
    LiveCandleAggregator,
)

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


def test_format_tick_record_omits_received_at_when_not_given():
    message = {"exch_feed_time": 1787209200, "ltp": 24213.05}

    record = format_tick_record("NIFTY", "SPOT", "NSE:NIFTY50-INDEX", message)

    assert "received_at" not in record


def test_format_tick_record_includes_received_at_when_given():
    message = {"exch_feed_time": 1787209200, "ltp": 24213.05}
    received = datetime.datetime(2026, 8, 20, 12, 30, 0, 250000, tzinfo=IST)

    record = format_tick_record("NIFTY", "SPOT", "NSE:NIFTY50-INDEX", message, received_at=received)

    assert record["received_at"] == "2026-08-20 12:30:00.250"


def test_tick_latency_ms_computes_real_gap():
    record = {"timestamp": "2026-08-20 12:30:00.000", "received_at": "2026-08-20 12:30:00.180"}

    assert tick_latency_ms(record) == 180.0


def test_tick_latency_ms_none_when_received_at_missing():
    record = {"timestamp": "2026-08-20 12:30:00.000"}

    assert tick_latency_ms(record) is None


def test_tick_latency_ms_none_when_exch_feed_time_is_int32_min_sentinel():
    # Real bug caught live on the VPS (21-Aug-2026): Fyers sent
    # exch_feed_time=-2147483648 for a tick with no genuine exchange
    # timestamp yet, which format_tick_record() archived as this exact
    # "1901" string - without the guard this poisoned avg/max latency
    # with a many-decades-long value.
    record = {"timestamp": "1901-12-14 02:15:52.000", "received_at": "2026-08-21 06:45:22.616"}

    assert tick_latency_ms(record) is None


def test_tick_latency_ms_none_when_negative():
    record = {"timestamp": "2026-08-20 12:30:00.500", "received_at": "2026-08-20 12:30:00.100"}

    assert tick_latency_ms(record) is None


def test_summarize_tick_latency_computes_avg_and_max():
    records = [
        {"timestamp": "2026-08-20 12:30:00.000", "received_at": "2026-08-20 12:30:00.100"},
        {"timestamp": "2026-08-20 12:30:01.000", "received_at": "2026-08-20 12:30:01.300"},
        {"timestamp": "2026-08-20 12:30:02.000", "received_at": "2026-08-20 12:30:02.200"},
    ]

    summary = summarize_tick_latency(records)

    assert summary["count"] == 3
    assert summary["avg_ms"] == 200.0
    assert summary["max_ms"] == 300.0


def test_summarize_tick_latency_skips_unmeasurable_records():
    records = [
        {"timestamp": "2026-08-20 12:30:00.000", "received_at": "2026-08-20 12:30:00.100"},
        {"timestamp": "2026-08-20 12:30:01.000"},  # no received_at - e.g. an older archive
    ]

    summary = summarize_tick_latency(records)

    assert summary["count"] == 1
    assert summary["avg_ms"] == 100.0


def test_summarize_tick_latency_empty_list():
    summary = summarize_tick_latency([])

    assert summary == {"avg_ms": None, "max_ms": None, "count": 0}


def test_candle_minute_key_truncates_to_the_minute():
    assert candle_minute_key("2026-08-21 09:17:42.500") == "2026-08-21 09:17"


def test_live_candle_aggregator_first_tick_opens_a_candle_and_signals_close():
    agg = LiveCandleAggregator()

    started_new = agg.on_tick("2026-08-21 09:17:05.000", 24200.0)

    assert started_new is True
    assert agg.as_list() == [
        {"Timestamp": "2026-08-21 09:17:00", "Open": 24200.0, "High": 24200.0, "Low": 24200.0, "Close": 24200.0}
    ]


def test_live_candle_aggregator_ticks_within_the_same_minute_update_high_low_close():
    agg = LiveCandleAggregator()
    agg.on_tick("2026-08-21 09:17:05.000", 24200.0)

    started_new = agg.on_tick("2026-08-21 09:17:42.000", 24250.0)

    assert started_new is False
    candle = agg.as_list()[0]
    assert candle["High"] == 24250.0
    assert candle["Low"] == 24200.0
    assert candle["Close"] == 24250.0
    assert candle["Open"] == 24200.0


def test_live_candle_aggregator_new_minute_closes_the_previous_candle():
    agg = LiveCandleAggregator()
    agg.on_tick("2026-08-21 09:17:05.000", 24200.0)
    agg.on_tick("2026-08-21 09:17:42.000", 24250.0)

    started_new = agg.on_tick("2026-08-21 09:18:01.000", 24230.0)

    assert started_new is True
    candles = agg.as_list()
    assert len(candles) == 2
    assert candles[0]["Timestamp"] == "2026-08-21 09:17:00"
    assert candles[0]["Close"] == 24250.0  # previous candle unchanged
    assert candles[1]["Timestamp"] == "2026-08-21 09:18:00"
    assert candles[1]["Open"] == 24230.0


def test_live_candle_aggregator_caps_at_max_candles():
    agg = LiveCandleAggregator(max_candles=3)

    for minute in range(5):
        agg.on_tick(f"2026-08-21 09:{17 + minute:02d}:00.000", 24200.0 + minute)

    candles = agg.as_list()
    assert len(candles) == 3
    assert candles[0]["Timestamp"] == "2026-08-21 09:19:00"  # oldest 2 dropped
    assert candles[-1]["Timestamp"] == "2026-08-21 09:21:00"


def test_live_candle_aggregator_as_list_has_no_internal_minute_key():
    agg = LiveCandleAggregator()
    agg.on_tick("2026-08-21 09:17:05.000", 24200.0)

    assert "_minute_key" not in agg.as_list()[0]
