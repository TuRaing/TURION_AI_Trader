import datetime
import json
import os
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
# Same buffering fix as run_tick_collector.py/run_event_driven_engine.py's
# matching lines - this process runs under the identical systemd/non-TTY
# conditions.

from report.firebase_realtime_sync import fetch_access_token
from strategy.event_driven_runner import pick_atm_symbols
from strategy.depth_collector import depth_log_filename, format_depth_record

# Added 24-Aug-2026, at the user's own explicit request - the VPS entry
# point for real-time DepthUpdate archival (strategy/depth_collector.py's
# pure logic). Same "top-level script resolves real credentials, module
# takes them as a plain parameter" split this project already uses for
# run_tick_collector.py/run_event_driven_engine.py.
#
# WIDENED to NIFTY + BANKNIFTY same day (was NIFTY-only for the first
# few hours) - user's own explicit ask to cover "all VPS strategies"'
# real slippage tomorrow, which includes oi_footprint_banknifty
# (BANKNIFTY-only, the RSI-momentum family's own NIFTY-only scope
# doesn't cover it). ATM CE/PE only per index still - matches strategy/
# tick_collector.py's own "deliberately ATM-only, not the full chain"
# scope.
#
# NOT LIVE-TESTED beyond the one real capture verify_depth_websocket.py
# already did (24-Aug-2026, 20 real messages, confirmed shape) - this
# is that same verified subscription pattern, just run continuously
# (both indices) and archived to disk instead of stopping after 20
# messages.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DEPTH_DIR = os.path.join("data", "depth")
ATM_RECHECK_SECONDS = 15 * 60  # same cadence as run_tick_collector.py's
# own atm_recheck_loop - frequent enough to track real intraday drift,
# infrequent enough not to hammer the option-chain REST endpoint.
INDICES = ("NIFTY", "BANKNIFTY")


class DepthWriter:
    """
    Owns the single open file handle for today's depth log, appending
    one JSON line per DepthUpdate message. Rotates to a new file
    automatically if the calendar date changes while running - same
    pattern as run_tick_collector.py's own TickWriter.
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

        os.makedirs(DEPTH_DIR, exist_ok=True)
        path = os.path.join(DEPTH_DIR, depth_log_filename(now))
        self._fh = open(path, "a", encoding="utf-8")
        self._date = today
        print(f"Depth log: {path}")

    def write(self, record):
        self._ensure_open_for_today()
        self._fh.write(json.dumps(record) + "\n")
        self._fh.flush()


def main():

    # Added 24-Aug-2026 - same weekend guard as run_event_driven_engine.py/
    # run_tick_collector.py (22-Aug-2026 fix) - see those files' own
    # comments for the real crash-loop incident this avoids. Checked
    # FIRST, before even fetching a token.
    now_ist = datetime.datetime.now(IST)
    if now_ist.weekday() >= 5:  # Saturday=5, Sunday=6
        print(f"{now_ist.strftime('%A')} - NSE is closed on weekends, skipping this start attempt.")
        sys.exit(0)

    access_token = fetch_access_token()

    if not access_token:
        print("No access_token available via Firebase yet (today's login hasn't run, or "
              "Firebase isn't configured) - skipping this start attempt.")
        sys.exit(0)

    # See run_event_driven_engine.py's matching 21-Aug-2026 comment -
    # pick_atm_symbols() ultimately calls strategy/fyers_auth.py's
    # get_access_token() (local .env only) several layers down; setting
    # the env var directly here makes every one of those calls pick up
    # the real Firebase-sourced token without touching any shared module.
    os.environ["FYERS_ACCESS_TOKEN"] = access_token

    from fyers_apiv3.FyersWebsocket import data_ws  # imported here, not at
    # module level, matching live_tick_harness.py/tick_collector.py's own
    # reasoning - this module stays importable without fyers_apiv3 installed.

    writer = DepthWriter()

    # state[index] = {"strike": int, "symbols": {fyers_symbol: True}} - same
    # per-index shape run_tick_collector.py's own `state` dict already uses.
    print("Fetching initial ATM strikes for NIFTY, BANKNIFTY...")
    state = {}
    for index in INDICES:
        spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)
        state[index] = {"strike": atm_strike, "symbols": {ce_symbol: True, pe_symbol: True}}
        print(f"{index}: spot={spot} atm_strike={atm_strike} ce={ce_symbol} pe={pe_symbol}")

    def all_subscribed_symbols():
        symbols = []
        for index in INDICES:
            symbols.extend(state[index]["symbols"].keys())
        return symbols

    def symbol_is_tracked(symbol):
        return any(symbol in state[index]["symbols"] for index in INDICES)

    def on_message(message):
        symbol = message.get("symbol")

        if not symbol_is_tracked(symbol):
            return  # a message for a symbol we just unsubscribed from mid-flight

        record = format_depth_record(symbol, message, received_at=datetime.datetime.now(IST))
        writer.write(record)

    def on_error(message):
        print(f"[depth collector websocket error] {message}")

    def on_close(message):
        print(f"[depth collector websocket closed] {message}")

    def on_open():
        socket.subscribe(symbols=all_subscribed_symbols(), data_type="DepthUpdate")
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
        from strategy.tick_collector import atm_has_drifted
        from strategy.fyers_options_engine import INDEX_CONFIG

        while True:
            time.sleep(ATM_RECHECK_SECONDS)
            for index in INDICES:
                try:
                    spot, new_strike, ce_symbol, pe_symbol = pick_atm_symbols(index)
                except Exception as error:
                    print(f"{index} ATM re-check failed (continuing on the old strike): {error}")
                    continue

                if not atm_has_drifted(state[index]["strike"], spot, INDEX_CONFIG[index]["strike_step"]):
                    continue

                old_symbols = list(state[index]["symbols"].keys())
                new_symbols = {ce_symbol: True, pe_symbol: True}

                print(f"{index} ATM drifted {state[index]['strike']} -> {new_strike}, re-subscribing.")

                try:
                    socket.unsubscribe(symbols=old_symbols, data_type="DepthUpdate")
                except Exception as error:
                    print(f"Unsubscribe failed for {index} (continuing anyway): {error}")

                socket.subscribe(symbols=list(new_symbols.keys()), data_type="DepthUpdate")
                state[index] = {"strike": new_strike, "symbols": new_symbols}

    threading.Thread(target=atm_recheck_loop, daemon=True).start()

    print("Connecting to Fyers WebSocket for depth archival...")
    socket.connect()

    # See run_tick_collector.py's own 21-Aug-2026 comment - connect() does
    # NOT block, so the main thread must stay alive itself or Python's
    # interpreter-shutdown sequence starts prematurely.
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
