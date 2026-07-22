import argparse
import sys

# Force UTF-8 stdout so emoji/currency symbols don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from strategy.orb_vwap_backtest import run_orb_vwap_backtest, DEFAULT_COST_PER_TRADE
from strategy.report_engine import print_orb_vwap_backtest_report


def main():

    parser = argparse.ArgumentParser(
        description="Backtest an Opening Range Breakout entry, filtered by VWAP "
                     "direction and a volume spike - the intraday candidate for the "
                     "Best Trade Engine researched 21-Jul. Analysis only - not wired "
                     "into any paper trading or live automation."
    )

    parser.add_argument("--symbol", default="^NSEI")
    parser.add_argument("--period", default="60d", help="History window (Yahoo limits 5m data to ~60d)")
    parser.add_argument("--interval", default="5m")
    parser.add_argument("--orb-minutes", type=int, default=15, help="Opening Range length in minutes")
    parser.add_argument("--atr-sl-mult", type=float, default=1.0, help="Stop-loss distance as a multiple of ATR")
    parser.add_argument("--atr-target-mult", type=float, default=2.0, help="Target distance as a multiple of ATR")
    parser.add_argument("--cost-per-trade", type=float, default=DEFAULT_COST_PER_TRADE, help="Estimated real round-trip cost (Rs) subtracted for Net PnL")
    parser.add_argument("--no-short", action="store_true", help="Only take BUY entries, skip SELL/short entries")

    args = parser.parse_args()

    print(f"Running ORB+VWAP+Volume backtest on {args.symbol} ({args.interval}, {args.period})...")

    result = run_orb_vwap_backtest(
        symbol=args.symbol,
        period=args.period,
        interval=args.interval,
        orb_minutes=args.orb_minutes,
        atr_sl_mult=args.atr_sl_mult,
        atr_target_mult=args.atr_target_mult,
        cost_per_trade=args.cost_per_trade,
        allow_short=not args.no_short,
    )

    print_orb_vwap_backtest_report(args.symbol, result)


if __name__ == "__main__":
    main()
