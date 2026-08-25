from strategy.deribit_data import (
    to_usd_premium, pick_atm_instruments, parse_ticker_message, parse_index_message,
)


# --- to_usd_premium ---

def test_to_usd_premium_multiplies_coin_price_by_index_price():
    assert to_usd_premium(0.1391, 78978.71) == 0.1391 * 78978.71


def test_to_usd_premium_none_coin_price_returns_none():
    assert to_usd_premium(None, 78978.71) is None


def test_to_usd_premium_none_index_price_returns_none():
    assert to_usd_premium(0.1391, None) is None


# --- pick_atm_instruments ---

def _instrument(name, strike, option_type, expiry, settlement_period="week"):
    return {
        "instrument_name": name, "strike": strike, "option_type": option_type,
        "expiration_timestamp": expiry, "settlement_period": settlement_period,
    }


def test_pick_atm_instruments_empty_raises():
    try:
        pick_atm_instruments([], 80000)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_pick_atm_instruments_picks_nearest_strike_at_nearest_expiry():
    instruments = [
        _instrument("BTC-1SEP26-79000-C", 79000, "call", 1000),
        _instrument("BTC-1SEP26-79000-P", 79000, "put", 1000),
        _instrument("BTC-1SEP26-80000-C", 80000, "call", 1000),
        _instrument("BTC-1SEP26-80000-P", 80000, "put", 1000),
        # A later expiry, closer strike - must NOT be picked, nearest
        # expiry wins first.
        _instrument("BTC-8SEP26-79010-C", 79010, "call", 2000),
        _instrument("BTC-8SEP26-79010-P", 79010, "put", 2000),
    ]

    expiry, strike, ce, pe = pick_atm_instruments(instruments, spot_price=79020)

    assert expiry == 1000
    assert strike == 79000  # closer to 79020 than 80000
    assert ce == "BTC-1SEP26-79000-C"
    assert pe == "BTC-1SEP26-79000-P"


def test_pick_atm_instruments_prefers_weekly_settlement_period_over_a_nearer_daily():
    instruments = [
        # Nearer in time, but a "day" expiry.
        _instrument("BTC-25AUG26-79000-C", 79000, "call", 500, settlement_period="day"),
        _instrument("BTC-25AUG26-79000-P", 79000, "put", 500, settlement_period="day"),
        # Further out, but the preferred "week" settlement period.
        _instrument("BTC-4SEP26-79000-C", 79000, "call", 1500, settlement_period="week"),
        _instrument("BTC-4SEP26-79000-P", 79000, "put", 1500, settlement_period="week"),
    ]

    expiry, strike, ce, pe = pick_atm_instruments(instruments, spot_price=79000)

    assert expiry == 1500
    assert ce == "BTC-4SEP26-79000-C"


def test_pick_atm_instruments_falls_back_to_nearest_overall_when_no_weekly_exists():
    instruments = [
        _instrument("BTC-25AUG26-79000-C", 79000, "call", 500, settlement_period="day"),
        _instrument("BTC-25AUG26-79000-P", 79000, "put", 500, settlement_period="day"),
    ]

    expiry, strike, ce, pe = pick_atm_instruments(instruments, spot_price=79000)

    assert expiry == 500
    assert ce == "BTC-25AUG26-79000-C"


def test_pick_atm_instruments_missing_pair_raises():
    instruments = [_instrument("BTC-1SEP26-79000-C", 79000, "call", 1000)]  # no matching put

    try:
        pick_atm_instruments(instruments, spot_price=79000)
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- parse_ticker_message / parse_index_message ---
# Real message shapes confirmed 24-Aug-2026 via a live WebSocket
# connection to wss://www.deribit.com/ws/api/v2 - not guessed.

def _real_ticker_message(**data_overrides):
    data = {
        "timestamp": 1787577921981,
        "state": "open",
        "index_price": 78978.71,
        "instrument_name": "BTC-25AUG26-68000-C",
        "mark_price": 0.1391,
        "best_ask_price": 0.142,
        "best_bid_price": 0.136,
        "underlying_price": 78988.18,
    }
    data.update(data_overrides)
    return {
        "jsonrpc": "2.0",
        "method": "subscription",
        "params": {"channel": "ticker.BTC-25AUG26-68000-C.100ms", "data": data},
    }


def _real_index_message(**data_overrides):
    data = {"timestamp": 1787577921981, "price": 78978.71, "index_name": "btc_usd"}
    data.update(data_overrides)
    return {
        "jsonrpc": "2.0",
        "method": "subscription",
        "params": {"channel": "deribit_price_index.btc_usd", "data": data},
    }


def test_parse_ticker_message_extracts_real_fields():
    parsed = parse_ticker_message(_real_ticker_message())

    assert parsed == {
        "instrument_name": "BTC-25AUG26-68000-C",
        "timestamp": 1787577921981,
        "mark_price": 0.1391,
        "best_bid_price": 0.136,
        "best_ask_price": 0.142,
        "index_price": 78978.71,
    }


def test_parse_ticker_message_ignores_a_sub_ack():
    sub_ack = {"jsonrpc": "2.0", "id": 1, "result": ["ticker.BTC-25AUG26-68000-C.100ms"]}

    assert parse_ticker_message(sub_ack) is None


def test_parse_ticker_message_ignores_an_index_message():
    assert parse_ticker_message(_real_index_message()) is None


def test_parse_index_message_extracts_real_fields():
    parsed = parse_index_message(_real_index_message())

    assert parsed == {"index_name": "btc_usd", "timestamp": 1787577921981, "price": 78978.71}


def test_parse_index_message_ignores_a_ticker_message():
    assert parse_index_message(_real_ticker_message()) is None
