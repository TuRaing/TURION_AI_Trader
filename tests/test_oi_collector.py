import datetime

from strategy.oi_collector import oi_log_filename, format_oi_record

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def test_oi_log_filename_format():
    now = datetime.datetime(2026, 8, 28, 10, 30, tzinfo=IST)

    assert oi_log_filename(now) == "oi_280826.jsonl"


def test_format_oi_record_matches_real_snapshot_shape():
    # Real shape from strategy/fyers_options_oi_footprint.py's own
    # _read_atm_oi_snapshot() return value.
    snapshot = {"spot": 24265.5, "strike": 24250, "ce_oi": 1234500, "pe_oi": 987600}
    ts = datetime.datetime(2026, 8, 28, 9, 34, 17, tzinfo=IST)

    record = format_oi_record("NIFTY", snapshot, ts)

    assert record == {
        "timestamp": "2026-08-28 09:34:17",
        "index": "NIFTY",
        "spot": 24265.5,
        "strike": 24250,
        "ce_oi": 1234500,
        "pe_oi": 987600,
    }


def test_format_oi_record_banknifty():
    snapshot = {"spot": 57959.65, "strike": 58000, "ce_oi": 555000, "pe_oi": 612300}
    ts = datetime.datetime(2026, 8, 28, 9, 34, 17, tzinfo=IST)

    record = format_oi_record("BANKNIFTY", snapshot, ts)

    assert record["index"] == "BANKNIFTY"
    assert record["strike"] == 58000
