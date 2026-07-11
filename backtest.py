import argparse
import sys

# Updated: 2026-07-11 - force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from strategy.backtest_engine import run_backtest
from strategy.report_engine import print_backtest_report


def main():

    parser = argparse.ArgumentParser(description="TURION AI Trader Backtest")

    parser.add_argument("--symbol", default="^NSEI")
    parser.add_argument("--period", default="60d")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--stop-loss", type=float, default=0.3, help="Stop-loss %% from entry price")
    parser.add_argument("--target", type=float, default=0.6, help="Target %% from entry price")

    args = parser.parse_args()

    print(f"Running Backtest on {args.symbol} ({args.period}, {args.interval})...")
    print(f"Stop-Loss: {args.stop_loss}%  Target: {args.target}%")

    summary = run_backtest(
        symbol=args.symbol,
        period=args.period,
        interval=args.interval,
        stop_loss_pct=args.stop_loss,
        target_pct=args.target
    )

    print_backtest_report(summary)


if __name__ == "__main__":
    main()
