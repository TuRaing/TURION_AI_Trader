def generate_reason(ema20, ema50, rsi):

    reasons = []

    # Trend

    if ema20 > ema50:
        reasons.append("✅ EMA20 > EMA50 : Bullish Trend")

    else:
        reasons.append("❌ EMA20 < EMA50 : Bearish Trend")

    # RSI

    if rsi > 60:
        reasons.append("✅ RSI > 60 : Strong Momentum")

    elif rsi < 40:
        reasons.append("⚠️ RSI < 40 : Weak Momentum")

    else:
        reasons.append("➖ RSI Neutral")

    # Final Decision Reason

    if ema20 > ema50 and rsi > 60:

        decision = "BUY"

        explanation = "Trend and Momentum both are Bullish."

    elif ema20 < ema50 and rsi < 40:

        decision = "SELL"

        explanation = "Trend and Momentum both are Bearish."

    else:

        decision = "NO TRADE"

        explanation = "Indicators are conflicting. Wait for confirmation."

    return decision, explanation, reasons