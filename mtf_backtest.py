import argparse
import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from strategy.multi_timeframe_backtest import run_multi_timeframe_backtest
from strategy.report_engine import print_multi_timeframe_backtest_report


def main():

    parser = argparse.ArgumentParser(
        description="Backtest the 15m/5m alignment core of the Best Trade Engine's "
                     "Multi-Timeframe Engine. Analysis only - not wired into any "
                     "paper trading or live automation."
    )

    parser.add_argument("--symbol", default="^NSEI")
    parser.add_argument("--trend-period", default="60d", help="History window for the 15m trend timeframe")
    parser.add_argument("--entry-period", default="60d", help="History window for the 5m entry timeframe")
    parser.add_argument("--atr-sl-mult", type=float, default=1.5, help="Stop-loss distance as a multiple of ATR")
    parser.add_argument("--atr-target-mult", type=float, default=3.0, help="Target distance as a multiple of ATR")

    args = parser.parse_args()

    print(f"Running 15m/5m Multi-Timeframe backtest on {args.symbol}...")

    result = run_multi_timeframe_backtest(
        symbol=args.symbol,
        trend_period=args.trend_period,
        entry_period=args.entry_period,
        stop_loss_atr_mult=args.atr_sl_mult,
        target_atr_mult=args.atr_target_mult,
    )

    print_multi_timeframe_backtest_report(args.symbol, result)


if __name__ == "__main__":
    main()
