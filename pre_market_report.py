import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

from data.watchlist import INDICES
from strategy.watchlist_scanner import download_watchlist, analyze_symbol, MIN_CANDLES
from strategy.support_resistance import get_support_resistance
from strategy.paper_trading import load_portfolio

from report.notifier import notify


def build_index_section(name, frame):

    analysis = analyze_symbol(frame)
    levels = get_support_resistance(frame)

    lines = [
        f"\n{name}",
        f"  Prev Close : {analysis['Price']}",
        f"  Trend Bias : {analysis['Bias']} ({analysis['Confidence']}%)",
        f"  Support    : {levels['Support']}",
        f"  Resistance : {levels['Resistance']}",
        f"  ATR (range): {analysis['ATR']}"
    ]

    if analysis["Candle Pattern"] != "No Pattern":
        lines.append(f"  Last Candle: {analysis['Candle Pattern']}")

    return lines


def main():

    print("Building Pre-Market Report...")

    frames = download_watchlist(INDICES, period="6mo", interval="1d")

    lines = ["TURION AI Trader - Pre-Market Report"]

    for name in INDICES:

        frame = frames.get(name)

        if frame is None or len(frame) < MIN_CANDLES:

            lines.append(f"\n{name}: data unavailable")
            continue

        lines.extend(build_index_section(name, frame))

    portfolio = load_portfolio()
    positions = portfolio["Positions"]

    lines.append(f"\nOpen Paper Positions ({len(positions)}):")

    if positions:

        for symbol, position in positions.items():
            lines.append(f"  {symbol}: Entry {position['Entry Price']:.2f}, "
                         f"SL {position['Stop Loss']:.2f}, Target {position['Target']:.2f}")

    else:

        lines.append("  None")

    lines.append("\nWatch these levels at open. Plan the trade, trade the plan.")

    message = "\n".join(lines)

    print(message)

    notify(message)


if __name__ == "__main__":
    main()
