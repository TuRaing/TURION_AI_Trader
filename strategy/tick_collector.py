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


def filter_completed_filenames(filenames, today_filename):
    """
    Every filename except today's (still being written by the live
    collector, must never be moved/deleted mid-write). Pure - takes
    plain filenames, not paths, so it works the same whether the
    caller got the listing from a local glob (run_tick_upload.py) or
    an `ls` over SSH on the VPS (sync_ticks_from_vps.py) - one shared
    rule instead of two copies that could drift apart.
    """

    return sorted(name for name in filenames if name != today_filename)


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


def format_tick_record(index, leg, symbol, message, received_at=None):
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
    received_at : datetime.datetime, IST, tz-aware - the moment THIS
        process actually received the tick (the caller's wall clock,
        not derived from the message) - None skips the "received_at"
        field entirely (kept optional/pure rather than defaulting to
        datetime.now() internally, matching this project's established
        "caller passes now_ist, functions here don't call the clock
        themselves" convention - see report/market_checks.py). Added
        20-Aug-2026 specifically so tick_latency_ms() below has
        something real to measure against "timestamp" (the EXCHANGE's
        own clock, from exch_feed_time) - the gap between the two is
        the real network+processing latency from Fyers to this VPS,
        the user's own explicit ask ("signal-to-decision latency").

    Returns
    -------
    dict, ready for json.dumps() + a newline.
    """

    epoch = message.get("exch_feed_time", message.get("last_traded_time"))
    timestamp = datetime.datetime.fromtimestamp(epoch, tz=IST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    record = {
        "timestamp": timestamp,
        "index": index,
        "leg": leg,
        "symbol": symbol,
        "ltp": message.get("ltp"),
        "bid": message.get("bid_price"),
        "ask": message.get("ask_price"),
        "volume": message.get("vol_traded_today"),
    }

    if received_at is not None:
        record["received_at"] = received_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    return record


def tick_latency_ms(record):
    """
    Milliseconds between the exchange's own tick timestamp ("timestamp",
    from Fyers' exch_feed_time) and when this process actually received
    it ("received_at") - real network+processing latency, the "signal-
    to-decision latency" the user asked to measure (20-Aug). Returns
    None if the record has no "received_at" (older archives, or a
    record built without one) rather than raising - a missing field is
    a normal "can't measure this one" case, not an error.
    """

    if "received_at" not in record:
        return None

    exchange_time = datetime.datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    received_time = datetime.datetime.strptime(record["received_at"], "%Y-%m-%d %H:%M:%S.%f")

    latency_ms = (received_time - exchange_time).total_seconds() * 1000

    # FIXED 21-Aug-2026 - real bug caught live on the VPS: Fyers
    # occasionally sends exch_feed_time as a sentinel/placeholder value
    # (-2147483648, a 32-bit signed int's minimum - confirmed against a
    # real archived record) for a tick with no genuine exchange
    # timestamp yet. format_tick_record() has no way to detect this at
    # write time, so it archives as "1901-12-14" - and without this
    # guard, that poisons every avg/max in summarize_tick_latency() with
    # a many-decades-long "latency" (confirmed live: avg ~84 days, max
    # ~125 years, in a real health-check report). Real exchange-to-VPS
    # latency is always sub-second to low-single-digit-seconds; treat
    # anything implausible (negative, or beyond a generous 5-minute
    # margin) as unmeasurable, same as a missing received_at.
    if latency_ms < 0 or latency_ms > 5 * 60 * 1000:
        return None

    return latency_ms


def summarize_tick_latency(records):
    """
    avg/max/count latency (ms) across a list of tick records (e.g. one
    day's worth, read back from a JSONL archive) - records with no
    measurable latency (no "received_at") are silently skipped, not
    counted as zero.

    Returns
    -------
    dict with avg_ms, max_ms, count (count = how many records had a
    measurable latency, not the total records passed in) - avg_ms/
    max_ms are None if count is 0 (nothing measurable, not "0ms").
    """

    latencies = [ms for ms in (tick_latency_ms(r) for r in records) if ms is not None]

    if not latencies:
        return {"avg_ms": None, "max_ms": None, "count": 0}

    return {
        "avg_ms": round(sum(latencies) / len(latencies), 1),
        "max_ms": round(max(latencies), 1),
        "count": len(latencies),
    }


def candle_minute_key(timestamp_str):
    """
    "YYYY-MM-DD HH:MM:SS.mmm" -> "YYYY-MM-DD HH:MM" - the 1-min bucket
    a tick with this timestamp belongs to. Added 21-Aug-2026 for
    LiveCandleAggregator below.
    """

    return timestamp_str[:16]


class LiveCandleAggregator:
    """
    Builds rolling 1-min OHLC candles from a live SPOT tick stream, for
    the mobile app's live chart (mobile_app/lib/screens/live_chart_
    screen.dart). Added 21-Aug-2026 - real gap found live: the app's own
    client-side aggregation (identical bucketing logic, kept in sync
    deliberately) has no history to seed from - Firebase only ever held
    the single latest tick, so opening the chart showed just one
    building candle instead of a real chart. This lets run_tick_
    collector.py maintain a real rolling history SERVER-SIDE and sync it
    periodically (see report/firebase_realtime_sync.py's sync_live_
    candles()) so the app can seed itself on open, then keep updating
    the current candle live from its own existing tick stream unchanged.

    Deliberately separate from strategy/live_tick_harness.py's
    CandleAggregator - that one is 5-min, RSI-focused, and feeds real
    trading decisions (must not change); this is 1-min, display-only,
    archival-process-only, no RSI, no trading logic at all - matches
    this repo's "each engine one responsibility" rule the same way
    strategy/tick_collector.py's own module docstring already argues
    for keeping this file separate from live_tick_harness.py.
    """

    def __init__(self, max_candles=120):
        self.max_candles = max_candles
        self._candles = []  # oldest first, each a dict with an internal _minute_key

    def on_tick(self, timestamp_str, ltp):
        """
        Returns True if this tick just CLOSED the previous candle
        (started a new bucket) - the caller's cue to sync as_list() to
        Firebase, rather than doing so on every single tick (which
        would reintroduce the exact blocking-Firebase-call latency
        bug fixed the same day - see run_tick_collector.py's own
        FIREBASE_SYNC_WORKERS comment).
        """

        minute_key = candle_minute_key(timestamp_str)

        if self._candles and self._candles[-1]["_minute_key"] == minute_key:
            candle = self._candles[-1]
            candle["High"] = max(candle["High"], ltp)
            candle["Low"] = min(candle["Low"], ltp)
            candle["Close"] = ltp
            return False

        self._candles.append({
            "_minute_key": minute_key,
            "Timestamp": f"{minute_key}:00",
            "Open": ltp, "High": ltp, "Low": ltp, "Close": ltp,
        })

        if len(self._candles) > self.max_candles:
            self._candles.pop(0)

        return True

    def as_list(self):
        """Candles ready to sync/serialize - the internal _minute_key
        bucket field stripped out (same shape the app's own client-side
        aggregator already produces, so no translation needed there)."""

        return [{k: v for k, v in c.items() if k != "_minute_key"} for c in self._candles]
