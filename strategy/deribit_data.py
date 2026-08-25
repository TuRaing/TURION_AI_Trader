import datetime

import requests

# Added 24-Aug-2026 - Deribit BTC/ETH options market-data integration
# for the crypto paper-trading sub-project (see the approved plan at
# the top of this branch's own history / doc/PROJECT_STATUS.md).
# Every endpoint below is Deribit's free, UNAUTHENTICATED, read-only
# public market data - no API key, no account, matching this sub-
# project's "paper trading only, no broker/exchange account" constraint.
#
# Every real field name and response shape here was CONFIRMED against
# Deribit's actual live API on 24-Aug-2026 (both REST and a real
# WebSocket subscription - see tests/test_deribit_data.py), not
# assumed - this project's own established discipline (see strategy/
# live_tick_harness.py's module docstring for the matching Fyers
# precedent).
#
# UNIT CONVENTION: Deribit quotes BTC/ETH option premiums in the
# underlying COIN, not USD (confirmed via get_instruments()'s real
# quote_currency field and ticker's real mark_price/best_bid_price/
# best_ask_price) - strategy/event_driven_engine.py's rsi_momentum_
# decide_fn assumes entry_premium and cfg["initial_capital"] share one
# unit (a paper USD amount), so every premium MUST be converted via
# to_usd_premium() before it reaches a data_point. Every ticker
# response (REST and the ticker.{instrument}.100ms WebSocket channel)
# carries index_price (USD) alongside the coin-denominated prices in
# the SAME response, so this conversion never needs a second request.

REST_BASE_URL = "https://www.deribit.com/api/v2"
WS_URL = "wss://www.deribit.com/ws/api/v2"


def get_index_price(currency):
    """
    currency: "BTC" or "ETH" (case-insensitive). Real response shape
    confirmed 24-Aug-2026: {"result": {"index_price": <float>, ...}}.
    """

    response = requests.get(
        f"{REST_BASE_URL}/public/get_index_price",
        params={"index_name": f"{currency.lower()}_usd"}, timeout=10,
    )
    response.raise_for_status()

    return response.json()["result"]["index_price"]


def get_instruments(currency):
    """
    Real, currently-listed option instruments for `currency` ("BTC"/
    "ETH"). Confirmed real fields (24-Aug-2026): instrument_name,
    strike, option_type ("call"/"put"), expiration_timestamp (ms epoch,
    UTC), settlement_period ("day"/"week"/"month" - confirmed via a
    real live query, used by pick_atm_instruments() below), quote_
    currency (the coin premiums are quoted in - e.g. "BTC", not "USD").
    """

    response = requests.get(
        f"{REST_BASE_URL}/public/get_instruments",
        params={"currency": currency.upper(), "kind": "option", "expired": "false"}, timeout=15,
    )
    response.raise_for_status()

    return response.json()["result"]


def get_ticker(instrument_name):
    """
    Real fields confirmed 24-Aug-2026: mark_price/best_bid_price/
    best_ask_price (quoted in the underlying coin) alongside index_
    price (USD) in the SAME response - see this module's own docstring
    on the coin-vs-USD unit convention.
    """

    response = requests.get(
        f"{REST_BASE_URL}/public/ticker",
        params={"instrument_name": instrument_name}, timeout=10,
    )
    response.raise_for_status()

    return response.json()["result"]


def to_usd_premium(coin_price, index_price):
    """
    Converts a Deribit coin-denominated option price (mark/bid/ask) to
    a paper USD premium, using the concurrent index_price from the SAME
    ticker response - see this module's own docstring. None in, None
    out (mirrors the None-quote handling every other premium field in
    this project already uses - a live tick with no price yet is not
    the same as a real zero, see event_driven_engine.py's own entry_
    premium checks).
    """

    if coin_price is None or index_price is None:
        return None

    return coin_price * index_price


def pick_atm_instruments(instruments, spot_price, prefer_settlement_period="week"):
    """
    Pure - given a real get_instruments() result and a spot price,
    picks one expiry and its ATM strike's call/put instrument names.

    Real Deribit strikes are NOT evenly spaced by one fixed step
    (confirmed via a real get_instruments() call, 24-Aug-2026) - unlike
    the NIFTY/BankNifty ATM pickers (strategy/event_driven_runner.py's
    pick_atm_symbols(), round(spot/strike_step)*strike_step), so ATM
    here is chosen from the strikes actually listed for the chosen
    expiry, not computed from a formula.

    Expiry choice: the nearest instrument whose settlement_period ==
    prefer_settlement_period ("week" by default, per this sub-project's
    plan - more runway than a "day" expiry, which can be as little as
    hours out). Falls back to the nearest expiry overall (any
    settlement_period) if none match that preference.

    Returns (expiration_timestamp_ms, strike, ce_instrument_name,
    pe_instrument_name). Raises ValueError if `instruments` is empty,
    or the chosen strike has no real call+put pair (shouldn't happen on
    a real Deribit response, but guards against a malformed/partial one
    rather than returning a silently-broken symbol).
    """

    if not instruments:
        raise ValueError("No instruments given - can't pick an ATM strike")

    preferred = [i for i in instruments if i.get("settlement_period") == prefer_settlement_period]
    pool = preferred if preferred else instruments

    nearest_expiry = min(i["expiration_timestamp"] for i in pool)
    same_expiry = [i for i in pool if i["expiration_timestamp"] == nearest_expiry]

    strikes = sorted({i["strike"] for i in same_expiry})
    atm_strike = min(strikes, key=lambda s: abs(s - spot_price))

    ce = next((i["instrument_name"] for i in same_expiry
               if i["strike"] == atm_strike and i["option_type"] == "call"), None)
    pe = next((i["instrument_name"] for i in same_expiry
               if i["strike"] == atm_strike and i["option_type"] == "put"), None)

    if ce is None or pe is None:
        raise ValueError(f"ATM strike {atm_strike} at expiry {nearest_expiry} is missing a call/put pair")

    return nearest_expiry, atm_strike, ce, pe


def parse_ticker_message(message):
    """
    Pure parser for one ticker.{instrument}.100ms subscription message
    (confirmed real shape 24-Aug-2026 via a live WebSocket connection).
    Mirrors strategy/live_tick_harness.py's handle_symbol_update_
    message()'s own "pure parsing, unit-testable without a live
    connection" split.

    Returns None for anything that isn't a ticker subscription message
    (a subscribe ack, an index-price message, or any other channel) -
    the caller is expected to try parse_index_message() next.
    """

    if message.get("method") != "subscription":
        return None

    params = message.get("params", {})
    channel = params.get("channel", "")

    if not channel.startswith("ticker."):
        return None

    data = params["data"]

    return {
        "instrument_name": data["instrument_name"],
        "timestamp": data["timestamp"],  # ms epoch, UTC
        "mark_price": data.get("mark_price"),
        "best_bid_price": data.get("best_bid_price"),
        "best_ask_price": data.get("best_ask_price"),
        "index_price": data.get("index_price"),
    }


def parse_index_message(message):
    """
    Pure parser for one deribit_price_index.{currency}_usd subscription
    message (confirmed real shape 24-Aug-2026). Returns None for
    anything that isn't an index-price subscription message.
    """

    if message.get("method") != "subscription":
        return None

    params = message.get("params", {})
    channel = params.get("channel", "")

    if not channel.startswith("deribit_price_index."):
        return None

    data = params["data"]

    return {
        "index_name": data["index_name"],
        "timestamp": data["timestamp"],  # ms epoch, UTC
        "price": data["price"],
    }


def connect_and_run(runner, ce_symbol, pe_symbol, index_name):
    """
    Verified against a REAL live WebSocket connection this session (one
    ticker + one index subscription, both channels confirmed to deliver
    the exact shape parse_ticker_message()/parse_index_message() expect
    - see tests/test_deribit_data.py) - unlike strategy/live_tick_
    harness.py's Fyers connect_and_run(), which remained NOT live-
    tested when it was written. Kept deliberately thin regardless - all
    real logic lives in the already-tested parse_*/to_usd_premium/
    runner code above and in strategy/crypto_tick_runner.py.

    Deribit's JSON-RPC subscribe protocol is unauthenticated for public
    channels - no access_token needed, unlike the Fyers equivalent.
    """

    import asyncio
    import json

    import websockets  # imported here, not at module level - lazy, same
    # convention this project's requirements.txt already uses for
    # fyers-apiv3 (live_tick_harness.py's own connect_and_run()) - so
    # every already-tested pure function above still works in an
    # environment without `websockets` installed.

    async def _run():
        async with websockets.connect(WS_URL) as ws:
            sub_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "public/subscribe",
                "params": {
                    "channels": [
                        f"ticker.{ce_symbol}.100ms",
                        f"ticker.{pe_symbol}.100ms",
                        f"deribit_price_index.{index_name.lower()}_usd",
                    ]
                },
            }
            await ws.send(json.dumps(sub_msg))

            async for raw in ws:
                message = json.loads(raw)

                ticker = parse_ticker_message(message)
                if ticker is not None:
                    timestamp = datetime.datetime.fromtimestamp(
                        ticker["timestamp"] / 1000, tz=datetime.timezone.utc
                    )
                    usd_mark = to_usd_premium(ticker["mark_price"], ticker["index_price"])
                    usd_bid = to_usd_premium(ticker["best_bid_price"], ticker["index_price"])
                    usd_ask = to_usd_premium(ticker["best_ask_price"], ticker["index_price"])
                    runner.on_tick(ticker["instrument_name"], timestamp, usd_mark, bid=usd_bid, ask=usd_ask)
                    continue

                index = parse_index_message(message)
                if index is not None:
                    timestamp = datetime.datetime.fromtimestamp(
                        index["timestamp"] / 1000, tz=datetime.timezone.utc
                    )
                    runner.on_tick(index_name, timestamp, index["price"])

    asyncio.run(_run())
