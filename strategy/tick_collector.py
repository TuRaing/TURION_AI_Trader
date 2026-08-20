import datetime

# Added 20-Aug-2026 - the ATM tick-by-tick archival collector, following
# up on 15-Aug's "TICK-BY-TICK DATA STORAGE" discussion in doc/
# PROJECT_STATUS.md (research only at the time, no code) - now that a
# real VPS exists to hold the persistent WebSocket connection this needs.
# Deliberately ATM-only (not OTM, not the full chain) - the user's own
# choice, since every live strategy in this project trades ATM options,
# so this is the only scope that's actually useful for analyzing this
# project's own execution/slippage behavior. Separate module from
# strategy/live_tick_harness.py - that one feeds decide_fn for real
# paper-trading decisions; this one just archives raw ticks to disk,
# no trading logic at all, per this repo's "each engine one
# responsibility" rule.
#
# Pure/testable logic only, matching this project's established split
# (see strategy/squareoff.py, report/market_checks.py) - the live
# WebSocket wiring is in run_tick_collector.py, NOT LIVE-TESTED (same
# caveat as strategy/live_tick_harness.py's own connect_and_run() -
# no way to verify real socket behavior without an actual connection).

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def atm_has_drifted(current_strike, spot, strike_step):
    """
    True if re-running the SAME ATM formula every other strategy in
    this project uses (round(spot/strike_step)*strike_step - see
    strategy/event_driven_runner.py's pick_atm_symbols()) against the
    latest spot would now pick a DIFFERENT strike than the one this
    collector is currently subscribed to. Used to decide when the
    collector should re-pick ATM CE/PE and re-subscribe, rather than
    picking ATM once at startup and never again (the known limitation
    already flagged in event_driven_runner.py's own module docstring
    for the trading engine - this collector fixes that gap for itself
    since tick archival specifically wants "whatever is ATM right now",
    not "whatever was ATM at 09:15").
    """

    new_strike = round(spot / strike_step) * strike_step

    return new_strike != current_strike


def tick_log_filename(now_ist):
    """
    One file per calendar day, e.g. "ticks_20260820.jsonl" - matches
    report/market_checks.py's market_check_log_filename() naming
    convention. JSONL (one JSON object per line) rather than a single
    JSON array, so a still-being-written file is always valid up to
    its last complete line (no need to hold the whole day's ticks in
    memory to append one more).
    """

    return f"ticks_{now_ist.strftime('%Y%m%d')}.jsonl"


def format_tick_record(index, leg, symbol, message):
    """
    Turns one raw Fyers SymbolUpdate message (see strategy/
    live_tick_harness.py's handle_symbol_update_message() for the same
    real field names - exch_feed_time, ltp, bid_price, ask_price,
    vol_traded_today) into one JSONL-ready record for archival.

    Parameters
    ----------
    index : "NIFTY" or "BANKNIFTY".
    leg : "SPOT", "CE", or "PE" - which of the 3 subscribed symbols per
        index this tick is for.
    symbol : the actual Fyers symbol string (e.g. "NSE:NIFTY2681824200CE").
    message : the raw tick dict from the WebSocket.

    Returns
    -------
    dict, ready for json.dumps() + a newline.
    """

    epoch = message.get("exch_feed_time", message.get("last_traded_time"))
    timestamp = datetime.datetime.fromtimestamp(epoch, tz=IST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    return {
        "timestamp": timestamp,
        "index": index,
        "leg": leg,
        "symbol": symbol,
        "ltp": message.get("ltp"),
        "bid": message.get("bid_price"),
        "ask": message.get("ask_price"),
        "volume": message.get("vol_traded_today"),
    }
