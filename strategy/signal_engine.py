def generate_signal(ema20, ema50, rsi):
    """
    Generate Trading Signal

    Parameters
    ----------
    ema20 : float
    ema50 : float
    rsi : float

    Returns
    -------
    BUY / SELL / NO TRADE
    """

    if ema20 > ema50 and rsi > 60:
        return "BUY"

    elif ema20 < ema50 and rsi < 40:
        return "SELL"

    else:
        return "NO TRADE"