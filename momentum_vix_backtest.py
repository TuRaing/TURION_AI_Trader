import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8")

from strategy.momentum_vix_backtest import run_momentum_vix_backtest


def main():

    parser = argparse.ArgumentParser(
        description="Backtest a Momentum(RSI)+India VIX-filtered directional signal for "
                     "BUY CE/BUY PE - the options candidate researched 21-Jul. Measures "
                     "directional accuracy on the underlying only (no real option premium "
                     "data available for free) - analysis only, not wired into any paper "
                     "trading or live automation."
    )

    parser.add_argument("--symbol", default="^NSEI")
    parser.add_argument("--vix-symbol", default="^INDIAVIX")
    parser.add_argument("--period", default="60d")
    parser.add_argument("--interval", default="15m")
    parser.add_argument("--atr-sl-mult", type=float, default=1.0)
    parser.add_argument("--atr-target-mult", type=float, default=2.0)

    args = parser.parse_args()

    print(f"Running Momentum(RSI)+India VIX backtest on {args.symbol} ({args.interval}, {args.period})...")

    result = run_momentum_vix_backtest(
        symbol=args.symbol,
        vix_symbol=args.vix_symbol,
        period=args.period,
        interval=args.interval,
        atr_sl_mult=args.atr_sl_mult,
        atr_target_mult=args.atr_target_mult,
    )

    print("----------------------------------------")
    print("   MOMENTUM (RSI) + INDIA VIX BACKTEST")
    print("----------------------------------------")
    print(f"Symbol : {args.symbol}")

    if "Error" in result:
        print(f"Error  : {result['Error']}")
        print("----------------------------------------")
        return

    print(f"Total Trades : {result['Total Trades']} (CE: {result['CE Trades']}, PE: {result['PE Trades']})")
    print()
    print(f"Wins (Directional)     : {result['Wins (Directional)']}")
    print(f"Win Rate (Directional) : {result['Win Rate (Directional)']}%")
    print(f"Total Underlying Points: {result['Total Underlying Points']}")
    print("----------------------------------------")
    print("Exit Breakdown")
    for reason, count in result["Exit Reasons"].items():
        print(f"  {reason} : {count}")
    print("----------------------------------------")
    print("Note: directional accuracy on the underlying only - NOT real")
    print("option premium P&L (no free option-chain history available).")
    print("Analysis only, not wired into any paper trading.")
    print("----------------------------------------")


if __name__ == "__main__":
    main()
