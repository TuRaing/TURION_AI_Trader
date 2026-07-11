import yfinance as yf

from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr

from strategy.market_structure import get_market_structure
from strategy.support_resistance import get_support_resistance
from strategy.volume_engine import get_volume_analysis
from strategy.candlestick_engine import get_candlestick_pattern
from strategy.ai_decision_engine import get_ai_decision

MIN_CANDLES = 60


def _extract_symbol_frame(data, symbol, single_symbol):
    """
    yfinance returns a flat frame for a single symbol, and a MultiIndex
    (per-symbol) frame when multiple tickers are batch-downloaded together.
    """

    if single_symbol:
        return data

    if symbol not in data.columns.get_level_values(0):
        return None

    return data[symbol]


def scan_watchlist(symbols, period="6mo", interval="1d"):
    """
    Run the full analysis pipeline (EMA/RSI, ATR, Market Structure,
    Support/Resistance, Volume, Candlestick, AI Decision Engine) across
    every symbol in one batched download, and rank the results by
    AI Decision confidence.

    Parameters
    ----------
    symbols : dict
        {display_name: yfinance_ticker}
    period : str
    interval : str

    Returns
    -------
    list of dict, sorted by Confidence descending
    """

    tickers = list(symbols.values())
    single_symbol = len(tickers) == 1

    data = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        threads=True,
        progress=False
    )

    results = []

    for name, ticker in symbols.items():

        try:

            frame = _extract_symbol_frame(data, ticker, single_symbol)

            if frame is None:
                continue

            frame = frame.dropna(how="all")

            if len(frame) < MIN_CANDLES:
                continue

            close = frame["Close"]

            if hasattr(close, "columns"):
                close = close.iloc[:, 0]

            ema20 = calculate_ema(frame, 20)
            ema50 = calculate_ema(frame, 50)
            rsi = calculate_rsi(frame)
            atr = calculate_atr(frame)

            structure = get_market_structure(frame)
            levels = get_support_resistance(frame)
            volume_analysis = get_volume_analysis(frame)
            candle_pattern = get_candlestick_pattern(frame)

            ai_decision = get_ai_decision(
                ema20.iloc[-1],
                ema50.iloc[-1],
                rsi.iloc[-1],
                structure["Trend Analysis"]["Trend"],
                levels,
                volume_analysis,
                candle_pattern
            )

            results.append({
                "Name": name,
                "Symbol": ticker,
                "Price": round(float(close.iloc[-1]), 2),
                "Decision": ai_decision["Decision"],
                "Bias": ai_decision["Bias"],
                "Confidence": ai_decision["Confidence"],
                "ATR": round(float(atr.iloc[-1]), 2),
                "Candle Pattern": candle_pattern["Pattern"]
            })

        except Exception as error:

            print(f"Skipped {name} ({ticker}): {error}")

    results.sort(key=lambda r: r["Confidence"], reverse=True)

    return results
