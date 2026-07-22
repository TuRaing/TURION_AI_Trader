import yfinance as yf
import pandas as pd

from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr
from strategy.risk_engine import calculate_atr_levels

# Updated: 2026-07-22 - Momentum (RSI) entry filtered by India VIX being in
# a "normal" band, researched 21-Jul as the candidate for Options Decision
# Engine's BUY CE/BUY PE logic. Analysis only - not wired into any paper
# trading or live automation.
#
# IMPORTANT CAVEAT: free option-chain history (real premiums) isn't
# available, so this backtests DIRECTIONAL ACCURACY on the underlying
# index only (NIFTY spot) - not real option P&L. A "win" here means the
# underlying moved far enough in the predicted direction to have been a
# profitable CE/PE buy in principle; it does not account for option
# premium, theta decay, or IV changes. Treat results as a signal-quality
# check, not a rupee backtest.

RSI_BULLISH = 60
RSI_BEARISH = 40
VIX_PERCENTILE_LOW = 0.20
VIX_PERCENTILE_HIGH = 0.80
VIX_LOOKBACK_CANDLES = 125  # ~5 trading days of 15m candles


def _flatten(series):

    if hasattr(series, "columns"):
        return series.iloc[:, 0]

    return series


def run_momentum_vix_backtest(
    symbol="^NSEI",
    vix_symbol="^INDIAVIX",
    period="60d",
    interval="15m",
    atr_sl_mult=1.0,
    atr_target_mult=2.0,
    vix_percentile_low=VIX_PERCENTILE_LOW,
    vix_percentile_high=VIX_PERCENTILE_HIGH,
):
    """
    Backtests a Momentum(RSI)+India VIX-filtered directional signal -
    BUY CE when RSI crosses above 60 with India VIX inside its own recent
    [20th, 80th] percentile band (not the deadest or the most panicked
    conditions), BUY PE on the mirror-image RSI<40 condition.

    See the module docstring above - this measures directional accuracy
    on the underlying only, not real option premium P&L.

    Returns
    -------
    dict, or {"Error": str} if either symbol has no usable data.
    """

    price_data = yf.download(symbol, period=period, interval=interval, progress=False)
    vix_data = yf.download(vix_symbol, period=period, interval=interval, progress=False)

    if price_data.empty:
        return {"Error": f"No usable {interval} data for {symbol}"}

    if vix_data.empty:
        return {"Error": f"No usable {interval} data for {vix_symbol}"}

    return _run_on_data(
        price_data, vix_data, atr_sl_mult, atr_target_mult,
        vix_percentile_low, vix_percentile_high,
    )


def _run_on_data(price_data, vix_data, atr_sl_mult, atr_target_mult, vix_percentile_low, vix_percentile_high):
    """
    Core backtest loop, split out from run_momentum_vix_backtest() so a
    tuning sweep can download each symbol's data once and re-run this
    against many parameter combinations instead of re-fetching per combo.
    """

    close = _flatten(price_data["Close"])
    high = _flatten(price_data["High"])
    low = _flatten(price_data["Low"])

    rsi = calculate_rsi(price_data)
    atr = calculate_atr(price_data)

    vix_close = _flatten(vix_data["Close"])
    vix_low_band = vix_close.rolling(VIX_LOOKBACK_CANDLES).quantile(vix_percentile_low)
    vix_high_band = vix_close.rolling(VIX_LOOKBACK_CANDLES).quantile(vix_percentile_high)

    # As-of join: for each NIFTY candle, the most recently completed India
    # VIX reading at or before it - no look-ahead.
    merged = pd.merge_asof(
        pd.DataFrame({"Close": close, "High": high, "Low": low, "RSI": rsi}).reset_index(),
        pd.DataFrame({"VIX": vix_close, "VIX Low Band": vix_low_band, "VIX High Band": vix_high_band}).reset_index(),
        on=price_data.index.name or "Datetime",
        direction="backward",
    ).set_index(price_data.index.name or "Datetime")

    trades = []
    position = None

    for timestamp, row in merged.iterrows():

        if pd.isna(row["RSI"]) or pd.isna(row["VIX"]) or pd.isna(row["VIX Low Band"]):
            continue

        price = float(row["Close"])

        if position is not None:

            if position["Direction"] == "BUY":

                if float(row["Low"]) <= position["Stop Loss"]:
                    trades.append(_close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                    continue

                if float(row["High"]) >= position["Target"]:
                    trades.append(_close_trade(position, timestamp, position["Target"], "Target"))
                    position = None
                    continue

            else:

                if float(row["High"]) >= position["Stop Loss"]:
                    trades.append(_close_trade(position, timestamp, position["Stop Loss"], "Stop Loss"))
                    position = None
                    continue

                if float(row["Low"]) <= position["Target"]:
                    trades.append(_close_trade(position, timestamp, position["Target"], "Target"))
                    position = None
                    continue

        if position is not None:
            continue

        vix_in_band = row["VIX Low Band"] <= row["VIX"] <= row["VIX High Band"]

        if not vix_in_band:
            continue

        direction = None

        if row["RSI"] > RSI_BULLISH:
            direction = "BUY"
        elif row["RSI"] < RSI_BEARISH:
            direction = "SELL"

        if direction is not None and pd.notna(atr.loc[timestamp]):

            stop_loss, target = calculate_atr_levels(
                price, float(atr.loc[timestamp]), direction,
                sl_mult=atr_sl_mult, target_mult=atr_target_mult,
            )

            position = {
                "Direction": direction,
                "Option": "CE" if direction == "BUY" else "PE",
                "Entry Time": timestamp,
                "Entry Price": price,
                "Stop Loss": stop_loss,
                "Target": target,
            }

    if position is not None:
        last_timestamp = merged.index[-1]
        trades.append(_close_trade(position, last_timestamp, float(close.iloc[-1]), "End Of Data"))

    return _summarize(trades)


def _close_trade(position, exit_time, exit_price, reason):

    if position["Direction"] == "BUY":
        points = exit_price - position["Entry Price"]
    else:
        points = position["Entry Price"] - exit_price

    return {
        "Option": position["Option"],
        "Entry Time": position["Entry Time"],
        "Entry Price": position["Entry Price"],
        "Exit Time": exit_time,
        "Exit Price": exit_price,
        "Exit Reason": reason,
        "Underlying Points": round(points, 2),
    }


def _summarize(trades):

    total_trades = len(trades)
    wins = [t for t in trades if t["Underlying Points"] > 0]

    total_points = sum(t["Underlying Points"] for t in trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades else 0

    exit_reasons = {}
    for t in trades:
        exit_reasons[t["Exit Reason"]] = exit_reasons.get(t["Exit Reason"], 0) + 1

    ce_trades = [t for t in trades if t["Option"] == "CE"]
    pe_trades = [t for t in trades if t["Option"] == "PE"]

    return {
        "Total Trades": total_trades,
        "CE Trades": len(ce_trades),
        "PE Trades": len(pe_trades),
        "Wins (Directional)": len(wins),
        "Win Rate (Directional)": round(win_rate, 2),
        "Total Underlying Points": round(total_points, 2),
        "Exit Reasons": exit_reasons,
        "Trades": trades,
    }
