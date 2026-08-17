from strategy.fyers_options_collector import snapshot as collect_options_snapshot
from strategy.fyers_depth_collector import snapshot as collect_depth_snapshot
from strategy.fyers_options_paper_trading import check_or_open as check_options_position
from strategy.fyers_paper_trading import run_watchlist_paper_trading
from fyers_daily_best_trade import main as run_best_trade_check
from data.watchlist import NIFTY_50_SYMBOLS, INDICES

# Added 05-Aug-2026, split further same day - the "run everything for
# today" task list, broken into pieces so each can run at its own
# appropriate cadence instead of one heavy combined job:
#
# - run_options_check(): light (a couple of API calls), benefits from
#   checking OFTEN - real option premium can move several % within a
#   single minute (leverage - see 04-Aug's research), so a 1-min cron-
#   job.org trigger (fyers_options_watch.yml) calls just this.
# - run_options_snapshot(): the historical-archive collector, doesn't
#   need to be as frequent as the position check itself.
# - run_swing_and_intraday(): comparatively heavy (a full 52-symbol
#   scan, Intraday's is a 3-timeframe alignment check per symbol) AND
#   doesn't benefit from checking faster than the underlying data's own
#   cadence (Swing is a daily-timeframe strategy; Intraday's entry
#   timeframe is 5m) - a 5-min cron-job.org trigger
#   (fyers_scheduled_check.yml) calls this + the snapshot together.
#
# run_all_tasks() (used by fyers_trigger_run.py, the one-shot morning
# login trigger) still runs everything once, in one go.


def run_options_check():

    print("\n--- Options paper trading check ---")
    try:
        _, action = check_options_position()
        print(action)
    except Exception as error:
        print(f"Options paper trading check failed (continuing): {error}")


def run_options_snapshot():

    print("\n--- Options premium snapshot ---")
    try:
        count = collect_options_snapshot()
        print(f"Wrote {count} option-leg records.")
    except Exception as error:
        print(f"Options snapshot failed (continuing): {error}")


def run_depth_snapshot():

    # Added 17-Aug-2026 - same cadence as run_options_snapshot() (both
    # called together every 5 min from fyers_scheduled_run.py), same
    # try/except-and-continue shape. Deliberately lightweight (only 6
    # API calls per run - ATM CE+PE depth x 2 indices, plus the 2 chain
    # calls to locate ATM) - checked against Fyers' real documented
    # quota (100,000/day, 200/min) before wiring this in: at 5-min
    # cadence this adds ~450 calls/day, under 0.5% of the daily budget,
    # not the actual cause of 17-Aug's API-limit-exceeded incident
    # (that was live-trading check volume on an unusually high-volume
    # 676-trade day - see PROJECT_STATUS.md).
    print("\n--- Options depth snapshot ---")
    try:
        count = collect_depth_snapshot()
        print(f"Wrote {count} depth records.")
    except Exception as error:
        print(f"Depth snapshot failed (continuing): {error}")


def run_swing_and_intraday():

    print("\n--- Swing (Watchlist) paper trading ---")
    try:
        symbols = dict(INDICES)
        for ticker in NIFTY_50_SYMBOLS:
            symbols[ticker.replace(".NS", "")] = ticker
        _, events = run_watchlist_paper_trading(symbols, period="6mo", interval="1d")
        print(f"{len(events)} Swing event(s) this run.")
    except Exception as error:
        print(f"Swing paper trading failed (continuing): {error}")

    print("\n--- Intraday (Best Trade) check ---")
    try:
        run_best_trade_check()
    except Exception as error:
        print(f"Intraday check failed (continuing): {error}")


def run_all_tasks():

    run_options_snapshot()
    run_depth_snapshot()
    run_options_check()
    run_swing_and_intraday()
