import yfinance as yf
import pandas as pd

from indicators.atr import calculate_atr
from strategy.orb_vwap_backtest import _flatten, close_trade, summarize_trades

# Updated: 2026-07-25 - Gap-fill: bet that a significant open-vs-previous-
# close gap reverts back toward the previous close during the day, the
# opposite thesis to Gap-and-Go (which bets the gap continues). Explicitly
# not pursued earlier (see PROJECT_STATUS.md) since Gap-and-Go was assumed
# to have more opportunities - tested now to check that assumption rather
# than leave it unverified. Analysis only, same pattern as this codebase's
# other *_backtest.py scripts.

ATR_PERIOD = 14
GAP_THRESHOLD_PCT = 0.3  # minimum |gap| %, below this a gap is treated as noise


def run_gap_fill_backtest(
    symbol="^NSEI",
    period="60d",
    start=None,
    end=None,
    interval="5m",
    gap_threshold_pct=GAP_THRESHOLD_PCT,
    atr_sl_mult=1.0,
):
    """
    Backtests a Gap-fill entry: at the first candle of each trading day,
    compare that candle's Open to the previous *calendar* day's Close
    (from daily data, so it reflects the real overnight/weekend gap, not
    just a gap between consecutive intraday candles). If the gap is at
    least gap_threshold_pct in either direction, enter betting it fills
    back to the previous close:
    - Gap up (Open > previous Close) -> SELL, Target = previous Close.
    - Gap down (Open < previous Close) -> BUY, Target = previous Close.
    Stop-Loss is ATR-based (same calculate_atr_levels pattern used
    elsewhere), placed on the side away from the target - i.e. betting
    the gap widens further, not fills. At most one entry per day, taken
    on the day's first candle only. Any position still open at day-end
    is force-closed there ("Day End Square-Off") - intraday only, same
    convention as strategy/orb_vwap_backtest.py.

    No look-ahead: the gap uses only the previous day's already-closed
    daily candle and the current day's first candle's own Open.

    start / end : str or None
        Explicit date range (passed to yfinance) for splitting Yahoo's
        one available ~60-day 5m window into independent sub-periods -
        e.g. to sanity-check whether a result holds in both halves of
        the window rather than being concentrated in one lucky stretch.
        Yahoo has no 5m history before ~60 days ago regardless of these
        values, so this cannot reach further back than `period` already
        does - it only re-slices the same available window. When set,
        overrides `period` for the intraday download; the daily download
        (needed for the previous-close gap reference) starts 10 calendar
        days earlier than `start` so the very first day in range still
        has a real previous close to compare against.

    Returns
    -------
    dict (see strategy.orb_vwap_backtest.summarize_trades), or
    {"Error": str} if no usable data.
    """

    if start is not None:
        data = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
    else:
        data = yf.download(symbol, period=period, interval=interval, progress=False)

    if data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    if start is not None:
        daily_start = (pd.Timestamp(start) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
        daily = yf.download(symbol, start=daily_start, end=end, interval="1d", progress=False)
    else:
        daily = yf.download(symbol, period=period, interval="1d", progress=False)

    if daily.empty:
        return {"Error": f"No usable daily data for {symbol} (needed for the gap reference)"}

    daily_close = _flatten(daily["Close"])
    prev_close_by_date = {ts.date(): float(c) for ts, c in daily_close.shift(1).dropna().items()}

    close = _flatten(data["Close"])
    open_ = _flatten(data["Open"])
    high = _flatten(data["High"])
    low = _flatten(data["Low"])

    atr = calculate_atr(data, period=ATR_PERIOD)

    day = pd.Series(data.index.date, index=data.index)

    trades = []

    for trading_day, day_index in data.groupby(day).groups.items():

        day_index = data.index[data.index.isin(day_index)]

        prev_close = prev_close_by_date.get(trading_day)

        if prev_close is None or len(day_index) == 0:
            continue

        first_timestamp = day_index[0]
        open_price = float(open_.loc[first_timestamp])
        atr_now = atr.loc[first_timestamp]

        if pd.isna(atr_now) or prev_close == 0:
            continue

        gap_pct = (open_price - prev_close) / prev_close * 100

        if abs(gap_pct) < gap_threshold_pct:
            continue

        if gap_pct > 0:
            direction = "SELL"
            stop_loss = open_price + float(atr_now) * atr_sl_mult
        else:
            direction = "BUY"
            stop_loss = open_price - float(atr_now) * atr_sl_mult

        position = {
            "Direction": direction,
            "Entry Time": first_timestamp,
            "Entry Price": open_price,
            "Stop Loss": stop_loss,
            "Target": prev_close,
        }

        for i, timestamp in enumerate(day_index):

            is_last_of_day = (i == len(day_index) - 1)
            bar_high = float(high.loc[timestamp])
            bar_low = float(low.loc[timestamp])

            if timestamp == first_timestamp:
                # The entry candle itself can't also be checked for exit -
                # nothing has happened yet at the moment of entry.
                if is_last_of_day:
                    trades.append(close_trade(position, timestamp, float(close.loc[timestamp]), "Day End Square-Off"))
                    position = None
                continue

            if position["Direction"] == "BUY":

                if bar_low <= position["Stop Loss"]:
                    trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                    break
                elif bar_high >= position["Target"]:
                    trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                    position = None
                    break

            else:

                if bar_high >= position["Stop Loss"]:
                    trades.append(close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                    break
                elif bar_low <= position["Target"]:
                    trades.append(close_trade(position, timestamp, position["Target"], "Target"))
                    position = None
                    break

            if is_last_of_day:
                trades.append(close_trade(position, timestamp, float(close.loc[timestamp]), "Day End Square-Off"))
                position = None

    return summarize_trades(trades)
