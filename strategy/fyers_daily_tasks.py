from strategy.fyers_options_collector import snapshot as collect_options_snapshot
from strategy.fyers_options_paper_trading import check_or_open as check_options_position
from strategy.fyers_paper_trading import run_watchlist_paper_trading
from fyers_daily_best_trade import main as run_best_trade_check
from data.watchlist import NIFTY_50_SYMBOLS, INDICES

# Added 05-Aug-2026 - the actual "run everything for today" task list,
# split out of fyers_trigger_run.py so both that script (the one-shot
# login trigger) and fyers_scheduled_run.py (the every-few-minutes
# scheduled check, reusing that day's already-shared token) call the
# exact same logic instead of two near-duplicate copies drifting apart.


def run_all_tasks():

    print("\n--- Options premium snapshot ---")
    try:
        count = collect_options_snapshot()
        print(f"Wrote {count} option-leg records.")
    except Exception as error:
        print(f"Options snapshot failed (continuing): {error}")

    print("\n--- Options paper trading check ---")
    try:
        _, action = check_options_position()
        print(action)
    except Exception as error:
        print(f"Options paper trading check failed (continuing): {error}")

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
