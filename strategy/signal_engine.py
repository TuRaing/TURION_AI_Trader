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


def apply_market_structure_filter(signal, trend):
    """
    Block a signal that disagrees with the broader market structure trend
    (eg. a BUY while structure is still Bearish/Sideways).

    Returns
    -------
    signal : str
    note : str or None
    """

    if signal == "BUY" and "Bullish" not in trend:
        return "NO TRADE", f"Blocked BUY: Market Structure is not Bullish ({trend})"

    if signal == "SELL" and "Bearish" not in trend:
        return "NO TRADE", f"Blocked SELL: Market Structure is not Bearish ({trend})"

    return signal, None


def apply_support_resistance_filter(signal, levels, buffer_pct=0.1):
    """
    Block a BUY too close to Resistance, or a SELL too close to Support,
    where a bounce/rejection is more likely than a breakout.

    Returns
    -------
    signal : str
    note : str or None
    """

    buffer = levels["Current Price"] * buffer_pct / 100

    if signal == "BUY" and levels["Distance To Resistance"] <= buffer:
        return "NO TRADE", f"Blocked BUY: Price too close to Resistance ({levels['Resistance']})"

    if signal == "SELL" and levels["Distance To Support"] <= buffer:
        return "NO TRADE", f"Blocked SELL: Price too close to Support ({levels['Support']})"

    return signal, None


def apply_volume_filter(signal, volume_analysis, min_ratio=0.5):
    """
    Block a BUY/SELL that isn't backed by at least half the recent
    average volume, where a move is more likely to be noise.

    Returns
    -------
    signal : str
    note : str or None
    """

    # Updated: 2026-07-11 - index tickers like ^NSEI report zero Volume on
    # Yahoo Finance, so there is no reliable average to compare against;
    # skip the filter instead of blocking every trade
    if volume_analysis["Average Volume"] == 0:
        return signal, None

    if signal in ("BUY", "SELL") and volume_analysis["Volume Ratio"] < min_ratio:
        return "NO TRADE", f"Blocked {signal}: Volume too low ({volume_analysis['Volume Ratio']}x average)"

    return signal, None


def generate_filtered_signal(ema20, ema50, rsi, market_structure_trend, levels, volume_analysis):
    """
    Generate a Trading Signal, then filter it through Market Structure,
    Support/Resistance and Volume so it does not trade against structure,
    straight into a level, or on unconfirmed low-volume moves.

    Returns
    -------
    signal : str
    filter_notes : list of str
    """

    signal = generate_signal(ema20, ema50, rsi)
    filter_notes = []

    signal, note = apply_market_structure_filter(signal, market_structure_trend)

    if note:
        filter_notes.append(note)

    signal, note = apply_support_resistance_filter(signal, levels)

    if note:
        filter_notes.append(note)

    signal, note = apply_volume_filter(signal, volume_analysis)

    if note:
        filter_notes.append(note)

    return signal, filter_notes