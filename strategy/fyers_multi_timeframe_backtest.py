import strategy.multi_timeframe_backtest as _mtf
from strategy.fyers_data import fyers_download

# Added 05-Aug-2026 - Fyers-sourced counterpart to strategy/
# multi_timeframe_backtest.py. That file's _download() is the ONLY
# yfinance-specific piece in ~500 lines of otherwise data-source-
# agnostic backtest logic - rather than duplicating the whole file
# just to swap that one function, this monkey-patches _download onto
# the already-imported module at import time. This is a deliberate,
# narrow RUNTIME rebind, not a file edit - safe because
# run_multi_timeframe_backtest() looks up _download via its own
# module's global namespace at call time, so reassigning it here
# redirects every internal call without touching multi_timeframe_
# backtest.py on disk at all.
#
# The actual point: Fyers' real multi-year history (confirmed 04-Aug -
# ~9y for 1-minute candles, ~20y for daily) replaces yfinance's ~60-day
# intraday ceiling that constrained nearly every backtest finding in
# this project to "one window, small sample" - callers can now pass
# trend_period/entry_period like "1y" or "2y" instead of being capped
# at "60d".


def _fyers_download(symbol, interval, period):
    return fyers_download(symbol, period=period, interval=interval)


_mtf._download = _fyers_download

run_multi_timeframe_backtest = _mtf.run_multi_timeframe_backtest
