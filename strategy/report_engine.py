def print_watchlist_report(results, top_n=10):

    print("----------------------------------------")
    print("       WATCHLIST SCAN REPORT")
    print("----------------------------------------")

    print(f"Symbols Scanned : {len(results)}")

    bullish = [r for r in results if r["Bias"] == "Bullish"]
    bearish = [r for r in results if r["Bias"] == "Bearish"]

    print()
    print(f"Top {top_n} Bullish")
    print("----------------------------------------")

    for r in bullish[:top_n]:
        print(f"  {r['Name']:<14} {r['Decision']:<9} {r['Confidence']}%  Price {r['Price']}  ({r['Candle Pattern']})")

    print()
    print(f"Top {top_n} Bearish")
    print("----------------------------------------")

    for r in bearish[:top_n]:
        print(f"  {r['Name']:<14} {r['Decision']:<9} {r['Confidence']}%  Price {r['Price']}  ({r['Candle Pattern']})")

    print("----------------------------------------")


def format_watchlist_message(results, top_n=5):

    bullish = [r for r in results if r["Bias"] == "Bullish"][:top_n]
    bearish = [r for r in results if r["Bias"] == "Bearish"][:top_n]

    lines = ["TURION AI Trader - Watchlist Scan", f"Scanned: {len(results)} symbols"]

    lines.append("\nTop Bullish:")

    for r in bullish:
        lines.append(f"  {r['Name']} - {r['Decision']} ({r['Confidence']}%) @ {r['Price']}")

    lines.append("\nTop Bearish:")

    for r in bearish:
        lines.append(f"  {r['Name']} - {r['Decision']} ({r['Confidence']}%) @ {r['Price']}")

    return "\n".join(lines)


def print_watchlist_paper_trade_report(portfolio, events):

    print("----------------------------------------")
    print("       WATCHLIST PAPER TRADING")
    print("----------------------------------------")

    print(f"Cash : {portfolio['Cash']:.2f}")

    positions = portfolio["Positions"]

    print()
    print(f"Open Positions ({len(positions)})")

    for symbol, position in positions.items():
        print(f"  {symbol}: Entry {position['Entry Price']:.2f}, "
              f"SL {position['Stop Loss']:.2f}, Target {position['Target']:.2f}")

    if events:

        print()
        print("Events This Run")

        for e in events:
            print(f"  {e['Name']}: {e['Action']} @ {e['Price']}")

    closed = portfolio["Closed Trades"]
    total_pnl = sum(t["PnL"] for t in closed)

    print()
    print(f"Closed Trades : {len(closed)}  Total PnL : {total_pnl:.2f}")

    print("----------------------------------------")


def format_watchlist_paper_trade_message(portfolio, events):

    lines = ["TURION AI Trader - Watchlist Paper Trading"]

    if events:

        lines.append("\nEvents:")

        for e in events:
            lines.append(f"  {e['Name']}: {e['Action']} @ {e['Price']}")

    else:

        lines.append("\nNo new trade events this run.")

    positions = portfolio["Positions"]

    lines.append(f"\nOpen Positions ({len(positions)}):")

    for symbol, position in positions.items():
        lines.append(f"  {symbol}: Entry {position['Entry Price']:.2f}, "
                      f"SL {position['Stop Loss']:.2f}, Target {position['Target']:.2f}")

    closed = portfolio["Closed Trades"]
    total_pnl = sum(t["PnL"] for t in closed)

    lines.append(f"\nCash: {portfolio['Cash']:.2f}  Closed Trades: {len(closed)}  Total PnL: {total_pnl:.2f}")

    return "\n".join(lines)


def format_paper_trade_message(price, signal, action, filter_notes, portfolio):

    lines = [
        "TURION AI Trader - Paper Trade Update",
        f"Price  : {price:.2f}",
        f"Signal : {signal}",
        f"Action : {action}"
    ]

    if filter_notes:

        lines.append("Filters:")

        for note in filter_notes:
            lines.append(f"  - {note}")

    position = portfolio["Positions"].get("NIFTY 50")

    if position:

        lines.append(
            f"Open Position: Entry {position['Entry Price']:.2f}, "
            f"SL {position['Stop Loss']:.2f}, Target {position['Target']:.2f}"
        )

    else:

        lines.append("Open Position: None")

    closed = portfolio["Closed Trades"]
    total_pnl = sum(t["PnL"] for t in closed)

    lines.append(f"Cash: {portfolio['Cash']:.2f}  Closed Trades: {len(closed)}  Total PnL: {total_pnl:.2f}")

    return "\n".join(lines)


def print_ai_decision(ai_decision):

    print("----------------------------------------")
    print("       AI DECISION ENGINE")
    print("----------------------------------------")

    print(f"Decision   : {ai_decision['Decision']}")
    print(f"Bias       : {ai_decision['Bias']}")
    print(f"Confidence : {ai_decision['Confidence']}%")

    print()
    print("Breakdown")

    for name, score in ai_decision["Breakdown"].items():
        print(f"  {name:<18}: {score:+d}")

    print("----------------------------------------")


def print_paper_portfolio(portfolio):

    print("----------------------------------------")
    print("       PAPER PORTFOLIO")
    print("----------------------------------------")

    print(f"Cash : {portfolio['Cash']:.2f}")

    positions = portfolio["Positions"]

    if positions:

        print()
        print(f"Open Positions ({len(positions)})")

        for symbol, position in positions.items():

            print(f"  {symbol}: Entry {position['Entry Price']:.2f}, "
                  f"SL {position['Stop Loss']:.2f}, Target {position['Target']:.2f}")

    else:

        print("Open Positions : None")

    closed = portfolio["Closed Trades"]

    print()
    print(f"Closed Trades : {len(closed)}")

    if closed:

        total_pnl = sum(t["PnL"] for t in closed)
        print(f"Total PnL     : {total_pnl:.2f}")

    print("----------------------------------------")


def print_validation_report(is_valid, errors, candle_count):

    print("----------------------------------------")
    print("       DATA VALIDATION REPORT")
    print("----------------------------------------")

    print(f"Status   : {'PASSED' if is_valid else 'FAILED'}")
    print(f"Candles  : {candle_count}")

    if is_valid:

        print("Data     : Available")
        print("Columns  : OK")
        print("NaN      : NOT FOUND")
        print("Duplicate: NOT FOUND")

    else:

        print("\nErrors")

        for error in errors:
            print(f"• {error}")

    print("----------------------------------------")


def print_support_resistance(levels):

    print("----------------------------------------")
    print("       SUPPORT / RESISTANCE REPORT")
    print("----------------------------------------")

    print(f"Current Price : {levels['Current Price']:.2f}")
    print(f"Resistance    : {levels['Resistance']:.2f}")
    print(f"Support       : {levels['Support']:.2f}")

    print()

    print(f"Distance To Resistance : {levels['Distance To Resistance']:.2f}")
    print(f"Distance To Support    : {levels['Distance To Support']:.2f}")

    print("----------------------------------------")


def print_volume_analysis(volume_analysis):

    print("----------------------------------------")
    print("       VOLUME REPORT")
    print("----------------------------------------")

    print(f"Current Volume : {volume_analysis['Current Volume']}")
    print(f"Average Volume : {volume_analysis['Average Volume']}")
    print(f"Volume Ratio   : {volume_analysis['Volume Ratio']}x")
    print(f"Spike          : {'YES' if volume_analysis['Spike'] else 'NO'}")

    print("----------------------------------------")


def print_candlestick_pattern(candle_pattern):

    print("----------------------------------------")
    print("       CANDLESTICK REPORT")
    print("----------------------------------------")

    print(f"Pattern : {candle_pattern['Pattern']}")
    print(f"Bias    : {candle_pattern['Bias']}")

    print("----------------------------------------")


def print_backtest_report(summary):

    print("----------------------------------------")
    print("       BACKTEST REPORT")
    print("----------------------------------------")

    print(f"Total Trades : {summary['Total Trades']}")
    print(f"Wins         : {summary['Wins']}")
    print(f"Losses       : {summary['Losses']}")
    print(f"Win Rate     : {summary['Win Rate']}%")

    print()

    print(f"Total PnL    : {summary['Total PnL']:.2f}")
    print(f"Max Drawdown : {summary['Max Drawdown']:.2f}")

    print("----------------------------------------")

    print("Exit Breakdown")

    for reason, count in summary["Exit Reasons"].items():
        print(f"  {reason} : {count}")

    print("----------------------------------------")


def print_filtered_signal(signal, filter_notes):

    print("----------------------------------------")
    print("       FILTERED SIGNAL")
    print("----------------------------------------")

    print(f"Signal : {signal}")

    if filter_notes:

        print()
        print("Filters Applied")

        for note in filter_notes:
            print(f"  - {note}")

    print("----------------------------------------")


def print_risk_levels(signal, stop_loss, target):

    print("----------------------------------------")
    print("       ATR RISK LEVELS")
    print("----------------------------------------")

    if stop_loss is None:

        print("No open-trade signal - nothing to size.")

    else:

        print(f"If {signal} now:")
        print(f"  Stop Loss : {stop_loss:.2f}")
        print(f"  Target    : {target:.2f}")

    print("----------------------------------------")


def print_market_structure(structure):

    trend = structure["Trend Analysis"]

    print("----------------------------------------")
    print("       MARKET STRUCTURE REPORT")
    print("----------------------------------------")

    print(f"Previous High : {trend['Previous High']:.2f}")
    print(f"Latest High   : {trend['Latest High']:.2f}")

    print()

    print(f"Previous Low  : {trend['Previous Low']:.2f}")
    print(f"Latest Low    : {trend['Latest Low']:.2f}")

    print("----------------------------------------")

    print(f"Higher High : {'YES' if trend['Higher High'] else 'NO'}")
    print(f"Higher Low  : {'YES' if trend['Higher Low'] else 'NO'}")
    print(f"Lower High  : {'YES' if trend['Lower High'] else 'NO'}")
    print(f"Lower Low   : {'YES' if trend['Lower Low'] else 'NO'}")

    print("----------------------------------------")

    print(f"Trend : {trend['Trend']}")

    print("----------------------------------------")