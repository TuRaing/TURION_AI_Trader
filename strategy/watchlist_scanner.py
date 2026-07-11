import yfinance as yf

from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr

from strategy.signal_engine import generate_filtered_signal
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


def download_watchlist(symbols, period="6mo", interval="1d"):
    """
    Batch-download every symbol's OHLCV data in one call.

    Parameters
    ----------
    symbols : dict
        {display_name: yfinance_ticker}

    Returns
    -------
    dict {display_name: DataFrame or None}
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

    frames = {}

    for name, ticker in symbols.items():

        frame = _extract_symbol_frame(data, ticker, single_symbol)

        if frame is not None:
            frame = frame.dropna(how="all")

        frames[name] = frame

    return frames


def analyze_symbol(frame):
    """
    Run the full analysis pipeline (EMA/RSI, ATR, Market Structure,
    Support/Resistance, Volume, Candlestick, filtered Signal, AI Decision
    Engine) on one symbol's OHLCV frame.

    Returns
    -------
    dict
    """

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

    signal, filter_notes = generate_filtered_signal(
        ema20.iloc[-1],
        ema50.iloc[-1],
        rsi.iloc[-1],
        structure["Trend Analysis"]["Trend"],
        levels,
        volume_analysis,
        candle_pattern
    )

    ai_decision = get_ai_decision(
        ema20.iloc[-1],
        ema50.iloc[-1],
        rsi.iloc[-1],
        structure["Trend Analysis"]["Trend"],
        levels,
        volume_analysis,
        candle_pattern
    )

    return {
        "Price": round(float(close.iloc[-1]), 2),
        "ATR": round(float(atr.iloc[-1]), 2),
        "Signal": signal,
        "Filter Notes": filter_notes,
        "Decision": ai_decision["Decision"],
        "Bias": ai_decision["Bias"],
        "Confidence": ai_decision["Confidence"],
        "Candle Pattern": candle_pattern["Pattern"]
    }


def scan_watchlist(symbols, period="6mo", interval="1d"):
    """
    Analyze every symbol in the watchlist and rank the results by
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

    frames = download_watchlist(symbols, period, interval)

    results = []

    for name, ticker in symbols.items():

        try:

            frame = frames[name]

            if frame is None or len(frame) < MIN_CANDLES:
                continue

            analysis = analyze_symbol(frame)

            results.append({
                "Name": name,
                "Symbol": ticker,
                "Price": analysis["Price"],
                "Decision": analysis["Decision"],
                "Bias": analysis["Bias"],
                "Confidence": analysis["Confidence"],
                "ATR": analysis["ATR"],
                "Candle Pattern": analysis["Candle Pattern"]
            })

        except Exception as error:

            print(f"Skipped {name} ({ticker}): {error}")

    results.sort(key=lambda r: r["Confidence"], reverse=True)

    return results
