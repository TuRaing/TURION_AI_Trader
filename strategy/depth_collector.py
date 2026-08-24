import datetime

# Added 24-Aug-2026, at the user's own explicit request, right after
# verify_depth_websocket.py (22-Aug) confirmed the REAL, undocumented
# shape of Fyers' WebSocket "DepthUpdate" feed (a real live capture,
# not guessed - see that script's own module docstring for the full
# reasoning). Goal: today's real depth-slippage finding (LTP-based PnL
# overstates realized PnL by ~87-91% on a thin ATM book) was itself an
# ESTIMATE built on strategy/fyers_depth_collector.py's ~5-min-stale
# REST /depth snapshots - this collector replaces that staleness with
# continuous, real-time, tick-frequency depth, the same "each engine
# one responsibility" split strategy/tick_collector.py already
# established for LTP archival (this module is the depth equivalent -
# archives raw depth to disk, no trading logic, never touches
# strategy/event_driven_engine.py's already-live decision path).
#
# Pure/testable logic only, matching strategy/tick_collector.py's own
# split - the live WebSocket wiring is in run_depth_collector.py, NOT
# LIVE-TESTED beyond the one real capture verify_depth_websocket.py
# already did (same caveat as every other live-socket module here).
#
# REAL VERIFIED SHAPE (24-Aug-2026, via verify_depth_websocket.py's
# actual output - data/depth_websocket_verification.jsonl on the VPS):
#   {"bid_price1"..."bid_price5": float, "ask_price1"..."ask_price5": float,
#    "bid_size1"..."bid_size5": int, "ask_size1"..."ask_size5": int,
#    "bid_order1"..."bid_order5": int, "ask_order1"..."ask_order5": int,
#    "type": "dp", "symbol": str}
# NO exchange timestamp field at all (unlike SymbolUpdate's own exch_
# feed_time) - confirmed absent from every one of the 20 real captured
# messages - so unlike format_tick_record() (tick_collector.py), where
# received_at is optional/supplementary, here it's the ONLY timestamp
# available and therefore required.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def depth_log_filename(now_ist):
    """
    One file per calendar day, e.g. "depth_240826.jsonl" (DD-MM-YY,
    24-Aug-2026) - same convention as strategy/tick_collector.py's own
    tick_log_filename() (CHANGED there 22-Aug-2026, user's own explicit
    ask) - kept consistent from day one here rather than starting on
    the old YYYYMMDD convention and needing a later rename.
    """

    return f"depth_{now_ist.strftime('%d%m%y')}.jsonl"


def format_depth_record(symbol, message, received_at):
    """
    Turns one raw Fyers DepthUpdate message into one JSONL-ready
    record for archival. "Bids"/"Asks" are lists of {"price", "volume",
    "ord"} dicts, level 1 (best) first - deliberately the SAME shape
    strategy/fyers_depth_collector.py's own REST-based archive
    (reports/options_depth_history.jsonl) already uses, so any existing
    walk-the-book analysis code (e.g. the slippage estimate that found
    LTP-based PnL overstates realized PnL by ~87-91%) works unchanged
    against records from EITHER source - one depth-ladder shape, not
    two to keep in sync.

    received_at : datetime.datetime, IST, tz-aware - required (not
    optional, unlike format_tick_record()'s received_at) - the raw
    message itself carries no exchange-side timestamp for depth
    updates, so this process's own wall-clock reception is the only
    time this record can carry.
    """

    def level(prefix, i):
        return {
            "price": message.get(f"{prefix}_price{i}"),
            "volume": message.get(f"{prefix}_size{i}"),
            "ord": message.get(f"{prefix}_order{i}"),
        }

    return {
        "received_at": received_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "symbol": symbol,
        "Bids": [level("bid", i) for i in range(1, 6)],
        "Asks": [level("ask", i) for i in range(1, 6)],
    }
