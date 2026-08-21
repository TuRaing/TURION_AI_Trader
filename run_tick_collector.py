import concurrent.futures
import datetime
import json
import os
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
# FIXED 21-Aug-2026 - same buffering fix as run_event_driven_engine.py's
# matching line (see that file's comment for the full real-incident
# detail) - applied here too for consistency, this process runs under
# the identical systemd/non-TTY conditions.

from report.firebase_realtime_sync import fetch_access_token, sync_live_tick
from strategy.event_driven_runner import pick_atm_symbols
from strategy.fyers_options_engine import INDEX_CONFIG
from strategy.tick_collector import atm_has_drifted, tick_log_filename, format_tick_record

# Added 20-Aug-2026 - the VPS entry point for the ATM tick-by-tick
# archival collector (strategy/tick_collector.py's pure logic). Same
# "top-level script resolves real credentials, module takes them as a
# plain parameter" split this project already uses for run_event_
# driven_engine.py. Archives raw ATM CE/PE/spot ticks for NIFTY and
# BANKNIFTY to local JSONL files - no trading logic, no decide_fn,
# completely separate from strategy/live_tick_harness.py per this
# repo's "each engine one responsibility" rule.
#
# NOT LIVE-TESTED - same caveat as run_event_driven_engine.py and
# strategy/live_tick_harness.py's connect_and_run(): fyers_apiv3's real
# socket behavior (auth, subscribe, unsubscribe, reconnect) can only be
# confirmed against a real live connection, not from here. In
# particular, FyersDataSocket.unsubscribe() below is assumed to exist
# and behave symmetrically to .subscribe() based on the SDK's public
# surface - not yet exercised live.
#
# LOCAL DISK ONLY - does not upload anywhere. Pair with a separate
# nightly job (run_tick_upload.py) to ship completed days to cheap
# cloud object storage and free local disk - see doc/PROJECT_STATUS.
# md's 15-Aug "TICK-BY-TICK DATA STORAGE" entry for the reasoning
# (VPS disk fills in days at full tick volume; narrow ATM-only scope
# here specifically avoids that).

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TICK_DIR = os.path.join("data", "ticks")
ATM_RECHECK_SECONDS = 15 * 60  # re-pick ATM every 15 min - frequent
# enough to track real intraday drift, infrequent enough not to hammer
# the option-chain REST endpoint (pick_atm_symbols() is one real
# network call, not free).
FIREBASE_SYNC_WORKERS = 4  # FIXED 21-Aug-2026 - real bug caught live:
# sync_live_tick() was called synchronously inside on_message(), a
# cross-region REST call (VPS in Mumbai, Realtime Database in
# asia-southeast1/Singapore) blocking the WebSocket's own receive
# thread on EVERY tick - confirmed live via the archived tick data
# itself: median exchange-to-received latency 1.5s, 82% of ticks over
# 1s, max 46.5s, across 92,124 real ticks. A bounded thread pool
# (not one raw thread per tick, which could pile up unboundedly faster
# than Firebase can drain them under a tick burst) moves the network
# call off the hot path - the local JSONL archive (this process's own
# durable record) stays synchronous and immediate.

INDICES = ("NIFTY", "BANKNIFTY")


class TickWriter:
    """
    Owns the single open file handle for today's tick log, appending
    one JSON line per tick. Rotates to a new file automatically if the
    calendar date changes while running (the process is expected to
    restart daily via cron/systemd anyway, but this makes a long-lived
    run correct too, not just convenient).
    """

    def __init__(self):
        self._date = None
        self._fh = None

    def _ensure_open_for_today(self):

        now = datetime.datetime.now(IST)
        today = now.date()

        if today == self._date:
            return

        if self._fh:
            self._fh.close()

        os.makedirs(TICK_DIR, exist_ok=True)
        path = os.path.join(TICK_DIR, tick_log_filename(now))
        self._fh = open(path, "a", encoding="utf-8")
        self._date = today
        print(f"Tick log: {path}")

    def write(self, record):
        self._ensure_open_for_today()
        self._fh.write(json.dumps(record) + "\n")
        self._fh.flush()


def main():

    access_token = fetch_access_token()

    if not access_token:
        print("No access_token available via Firebase yet (today's login hasn't run, or "
              "Firebase isn't configured) - skipping this start attempt.")
        sys.exit(0)

    # See run_event_driven_engine.py's matching comment (21-Aug-2026) -
    # pick_atm_symbols() below ultimately calls strategy/fyers_auth.py's
    # get_access_token() (local .env only) several layers down; setting
    # the env var directly here makes every one of those calls pick up
    # the real Firebase-sourced token without touching any shared module.
    os.environ["FYERS_ACCESS_TOKEN"] = access_token

    from fyers_apiv3.FyersWebsocket import data_ws  # see module docstring -
    # imported here, not at module level, matching live_tick_harness.py's
    # own reasoning (this module stays importable without fyers_apiv3
    # installed).

    writer = TickWriter()

    # See FIREBASE_SYNC_WORKERS' own 21-Aug-2026 comment above.
    firebase_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=FIREBASE_SYNC_WORKERS, thread_name_prefix="firebase-sync"
    )

    def sync_live_tick_async(index, leg, record):
        try:
            sync_live_tick(index, leg, record)
        except Exception as error:
            print(f"Live tick Firebase sync failed for {record['symbol']} (continuing): {error}")

    # state[index] = {"strike": int, "symbols": {fyers_symbol: leg}}
    state = {}

    print("Fetching initial ATM strikes...")
    for index in INDICES:
        spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)
        underlying_symbol = INDEX_CONFIG[index]["underlying_symbol"]
        state[index] = {
            "strike": atm_strike,
            "symbols": {underlying_symbol: "SPOT", ce_symbol: "CE", pe_symbol: "PE"},
        }
        print(f"{index}: spot={spot} atm_strike={atm_strike} ce={ce_symbol} pe={pe_symbol}")

    def all_subscribed_symbols():
        symbols = []
        for index in INDICES:
            symbols.extend(state[index]["symbols"].keys())
        return symbols

    def symbol_lookup(symbol):
        for index in INDICES:
            leg = state[index]["symbols"].get(symbol)
            if leg:
                return index, leg
        return None, None

    def on_message(message):
        symbol = message.get("symbol")
        index, leg = symbol_lookup(symbol)

        if index is None:
            return  # a tick for a symbol we just unsubscribed from mid-flight

        # received_at is THIS process's own wall clock at the moment the
        # tick arrived - the "received" side of tick_latency_ms()'s
        # exchange-vs-received comparison (user's own 20-Aug ask: real
        # signal-to-decision latency, not an estimate).
        record = format_tick_record(index, leg, symbol, message, received_at=datetime.datetime.now(IST))
        writer.write(record)

        # Added 20-Aug-2026 - the mobile app's live tick-by-tick chart
        # (VPS tab). Best-effort - a Firebase hiccup must never stop the
        # local archive, which is the durable record. FIXED 21-Aug-2026 -
        # moved off this hot path entirely (see FIREBASE_SYNC_WORKERS'
        # own comment) - was blocking every tick on a real cross-region
        # network call.
        firebase_executor.submit(sync_live_tick_async, index, leg, record)

    def on_error(message):
        print(f"[tick collector websocket error] {message}")

    def on_close(message):
        print(f"[tick collector websocket closed] {message}")

    def on_open():
        socket.subscribe(symbols=all_subscribed_symbols(), data_type="SymbolUpdate")
        socket.keep_running()

    socket = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=on_open,
        on_close=on_close,
        on_error=on_error,
        on_message=on_message,
    )

    def atm_recheck_loop():
        while True:
            time.sleep(ATM_RECHECK_SECONDS)
            for index in INDICES:
                try:
                    spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)
                except Exception as error:
                    print(f"ATM re-check failed for {index} (continuing on the old strike): {error}")
                    continue

                if not atm_has_drifted(state[index]["strike"], spot, INDEX_CONFIG[index]["strike_step"]):
                    continue

                old_symbols = list(state[index]["symbols"].keys())
                underlying_symbol = INDEX_CONFIG[index]["underlying_symbol"]
                new_symbols = {underlying_symbol: "SPOT", ce_symbol: "CE", pe_symbol: "PE"}

                print(f"{index}: ATM drifted {state[index]['strike']} -> {atm_strike}, re-subscribing.")

                try:
                    socket.unsubscribe(symbols=old_symbols, data_type="SymbolUpdate")
                except Exception as error:
                    print(f"Unsubscribe failed for {index} (continuing anyway): {error}")

                socket.subscribe(symbols=list(new_symbols.keys()), data_type="SymbolUpdate")
                state[index] = {"strike": atm_strike, "symbols": new_symbols}

    threading.Thread(target=atm_recheck_loop, daemon=True).start()

    print("Connecting to Fyers WebSocket for tick archival...")
    socket.connect()


if __name__ == "__main__":
    main()
