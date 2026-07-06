def get_market_state(price, ema20, ema50):

    """
    Determine Market State

    Returns:
        state
        action
        reason
    """

    # Strong Bullish
    if price > ema20 and ema20 > ema50:
        return (
            "🟢 Bullish",
            "LOOK FOR BUY",
            "Price is above EMA20 and EMA20 is above EMA50."
        )

    # Strong Bearish
    elif price < ema20 and ema20 < ema50:
        return (
            "🔴 Bearish",
            "LOOK FOR SELL / PUT",
            "Price is below EMA20 and EMA20 is below EMA50."
        )

    # Sideways
    else:
        return (
            "🟡 Sideways",
            "NO TRADE",
            "Market has no clear trend."
        )