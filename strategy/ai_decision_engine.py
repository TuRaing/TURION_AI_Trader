def score_ema_trend(ema20, ema50):

    return 1 if ema20 > ema50 else -1


def score_rsi(rsi):

    if rsi > 60:
        return 1

    if rsi < 40:
        return -1

    return 0


def score_market_structure(trend):

    if "Bullish" in trend:
        return 1

    if "Bearish" in trend:
        return -1

    return 0


def score_levels(levels, buffer_pct=0.15):

    buffer = levels["Current Price"] * buffer_pct / 100

    if levels["Distance To Resistance"] <= buffer:
        return -1

    if levels["Distance To Support"] <= buffer:
        return 1

    return 0


def score_candlestick(candle_pattern):

    if candle_pattern["Bias"] == "Bullish":
        return 1

    if candle_pattern["Bias"] == "Bearish":
        return -1

    return 0


def get_ai_decision(ema20, ema50, rsi, structure_trend, levels, volume_analysis, candle_pattern, confidence_threshold=60):
    """
    Combine every existing engine (EMA/RSI trend, Market Structure,
    Support/Resistance, Candlestick, Volume) into one weighted
    confidence score, instead of a single indicator making the call.

    This is a rule-based weighted scorer, not a trained ML model -
    it is transparent (every point in the score is traceable to a
    reason) rather than a black box.

    Returns
    -------
    dict
    """

    breakdown = {
        "EMA Trend": score_ema_trend(ema20, ema50),
        "RSI": score_rsi(rsi),
        "Market Structure": score_market_structure(structure_trend),
        "Support/Resistance": score_levels(levels),
        "Candlestick": score_candlestick(candle_pattern)
    }

    total_score = sum(breakdown.values())
    max_score = len(breakdown)

    confidence = abs(total_score) / max_score * 100

    if volume_analysis["Spike"]:
        confidence = min(100, confidence + 10)

    if total_score > 0:
        bias = "Bullish"

    elif total_score < 0:
        bias = "Bearish"

    else:
        bias = "Neutral"

    if bias == "Bullish" and confidence >= confidence_threshold:
        decision = "BUY"

    elif bias == "Bearish" and confidence >= confidence_threshold:
        decision = "SELL"

    else:
        decision = "NO TRADE"

    return {
        "Decision": decision,
        "Bias": bias,
        "Confidence": round(confidence, 1),
        "Breakdown": breakdown
    }
