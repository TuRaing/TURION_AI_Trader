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