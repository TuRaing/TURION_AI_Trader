def calculate_atr_levels(price, atr_value, direction, sl_mult=1.5, target_mult=3.0):
    """
    Calculate ATR-based Stop-Loss and Target for a trade direction.

    Parameters
    ----------
    price : float
    atr_value : float
    direction : str
        "BUY" or "SELL"
    sl_mult : float
    target_mult : float

    Returns
    -------
    stop_loss : float
    target : float
    """

    if direction == "BUY":

        stop_loss = price - (atr_value * sl_mult)
        target = price + (atr_value * target_mult)

    else:

        stop_loss = price + (atr_value * sl_mult)
        target = price - (atr_value * target_mult)

    return stop_loss, target
