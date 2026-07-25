import sys

# Force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

import yfinance as yf

from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr

from strategy.signal_engine import generate_filtered_signal
from strategy.risk_engine import calculate_atr_levels
from strategy.market_structure import get_market_structure
from strategy.support_resistance import get_support_resistance
from strategy.volume_engine import get_volume_analysis
from strategy.candlestick_engine import get_candlestick_pattern
from strategy.data_validator import validate_market_data

from strategy.paper_trading import load_portfolio, save_portfolio, process_signal
from strategy.report_engine import print_paper_portfolio, format_paper_trade_message

from report.notifier import notify


def main():

    print("Running Paper Trade check on NIFTY...")

    data = yf.download("^NSEI", period="5d", interval="15m")

    is_valid, errors = validate_market_data(data)

    if not is_valid:

        print("\nDATA VALIDATION FAILED")

        for error in errors:
            print("-", error)

        return

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    ema20 = calculate_ema(data, 20)
    ema50 = calculate_ema(data, 50)
    rsi = calculate_rsi(data)
    atr = calculate_atr(data)

    price = close.iloc[-1]

    structure = get_market_structure(data)
    levels = get_support_resistance(data)
    volume_analysis = get_volume_analysis(data)
    candle_pattern = get_candlestick_pattern(data)

    signal, filter_notes = generate_filtered_signal(
        ema20.iloc[-1],
        ema50.iloc[-1],
        rsi.iloc[-1],
        structure["Trend Analysis"]["Trend"],
        levels,
        volume_analysis,
        candle_pattern
    )

    portfolio = load_portfolio()

    if portfolio["Positions"].get("NIFTY 50") is None and signal == "BUY":

        stop_loss, target = calculate_atr_levels(price, atr.iloc[-1], "BUY")

    else:

        stop_loss, target = None, None

    portfolio, action = process_signal(portfolio, "NIFTY 50", signal, price, stop_loss, target)

    save_portfolio(portfolio)

    print(f"\nSignal : {signal}")
    print(f"Action : {action}")

    if filter_notes:

        print("Filters Applied")

        for note in filter_notes:
            print(f"  - {note}")

    print_paper_portfolio(portfolio)

    message = format_paper_trade_message(price, signal, action, filter_notes, portfolio)

    notify(message)


if __name__ == "__main__":
    main()
