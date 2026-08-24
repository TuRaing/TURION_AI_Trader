import argparse
import bisect
import datetime
import glob
import json
import os
from collections import defaultdict

from strategy.options_transaction_costs import calculate_options_round_trip_cost

# Added 24-Aug-2026, at the user's own explicit request, right after
# run_depth_collector.py started archiving real-time DepthUpdate data
# (sub-second granularity, confirmed live) - the measurement half of
# the pair. Same walk-the-book method the 21-Aug retrospective analysis
# used against fyers_depth_collector.py's ~5-min-stale REST snapshots
# (which found LTP-based PnL overstates realized PnL by ~87-91% on a
# thin ATM book) - but matched against THIS archive, whose nearest
# snapshot to a real trade's Entry/Exit Time should now be seconds, not
# minutes, away.
#
# Manually run, not scheduled (same "one-off/on-demand analysis, not a
# continuous service" nature as strategy/fyers_depth_collector.py's own
# module). Reads real trade records from reports/fyers_options_*_
# portfolio.json - every RSI-momentum book (NIFTY) and both oi_footprint
# books (NIFTY + BANKNIFTY, WIDENED same day once run_depth_collector.py
# itself grew a BANKNIFTY branch - user's own "check all VPS strategies"
# ask) - and data/depth/depth_DDMMYY.jsonl (the real-time archive),
# joins them by nearest received_at, and reports recorded (LTP) vs
# realistic (walked) Net PnL per trade.

DEPTH_DIR = os.path.join("data", "depth")
REPORTS_DIR = "reports"

# name substring -> real lot size (strategy/fyers_options_engine.py's own
# INDEX_CONFIG) - every book this script covers is one or the other.
BOOK_PREFIXES_AND_LOT_SIZE = (
    ("st2_threshold", 75),
    ("simple_st1_threshold", 75),
    ("oi_footprint_eventdriven_nifty", 75),
    ("oi_footprint_eventdriven_banknifty", 30),
)


def load_depth_by_symbol(depth_path):
    """Real depth records for one day, indexed by symbol, sorted by
    received_at - same shape strategy/depth_collector.py's own
    format_depth_record() produces."""

    by_symbol = defaultdict(list)

    with open(depth_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            record["_dt"] = datetime.datetime.strptime(record["received_at"], "%Y-%m-%d %H:%M:%S.%f")
            by_symbol[record["symbol"]].append(record)

    for symbol in by_symbol:
        by_symbol[symbol].sort(key=lambda r: r["_dt"])

    return by_symbol


def nearest_record(records, target_dt):
    """Real depth record closest in time to target_dt - binary search
    since records are sorted, same idea as the earlier scratchpad
    analysis but O(log n) instead of a full linear min() scan, since
    this archive is far denser (sub-second cadence, not 5-min)."""

    times = [r["_dt"] for r in records]
    idx = bisect.bisect_left(times, target_dt)

    candidates = [i for i in (idx - 1, idx) if 0 <= i < len(records)]
    return min(candidates, key=lambda i: abs((records[i]["_dt"] - target_dt).total_seconds()))


def walk_book(levels, quantity):
    """Volume-weighted average fill price walking one side of the book
    (Bids or Asks, each {"price", "volume", "ord"}) until `quantity` is
    filled. Returns (avg_price, ran_out_of_book)."""

    remaining, cost, filled = quantity, 0.0, 0

    for level in levels:
        take = min(remaining, level["volume"])
        cost += take * level["price"]
        filled += take
        remaining -= take
        if remaining <= 0:
            break

    if filled == 0:
        return None, True

    return cost / filled, remaining > 0


def matched_books():
    """(path, lot_size) for every portfolio file this script can match
    against the real-time depth archive - every RSI-momentum book
    (NIFTY, lot_size 75) and both oi_footprint books (NIFTY 75 /
    BANKNIFTY 30) - see BOOK_PREFIXES_AND_LOT_SIZE's own comment."""

    matched = []
    for path in glob.glob(os.path.join(REPORTS_DIR, "fyers_options_*_eventdriven*_portfolio.json")):
        name = os.path.basename(path)
        for prefix, lot_size in BOOK_PREFIXES_AND_LOT_SIZE:
            if prefix in name:
                matched.append((path, lot_size))
                break
    return sorted(matched)


def analyze(depth_path, max_gap_seconds=20):

    depth_by_symbol = load_depth_by_symbol(depth_path)
    results = []

    for path, lot_size in matched_books():
        data = json.load(open(path, encoding="utf-8"))

        for trade in data.get("Closed Trades", []):
            symbol = trade.get("Symbol")
            records = depth_by_symbol.get(symbol)

            if not records:
                continue

            entry_dt = datetime.datetime.strptime(trade["Entry Time"], "%Y-%m-%d %H:%M:%S")
            exit_dt = datetime.datetime.strptime(trade["Exit Time"], "%Y-%m-%d %H:%M:%S")

            entry_idx = nearest_record(records, entry_dt)
            exit_idx = nearest_record(records, exit_dt)

            entry_gap = abs((records[entry_idx]["_dt"] - entry_dt).total_seconds())
            exit_gap = abs((records[exit_idx]["_dt"] - exit_dt).total_seconds())

            if entry_gap > max_gap_seconds or exit_gap > max_gap_seconds:
                continue

            quantity = trade["Lots"] * lot_size

            entry_fill, entry_ran_out = walk_book(records[entry_idx]["Asks"], quantity)
            exit_fill, exit_ran_out = walk_book(records[exit_idx]["Bids"], quantity)

            if entry_fill is None or exit_fill is None:
                continue

            recorded_net_pnl = trade["Net PnL"]

            gross_walked = (exit_fill - entry_fill) * quantity
            cost = calculate_options_round_trip_cost(entry_fill, exit_fill, lot_size, trade["Lots"])
            realistic_net_pnl = gross_walked - cost

            results.append({
                "book": os.path.basename(path),
                "symbol": symbol,
                "entry_time": trade["Entry Time"],
                "exit_time": trade["Exit Time"],
                "quantity": quantity,
                "recorded_net_pnl": recorded_net_pnl,
                "realistic_net_pnl": round(realistic_net_pnl, 2),
                "entry_gap_s": round(entry_gap, 2),
                "exit_gap_s": round(exit_gap, 2),
                "entry_ran_out_of_book": entry_ran_out,
                "exit_ran_out_of_book": exit_ran_out,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="DDMMYY (default: today, IST)", default=None)
    parser.add_argument("--max-gap-seconds", type=float, default=20,
                         help="skip a trade if the nearest depth record is farther than this")
    args = parser.parse_args()

    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    date_str = args.date or datetime.datetime.now(IST).strftime("%d%m%y")
    depth_path = os.path.join(DEPTH_DIR, f"depth_{date_str}.jsonl")

    if not os.path.exists(depth_path):
        print(f"No depth archive found at {depth_path}")
        return

    results = analyze(depth_path, args.max_gap_seconds)

    print(f"Matched {len(results)} trades to real depth records (within {args.max_gap_seconds}s).\n")

    if not results:
        return

    print(f"{'Book':50} {'Time':17} {'Recorded':>12} {'Realistic':>12} {'Gap(s) E/X':>12}")
    total_recorded, total_realistic = 0.0, 0.0

    for r in results:
        total_recorded += r["recorded_net_pnl"]
        total_realistic += r["realistic_net_pnl"]
        print(f"{r['book']:50} {r['entry_time'][11:]:17} {r['recorded_net_pnl']:>12,.2f} "
              f"{r['realistic_net_pnl']:>12,.2f} {r['entry_gap_s']:>5.1f}/{r['exit_gap_s']:<5.1f}")

    print()
    print(f"TOTAL recorded (LTP-based):  Rs {total_recorded:,.2f}")
    print(f"TOTAL realistic (real depth, walk-the-book): Rs {total_realistic:,.2f}")
    if total_recorded:
        print(f"Overstatement: {(total_recorded - total_realistic) / abs(total_recorded) * 100:.1f}%")


if __name__ == "__main__":
    main()
