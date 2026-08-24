import datetime

from strategy.depth_collector import depth_log_filename, format_depth_record

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def test_depth_log_filename_format():
    now = datetime.datetime(2026, 8, 24, 10, 30, tzinfo=IST)

    assert depth_log_filename(now) == "depth_240826.jsonl"


def _real_captured_message(symbol="NSE:NIFTY26AUG24300PE"):
    # A real message captured live 24-Aug-2026 via verify_depth_websocket.py
    # (data/depth_websocket_verification.jsonl on the VPS) - not invented.
    return {
        "bid_price1": 50.9, "bid_price2": 50.85, "bid_price3": 50.8, "bid_price4": 50.75, "bid_price5": 50.7,
        "ask_price1": 51.05, "ask_price2": 51.1, "ask_price3": 51.15, "ask_price4": 51.2, "ask_price5": 51.25,
        "bid_size1": 12935, "bid_size2": 3055, "bid_size3": 4875, "bid_size4": 2795, "bid_size5": 6045,
        "ask_size1": 1625, "ask_size2": 7345, "ask_size3": 7215, "ask_size4": 6175, "ask_size5": 6240,
        "bid_order1": 18, "bid_order2": 11, "bid_order3": 12, "bid_order4": 7, "bid_order5": 13,
        "ask_order1": 11, "ask_order2": 20, "ask_order3": 15, "ask_order4": 13, "ask_order5": 15,
        "type": "dp", "symbol": symbol,
    }


def test_format_depth_record_matches_real_captured_shape():
    now = datetime.datetime(2026, 8, 24, 10, 30, 0, tzinfo=IST)
    record = format_depth_record("NSE:NIFTY26AUG24300PE", _real_captured_message(), now)

    assert record["received_at"] == "2026-08-24 10:30:00.000"
    assert record["symbol"] == "NSE:NIFTY26AUG24300PE"
    assert record["Bids"][0] == {"price": 50.9, "volume": 12935, "ord": 18}
    assert record["Asks"][0] == {"price": 51.05, "volume": 1625, "ord": 11}
    assert len(record["Bids"]) == 5
    assert len(record["Asks"]) == 5


def test_format_depth_record_bids_and_asks_are_best_price_first():
    record = format_depth_record("X", _real_captured_message(), datetime.datetime.now(IST))

    bid_prices = [level["price"] for level in record["Bids"]]
    ask_prices = [level["price"] for level in record["Asks"]]

    assert bid_prices == sorted(bid_prices, reverse=True)  # best bid (highest) first
    assert ask_prices == sorted(ask_prices)  # best ask (lowest) first


def test_format_depth_record_shape_matches_rest_based_archive():
    # strategy/fyers_depth_collector.py's own REST-based record uses
    # "Bids"/"Asks" as lists of {"price", "volume", "ord"} dicts - this
    # WebSocket-based record must match exactly, so existing walk-the-
    # book analysis code works unchanged against either source.
    record = format_depth_record("X", _real_captured_message(), datetime.datetime.now(IST))

    for side in ("Bids", "Asks"):
        for level in record[side]:
            assert set(level.keys()) == {"price", "volume", "ord"}
