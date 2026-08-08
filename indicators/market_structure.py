# Added 08-Aug-2026 - ICT/Smart Money Concepts building blocks, requested
# by the user after evaluating a ChatGPT-sourced strategy list (see
# strategy/ict_smc_backtest.py for the full entry rule that wires these
# together and the honest verdict against this project's own past
# research). Deliberately scoped to the 4 concepts the user actually
# named - swing-point Liquidity, Break of Structure (BOS), Change of
# Character (CHOCH), Order Blocks, and Fair Value Gaps (FVG) - NOT the
# full ICT framework (no kill zones, premium/discount arrays, dealing
# ranges, etc.) - those are real ICT concepts but weren't asked for and
# would be scope creep here.
#
# Every function is pure (plain list/array in, plain data out) so each
# piece is independently testable without needing real market data or a
# running backtest - same convention as this project's other strategy-
# logic pure functions (e.g. fyers_options_gapfill.py's _target_hit).


def find_swing_points(high, low, lookback=2):
    """
    Fractal swing high/low detection: candle i is a swing high if its High
    is the strict max within [i-lookback, i+lookback], a swing low if its
    Low is the strict min in the same window. This IS the "Liquidity"
    concept in ICT terms - these are the levels where stops/orders cluster,
    and where BOS/CHOCH breaks are measured against.

    A swing at index i can only be confirmed once `lookback` candles AFTER
    it have closed - callers walking forward candle-by-candle (as strategy/
    ict_smc_backtest.py does) must only trust swings whose index <=
    current_index - lookback, or they leak future information.

    Parameters
    ----------
    high, low : sequences of float (same length)
    lookback : int - candles required on EACH side to confirm a swing

    Returns
    -------
    list of dict, chronological: {"index": int, "price": float, "type": "high"/"low"}
    """

    n = len(high)
    swings = []

    for i in range(lookback, n - lookback):

        window_high = high[i - lookback:i + lookback + 1]
        window_low = low[i - lookback:i + lookback + 1]

        if high[i] == max(window_high):
            swings.append({"index": i, "price": high[i], "type": "high"})

        if low[i] == min(window_low):
            swings.append({"index": i, "price": low[i], "type": "low"})

    return swings


class MarketStructureTracker:
    """
    Stateful BOS/CHOCH classifier - fed confirmed swings and candle closes
    in chronological order, tracks the current trend bias and classifies
    each structural break.

    - BOS (Break of Structure): a close breaks the most recent swing in
      the direction the trend is ALREADY in - confirms trend continuation.
    - CHOCH (Change of Character): a close breaks the most recent swing
      AGAINST the current trend - the first sign of a possible reversal.
      Flips the tracked trend on the spot (ICT convention: CHOCH IS the
      new trend's first confirmation, not just a warning).

    Trend starts as None (unknown) until the first two opposite-direction
    swings establish an initial higher-high/higher-low (up) or lower-high/
    lower-low (down) sequence.
    """

    def __init__(self):
        self.trend = None
        self.last_swing_high = None
        self.last_swing_low = None
        self.prior_swing_high = None
        self.prior_swing_low = None

    def add_swing(self, swing_type, price):
        """Records a newly-confirmed swing, updating trend bias from the
        HH/HL vs LH/LL sequence once enough swings exist."""

        if swing_type == "high":

            if self.last_swing_high is not None:

                if self.trend is None:
                    self.trend = "up" if price > self.last_swing_high else "down"

            self.prior_swing_high = self.last_swing_high
            self.last_swing_high = price

        else:

            if self.last_swing_low is not None:

                if self.trend is None:
                    self.trend = "up" if price > self.last_swing_low else "down"

            self.prior_swing_low = self.last_swing_low
            self.last_swing_low = price

    def check_break(self, close_price):
        """
        Given a bar's close, checks it against the last confirmed swing
        high/low. Returns "BOS", "CHOCH", or None. On a CHOCH, flips
        self.trend to the new direction immediately.
        """

        if self.last_swing_high is not None and close_price > self.last_swing_high:

            if self.trend == "up":
                return "BOS"

            self.trend = "up"
            return "CHOCH"

        if self.last_swing_low is not None and close_price < self.last_swing_low:

            if self.trend == "down":
                return "BOS"

            self.trend = "down"
            return "CHOCH"

        return None


def detect_order_block(open_, close, direction, breakout_index):
    """
    The last candle AGAINST the breakout direction, immediately before the
    breakout candle - the ICT "Order Block": the last down-close candle
    before an up-move (bullish OB), or last up-close candle before a
    down-move (bearish OB). Returns None if the immediately-preceding
    candle doesn't actually oppose the breakout direction (no valid OB).

    Parameters
    ----------
    open_, close : sequences of float
    direction : "up" or "down" - the breakout's direction
    breakout_index : int - index of the candle that caused the BOS/CHOCH

    Returns
    -------
    dict {"index", "high_ref", "low_ref"} using the OB candle's own
    open/close as its zone edges, or None
    """

    ob_index = breakout_index - 1

    if ob_index < 0:
        return None

    ob_open = open_[ob_index]
    ob_close = close[ob_index]

    if direction == "up" and ob_close < ob_open:
        return {"index": ob_index, "high_ref": ob_open, "low_ref": ob_close}

    if direction == "down" and ob_close > ob_open:
        return {"index": ob_index, "high_ref": ob_close, "low_ref": ob_open}

    return None


def detect_fair_value_gap(high, low, index):
    """
    3-candle imbalance centered on `index` (the middle/impulsive candle):
    bullish FVG when candle[index-1].high < candle[index+1].low (a real
    price gap the market skipped over), bearish FVG when candle[index-1]
    .low > candle[index+1].high. Needs index-1 and index+1 to exist.

    Returns
    -------
    dict {"direction": "up"/"down", "top": float, "bottom": float} or None
    """

    if index - 1 < 0 or index + 1 >= len(high):
        return None

    left_high = high[index - 1]
    left_low = low[index - 1]
    right_high = high[index + 1]
    right_low = low[index + 1]

    if left_high < right_low:
        return {"direction": "up", "top": right_low, "bottom": left_high}

    if left_low > right_high:
        return {"direction": "down", "top": left_low, "bottom": right_high}

    return None
