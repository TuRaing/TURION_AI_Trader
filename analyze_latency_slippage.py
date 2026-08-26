import argparse
import bisect
import datetime
import glob
import json
import os
import statistics

from strategy.tick_collector import tick_latency_ms

# Added 26-Aug-2026, at the user's own explicit request: "आपला slippage
# latency ने होत आहे का नाही, हे कसं समजणार" - is our already-measured
# depth/spread-driven slippage (analyze_realtime_depth_slippage.py)
# actually caused (or made worse) by the ~0.7-1.2s exchange-to-VPS
# latency, or is that a separate, much smaller effect? Same real tick
# archive (data/ticks/ticks_DDMMYY.jsonl) already used for today's
# latency measurement - no new data collection needed.
#
# Method: rather than trying to re-derive a per-trade "what price would
# we have gotten with zero latency" (which would need to assume we
# could have placed a real order at the exact tick moment - not
# something this project can verify without a real broker execution
# venue), this measures something directly answerable from real data:
# how much does an ATM option's own LTP typically move over a time
# window equal to the real measured latency? That rupee figure is
# directly comparable to the spread-driven slippage rupee figures
# analyze_realtime_depth_slippage.py already reports - if it's small
# relative to those, latency is a minor contributor; if comparable or
# larger, it's a real, separate driver worth addressing on its own.

TICK_DIR = os.path.join("data", "ticks")


def load_ticks_by_symbol(tick_path):
    """Real tick records for one day, indexed by symbol, sorted by
    received_at - only CE/PE legs (SPOT has no tradeable LTP for this
    purpose)."""

    by_symbol = {}

    with open(tick_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)

            if record.get("leg") not in ("CE", "PE"):
                continue

            if record.get("ltp") is None or record.get("received_at") is None:
                continue

            record["_dt"] = datetime.datetime.strptime(record["received_at"], "%Y-%m-%d %H:%M:%S.%f")
            by_symbol.setdefault(record["symbol"], []).append(record)

    for symbol in by_symbol:
        by_symbol[symbol].sort(key=lambda r: r["_dt"])

    return by_symbol


def price_deltas_over_window(records, window_seconds):
    """
    For every tick in `records` (sorted, real received_at timestamps),
    finds the next tick at least `window_seconds` later (by our own
    wall clock - the same received_at basis tick_latency_ms() already
    uses) and returns the list of |LTP change| over that gap - the
    real, observed price movement an order would be exposed to if it
    took `window_seconds` to actually reach the market after a
    decision was made. Pure/testable - no I/O.
    """

    times = [r["_dt"] for r in records]
    deltas = []

    for i, r in enumerate(records):
        target = r["_dt"] + datetime.timedelta(seconds=window_seconds)
        j = bisect.bisect_left(times, target, lo=i)

        if j >= len(records):
            continue

        deltas.append(abs(records[j]["ltp"] - r["ltp"]))

    return deltas


def median_measured_latency_seconds(tick_path):
    """Real median tick_latency_ms() across today's whole archive - the
    same figure the earlier VPS health-check reported, recomputed here
    so this script is self-contained (never hardcodes a "typical
    latency" number - always derives it from today's own real data)."""

    latencies = []

    with open(tick_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            ms = tick_latency_ms(record)
            if ms is not None:
                latencies.append(ms)

    if not latencies:
        return None

    return statistics.median(latencies) / 1000.0


def analyze(tick_path, lot_size=75, window_seconds=None):
    by_symbol = load_ticks_by_symbol(tick_path)

    if window_seconds is None:
        window_seconds = median_measured_latency_seconds(tick_path)

    if window_seconds is None:
        return None

    results = []

    for symbol, records in by_symbol.items():
        deltas = price_deltas_over_window(records, window_seconds)

        if not deltas:
            continue

        results.append({
            "symbol": symbol,
            "ticks": len(records),
            "windows_measured": len(deltas),
            "median_price_move": round(statistics.median(deltas), 2),
            "mean_price_move": round(statistics.mean(deltas), 2),
            "p90_price_move": round(sorted(deltas)[int(len(deltas) * 0.9)], 2) if len(deltas) >= 10 else None,
            "median_rupee_impact_1_lot": round(statistics.median(deltas) * lot_size, 2),
        })

    return {"window_seconds": window_seconds, "symbols": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="DDMMYY (default: today, IST)", default=None)
    parser.add_argument("--lot-size", type=int, default=75, help="for the rupee-impact column")
    parser.add_argument("--window-seconds", type=float, default=None,
                         help="override the latency window (default: today's own measured median)")
    args = parser.parse_args()

    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    date_str = args.date or datetime.datetime.now(IST).strftime("%d%m%y")
    tick_path = os.path.join(TICK_DIR, f"ticks_{date_str}.jsonl")

    if not os.path.exists(tick_path):
        print(f"No tick archive found at {tick_path}")
        return

    result = analyze(tick_path, lot_size=args.lot_size, window_seconds=args.window_seconds)

    if result is None:
        print("No latency data available to derive a window from today's archive.")
        return

    window_source = "today's real median tick latency" if args.window_seconds is None else "user-specified"
    print(f"Latency window used: {result['window_seconds']:.3f}s ({window_source})\n")

    print(f"{'Symbol':32} {'Ticks':>8} {'Windows':>8} {'Median move':>12} {'Mean move':>10} "
          f"{'P90 move':>9} {'Rs/lot (median)':>16}")

    for r in sorted(result["symbols"], key=lambda x: -x["median_rupee_impact_1_lot"]):
        print(f"{r['symbol']:32} {r['ticks']:>8} {r['windows_measured']:>8} "
              f"{r['median_price_move']:>12.2f} {r['mean_price_move']:>10.2f} "
              f"{str(r['p90_price_move']):>9} {r['median_rupee_impact_1_lot']:>16,.2f}")


if __name__ == "__main__":
    main()
