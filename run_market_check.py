import datetime
import glob
import json
import os

import requests

from strategy.fyers_auth import _app_id, get_access_token
from strategy.tick_collector import tick_log_filename, summarize_tick_latency
from report.market_checks import (
    detect_crash,
    detect_unusual_trade,
    summarize_daily_pnl,
    detect_stale_workflow,
    format_running_market_checklist,
    market_check_log_filename,
)

# Added 19-Aug-2026 - the live wiring for report/market_checks.py's pure
# functions. Originally session-only (19-Aug), now DEPLOYED TO THE VPS
# (20-Aug) alongside the trading engine and tick collector, once the
# VPS existed.
#
# UPDATED 20-Aug-2026 - _resolve_access_token() below tries Firebase
# Realtime Database FIRST (the VPS's only credential source - it has no
# local Fyers login of its own, see report/firebase_realtime_sync.py),
# falling back to the local .env token (get_access_token()) so this
# same file still works unchanged when run by hand on a desktop that
# HAS done its own local `python -m strategy.fyers_auth` login. Only
# the token source changes; FYERS_APP_ID is still needed either way for
# the Authorization header (added to the VPS's own .env alongside the
# Firebase keys - not a secret, it's the same client_id already visible
# in the plain-text OAuth login URL every login uses).

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DATA_BASE_URL = "https://api-t1.fyers.in/data"
LOG_DIR = os.path.join("logs", "market_checks")
MARKET_CLOSE = (15, 30)
TICK_DIR = os.path.join("data", "ticks")


def _todays_tick_latency_line(now):
    """
    Added 20-Aug-2026 - the user's own explicit ask ("30-min checks
    मध्ये latency measure करता येईल का"): reads TODAY's own local tick
    archive (run_tick_collector.py's own file, same VPS - this only
    finds real data when actually run on the VPS, not this desktop)
    and summarizes signal-to-decision latency (real exchange-tick-time
    vs when this process received it, see strategy/tick_collector.py's
    tick_latency_ms()). Never raises - a missing/unreadable tick file
    (collector not running yet, or run locally where it never exists)
    just means "nothing to report", not a check failure.
    """

    path = os.path.join(TICK_DIR, tick_log_filename(now))

    if not os.path.exists(path):
        return "- [ ] Tick latency: no tick data yet today"

    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    summary = summarize_tick_latency(records)

    if summary["count"] == 0:
        return "- [ ] Tick latency: no measurable ticks yet today"

    return (
        f"- [ ] Tick latency (exchange -> VPS): avg {summary['avg_ms']}ms, "
        f"max {summary['max_ms']}ms ({summary['count']} ticks measured)"
    )


def _resolve_access_token():
    from report.firebase_realtime_sync import fetch_access_token

    token = fetch_access_token()

    return token if token else get_access_token()


def _headers():
    return {"Authorization": f"{_app_id()}:{_resolve_access_token()}"}


def _fetch_index_change_pct(fyers_symbol):
    response = requests.get(
        f"{DATA_BASE_URL}/quotes",
        headers=_headers(),
        params={"symbols": fyers_symbol},
        timeout=15,
    )
    data = response.json()

    if data.get("s") != "ok" or not data.get("d"):
        raise RuntimeError(f"quote fetch failed for {fyers_symbol}: {data}")

    v = data["d"][0]["v"]

    if "chp" in v and v["chp"] is not None:
        return v["chp"]

    return (v["lp"] - v["cp"]) / v["cp"] * 100


def _lot_size_for_book(name):
    # This project's own INDEX_CONFIG (strategy/fyers_options_engine.py)
    # - NIFTY 75, BANKNIFTY 30 - inferred from the filename since this
    # script scans every reports/*_portfolio.json rather than importing
    # each of the 60+ strategy modules just for their lot size.
    return 30 if "banknifty" in name.lower() else 75


def _today_trades(portfolio, today_str):
    # Exit Time is stored IST-naive (this session's own earlier UTC-vs-
    # IST timestamp fix) - a plain string-prefix match against today's
    # IST date, no timezone conversion needed.
    trades = []
    for trade in portfolio.get("Closed Trades", []):
        exit_time = trade.get("Exit Time", "")
        if exit_time.startswith(today_str):
            trades.append(trade)
    return trades


def run_check():
    now = datetime.datetime.now(IST)
    today_str = now.strftime("%Y-%m-%d")

    try:
        nifty_chp = _fetch_index_change_pct("NSE:NIFTY50-INDEX")
        banknifty_chp = _fetch_index_change_pct("NSE:NIFTYBANK-INDEX")
        crash_result = detect_crash(nifty_chp, banknifty_chp)
        data_warning = None
    except Exception as exc:
        crash_result = (False, None)
        data_warning = f"Live index data unavailable ({exc}) - crash check skipped this run."

    books_today_trades = {}
    unusual_trades = []
    strategy_workflows = []

    for path in sorted(glob.glob(os.path.join("reports", "*_portfolio.json"))):
        name = os.path.splitext(os.path.basename(path))[0]

        try:
            with open(path, encoding="utf-8") as fh:
                portfolio = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue

        today_trades = _today_trades(portfolio, today_str)
        books_today_trades[name] = today_trades

        lot_size = _lot_size_for_book(name)
        for trade in today_trades:
            is_unusual, reason = detect_unusual_trade(trade, lot_size)
            if is_unusual:
                unusual_trades.append((name, reason))

        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path), tz=IST)
        is_stale, gap = detect_stale_workflow(mtime, now)
        strategy_workflows.append((name, is_stale, gap))

    pnl_summary = summarize_daily_pnl(books_today_trades)

    report = format_running_market_checklist(
        now_ist=now,
        crash_result=crash_result,
        unusual_trades=unusual_trades,
        pnl_summary=pnl_summary,
        strategy_workflows=strategy_workflows,
    )

    if data_warning:
        lines = report.split("\n")
        lines.insert(2, f"> NOTE: {data_warning}")
        report = "\n".join(lines)

    report = report.rstrip("\n") + "\n" + _todays_tick_latency_line(now) + "\n"

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, market_check_log_filename(now))
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"\nWritten to {log_path}")

    # Added 20-Aug-2026 - the mobile app's new Checks tab. This one
    # script covers both the running-market checks (09:15-15:15 IST)
    # and the two closing checks (15:30/15:45) - split into "market" vs
    # "after_market" by time of day here, MARKET_CLOSE, since the
    # script itself has no other signal for which cron entry fired it.
    # Best-effort, same "never let a sync failure break the actual
    # check" rule as every other Firebase call in this project.
    try:
        from report.firebase_realtime_sync import sync_health_check
        check_type = "after_market" if (now.hour, now.minute) >= MARKET_CLOSE else "market"
        sync_health_check(check_type, report, now.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as error:
        print(f"Health-check Firebase sync failed (continuing): {error}")

    return log_path


if __name__ == "__main__":
    run_check()
