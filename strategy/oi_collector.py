import datetime

# Added 28-Aug-2026, at the user's own explicit request after today's
# real backtest work found GEX-wall/momentum-exhaustion, a PCR event-
# driven port, and an OI+Volume confirmation filter for oi_footprint
# all genuinely blocked on the same real gap: OI has only ever been
# read live (strategy/fyers_options_oi_footprint.py's own _read_atm_
# oi_snapshot(), a real option-chain REST call already made every
# ~5 minutes by event_driven_runner.py's refresh_oi_snapshots() for the
# 2 live oi_footprint books) and never archived - so none of today's
# 3 blocked ideas could be backtested against real history the way
# the tick/depth archives already let order-book-imbalance/VWAP/ORB/
# volume-spike be tested the same day.
#
# This module is the archival equivalent of strategy/depth_collector.py
# (pure record-shaping only, no I/O) - refresh_oi_snapshots() is the
# ONLY caller, appending one record per already-happening REST fetch
# rather than adding any new API load. Pure/testable logic only,
# same split as every other collector in this codebase.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def oi_log_filename(now_ist):
    """
    One file per calendar day, e.g. "oi_280826.jsonl" (DD-MM-YY,
    28-Aug-2026) - same convention as strategy/depth_collector.py's own
    depth_log_filename()/strategy/tick_collector.py's tick_log_filename().
    """

    return f"oi_{now_ist.strftime('%d%m%y')}.jsonl"


def format_oi_record(index, snapshot, timestamp):
    """
    Turns one real ATM OI snapshot (strategy/fyers_options_oi_
    footprint.py's own _read_atm_oi_snapshot() return shape -
    {"spot", "strike", "ce_oi", "pe_oi"}) into one JSONL-ready archive
    record. `timestamp` is the already-IST datetime refresh_oi_
    snapshots() itself uses (same value passed to on_oi_snapshot()) -
    not re-derived here, so this record's own timestamp always matches
    what the live decision path actually saw.
    """

    return {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "index": index,
        "spot": snapshot["spot"],
        "strike": snapshot["strike"],
        "ce_oi": snapshot["ce_oi"],
        "pe_oi": snapshot["pe_oi"],
    }
