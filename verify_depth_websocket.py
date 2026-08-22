import datetime
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from report.firebase_realtime_sync import fetch_access_token
from strategy.event_driven_runner import pick_atm_symbols

# Added 22-Aug-2026, at the user's own request - a ONE-OFF, manually-run
# verification tool, NOT a permanent service (no systemd unit, no cron
# entry) - the goal is only to observe the REAL raw shape of a Fyers
# WebSocket "DepthUpdate" message before writing any real parsing code
# against it.
#
# WHY THIS EXISTS: real-time full order-book depth (5-level bid/ask,
# not just top-of-book) would let the depth-slippage analysis (see
# today's real 21-Aug finding - LTP-based PnL overstated by ~87-91% on
# a thin ATM book) use the EXACT moment of a trade instead of a ~5-min-
# stale REST /depth snapshot (strategy/fyers_depth_collector.py, quota-
# limited, manual-run only). Real web research (22-Aug-2026) confirmed
# a "DepthUpdate" data_type exists as an alternative to the
# "SymbolUpdate" this project's own event_driven_runner.py/tick_
# collector.py already use (same FyersDataSocket.subscribe() call,
# just a different data_type string) - but could NOT confirm the exact
# message field shape from any documentation or sample code found
# (conflicting signals - some sources describe a DIFFERENT, possibly
# paid "50 Market Depth" product using protobuf, not plain JSON).
#
# SAME LESSON THIS PROJECT ALREADY LEARNED THE HARD WAY for the REST
# /depth endpoint (see doc/16aug26_SESSION_LOG.md - the first live run
# needed 3 rounds of fixes because the assumed shape was wrong) - do
# NOT guess the shape and write real parsing/archival code against it.
# This script does nothing except print/save whatever raw dict the SDK
# actually hands back, unmodified, so a human can look at real data
# before ANY of that gets built.
#
# Run manually (not scheduled) on a day the market is open:
#   venv/bin/python verify_depth_websocket.py
# Stops itself after MAX_MESSAGES messages or MAX_SECONDS, whichever
# comes first - never runs unattended/forever like the real collectors.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
OUTPUT_PATH = os.path.join("data", "depth_websocket_verification.jsonl")
MAX_MESSAGES = 20
MAX_SECONDS = 120


def main():

    access_token = fetch_access_token()

    if not access_token:
        print("No access_token available via Firebase - can't run this verification "
              "(same requirement as the real event-driven engine).")
        sys.exit(1)

    os.environ["FYERS_ACCESS_TOKEN"] = access_token  # see run_event_driven_engine.py's
    # own 21-Aug-2026 comment for why this line is needed - pick_atm_symbols()
    # ultimately reads strategy/fyers_auth.py's LOCAL .env token otherwise.

    print("Fetching ATM NIFTY CE/PE to subscribe to (same ATM formula every other "
          "strategy in this project already uses)...")
    spot, atm_strike, ce_symbol, pe_symbol = pick_atm_symbols("NIFTY")
    print(f"NIFTY spot={spot} atm_strike={atm_strike} ce={ce_symbol} pe={pe_symbol}")

    from fyers_apiv3.FyersWebsocket import data_ws  # imported here, not at module
    # level, matching strategy/live_tick_harness.py's own reasoning - this
    # module stays importable without fyers_apiv3 installed.

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    out_file = open(OUTPUT_PATH, "a", encoding="utf-8")

    state = {"count": 0, "started_at": None}

    def on_message(message):
        # No socket.close()/disconnect() call here on purpose - this
        # project has no existing, verified call site for stopping a
        # FyersDataSocket mid-run (grepped - only .subscribe()/
        # .unsubscribe()/.connect()/.keep_running() are used anywhere),
        # and guessing a method name is exactly the mistake this whole
        # script exists to avoid making about DepthUpdate's shape. The
        # main thread's own deadline loop below just stops COUNTING
        # (and the process exits shortly after) instead.
        if state["count"] >= MAX_MESSAGES:
            return

        state["count"] += 1

        record = {
            "received_at": datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "raw_message": message,
        }

        print(f"[{state['count']}/{MAX_MESSAGES}] RAW: {json.dumps(message, default=str)}")
        out_file.write(json.dumps(record, default=str) + "\n")
        out_file.flush()

        if state["count"] >= MAX_MESSAGES:
            print(f"Reached {MAX_MESSAGES} messages - the main loop below will exit shortly.")

    def on_error(message):
        print(f"[websocket error] {message}")

    def on_close(message):
        print(f"[websocket closed] {message}")

    def on_open():
        print(f"Connected - subscribing to DepthUpdate for {ce_symbol}, {pe_symbol}...")
        socket.subscribe(symbols=[ce_symbol, pe_symbol], data_type="DepthUpdate")
        state["started_at"] = time.monotonic()
        socket.keep_running()

    socket = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=False,  # deliberately NOT reconnect=True (unlike the real
        # engines) - a one-off verification run should just stop on any
        # disconnect, not keep retrying unattended.
        on_connect=on_open,
        on_close=on_close,
        on_error=on_error,
        on_message=on_message,
    )

    print(f"Connecting to Fyers WebSocket (DepthUpdate verification) - will stop after "
          f"{MAX_MESSAGES} messages or {MAX_SECONDS}s, whichever first...")
    socket.connect()

    # See run_tick_collector.py's own 21-Aug-2026 comment - connect() does
    # NOT block, so the main thread must stay alive itself or Python's
    # interpreter-shutdown sequence starts prematurely.
    deadline = time.monotonic() + MAX_SECONDS
    while time.monotonic() < deadline and state["count"] < MAX_MESSAGES:
        time.sleep(1)

    print(f"Stopping - received {state['count']} message(s). Raw output saved to {OUTPUT_PATH}")
    out_file.close()


if __name__ == "__main__":
    main()
