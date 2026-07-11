import sys

# Updated: 2026-07-11 - force UTF-8 stdout so emoji in reports don't crash on Windows' default cp1252 console
sys.stdout.reconfigure(encoding="utf-8")

import yfinance as yf
import matplotlib.pyplot as plt

from indicators.ema import calculate_ema

from indicators.rsi import calculate_rsi

from indicators.atr import calculate_atr

from strategy.signal_engine import generate_filtered_signal

from strategy.risk_engine import calculate_atr_levels

from strategy.reasoning_engine import generate_reason

from strategy.market_state import get_market_state

from strategy.data_validator import validate_market_data

from strategy.market_structure import get_market_structure

from strategy.support_resistance import get_support_resistance

from strategy.volume_engine import get_volume_analysis

from strategy.report_engine import (
    print_validation_report,
    print_market_structure,
    print_support_resistance,
    print_filtered_signal,
    print_risk_levels,
    print_volume_analysis
)

from report.excel_report import save_market_summary

print("Downloading NIFTY Data...")

# Download NIFTY Data
nifty = yf.download("^NSEI", period="5d", interval="15m")

# Validate Market Data

is_valid, errors = validate_market_data(nifty)

if not is_valid:

    print("\nDATA VALIDATION FAILED")

    for error in errors:
        print("-", error)

    exit()

print_validation_report(
    is_valid,
    errors,
    len(nifty)
)

# Close Price
close = nifty["Close"]

# Support new yfinance versions
if hasattr(close, "columns"):
    close = close.iloc[:, 0]

# EMA
ema20 = calculate_ema(nifty, 20)
ema50 = calculate_ema(nifty, 50)

#RSI
rsi = calculate_rsi(nifty)

# ATR
atr = calculate_atr(nifty)

price = close.iloc[-1]

market_state, action, reason = get_market_state(
    price,
    ema20.iloc[-1],
    ema50.iloc[-1]
)

structure = get_market_structure(nifty)

levels = get_support_resistance(nifty)

volume_analysis = get_volume_analysis(nifty)

signal, filter_notes = generate_filtered_signal(
    ema20.iloc[-1],
    ema50.iloc[-1],
    rsi.iloc[-1],
    structure["Trend Analysis"]["Trend"],
    levels,
    volume_analysis
)

decision, explanation, reasons = generate_reason(
    ema20.iloc[-1],
    ema50.iloc[-1],
    rsi.iloc[-1]
)

print("\nLatest RSI :", round(rsi.iloc[-1], 2))
# Chart
plt.figure(figsize=(14, 6))

plt.plot(close, label="Close Price", linewidth=2)
plt.plot(ema20, label="EMA 20")
plt.plot(ema50, label="EMA 50")

plt.title("NIFTY 50 with EMA")
plt.xlabel("Time")
plt.ylabel("Price")

plt.legend()
plt.grid(True)

print("\n========================================")
print("          TURION AI TRADER")
print("========================================")

print(f"Current Price : {price:.2f}")
print(f"EMA20         : {ema20.iloc[-1]:.2f}")
print(f"EMA50         : {ema50.iloc[-1]:.2f}")
print(f"RSI           : {rsi.iloc[-1]:.2f}")
print(f"ATR14         : {atr.iloc[-1]:.2f}")

print("----------------------------------------")

print(f"Market State  : {market_state}")

print(f"Action        : {action}")

print("----------------------------------------")

print("----------------------------------------")

print_market_structure(structure)

print_support_resistance(levels)

print_volume_analysis(volume_analysis)

print_filtered_signal(signal, filter_notes)

if signal in ("BUY", "SELL"):

    stop_loss, target = calculate_atr_levels(price, atr.iloc[-1], signal)

else:

    stop_loss, target = None, None

print_risk_levels(signal, stop_loss, target)

print("Reason")

print(reason)

save_market_summary(

    symbol="NIFTY",

    timeframe="15m",

    price=price,

    ema20=ema20.iloc[-1],

    ema50=ema50.iloc[-1],

    rsi=rsi.iloc[-1],

    market_state=market_state,

    market_structure=structure["Trend Analysis"]["Trend"],

    action=action,

    support=levels["Support"],

    resistance=levels["Resistance"],

    atr=atr.iloc[-1],

    volume_ratio=volume_analysis["Volume Ratio"]

)

print("========================================")

plt.show()


