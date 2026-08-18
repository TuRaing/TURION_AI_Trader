import datetime

import pandas as pd

from indicators.rsi import calculate_rsi
from strategy.backtest_live_engine import run_live_check

# Added 17-Aug-2026 - task #17 of the WebSocket code-prep (see strategy/
# event_driven_engine.py's module docstring for the full plan/context).
# This is the piece that turns a real-time tick stream into the
# data_point shape event_driven_engine.py's decide_fn expects - LOCAL
# test harness only, no VPS, no real WebSocket connection tested yet
# (see the CandleAggregator/LiveTickRunner split below for exactly
# which parts are and aren't verified).
#
# SPLIT BY DESIGN, so the untestable part stays as small as possible:
#   - CandleAggregator + LiveTickRunner: pure, no network - builds 5m
#     candles from ticks and RSI from those candles (reusing indicators/
#     rsi.py's calculate_rsi() unchanged, same function every existing
#     strategy already relies on), assembles data_points, calls decide_
#     fn via run_live_check(). Fully unit-tested with synthetic ticks.
#   - connect_and_run(): the actual fyers_apiv3 FyersDataSocket wiring.
#     Written to match the REAL, verified SDK pattern (see PROJECT_
#     STATUS.md's 17-Aug WebSocket-research entry for sources) but
#     COULD NOT be live-tested before committing - local session's
#     Fyers token is expired AND Fyers' own daily API quota was
#     exhausted today (same blocker as the depth collector's own
#     caveat). Treat the first real run as a verification run.

CANDLE_INTERVAL_MINUTES = 5
MIN_CANDLES_FOR_RSI = 15  # RSI(14) needs 14 diffs = 15 closes minimum


class CandleAggregator:
    """
    Builds rolling 5-minute OHLC candles from a live tick stream (one
    on_tick(timestamp, price) call per tick), and computes RSI(14) on
    the resulting candle series using the EXACT SAME calculate_rsi()
    every polling-based strategy in this project already uses on
    fyers_download's 5m candles - so a live RSI reading here means the
    same thing as the original engine's RSI reading, not a re-derived
    approximation.

    Seed with real historical candles (e.g. from fyers_download(...,
    interval="5m")) via `initial_candles` so RSI is available from the
    first live tick instead of needing ~70 minutes of live ticks to
    warm up 15 candles from scratch.
    """

    def __init__(self, initial_candles=None):

        self.candles = (
            initial_candles.copy() if initial_candles is not None
            else pd.DataFrame(columns=["Open", "High", "Low", "Close"])
        )
        self._bucket_start = None
        self._bucket = None

    @staticmethod
    def _floor_to_bucket(timestamp):

        minute = (timestamp.minute // CANDLE_INTERVAL_MINUTES) * CANDLE_INTERVAL_MINUTES

        return timestamp.replace(minute=minute, second=0, microsecond=0)

    def on_tick(self, timestamp, price):

        bucket_start = self._floor_to_bucket(timestamp)

        if self._bucket_start is None:
            self._bucket_start = bucket_start
            self._bucket = {"Open": price, "High": price, "Low": price, "Close": price}
            return

        if bucket_start == self._bucket_start:
            self._bucket["High"] = max(self._bucket["High"], price)
            self._bucket["Low"] = min(self._bucket["Low"], price)
            self._bucket["Close"] = price
            return

        self._close_bucket()
        self._bucket_start = bucket_start
        self._bucket = {"Open": price, "High": price, "Low": price, "Close": price}

    def _close_bucket(self):

        row = pd.DataFrame([self._bucket], index=[self._bucket_start])
        self.candles = pd.concat([self.candles, row]).tail(200)

    def current_rsi(self):
        """
        RSI over closed candles only (the current, still-forming bucket
        is deliberately excluded - matches the original engine reading
        RSI off completed 5m candles, not a partial one).
        """

        if len(self.candles) < MIN_CANDLES_FOR_RSI:
            return None

        rsi_series = calculate_rsi(self.candles)
        latest = rsi_series.iloc[-1]

        return float(latest) if pd.notna(latest) else None


class LiveTickRunner:
    """
    Owns one strategy's live decide_fn loop. Feed it every tick for the
    symbols it cares about (underlying spot, ATM CE, ATM PE) via
    on_tick(); it maintains the latest known state, and once enough
    state exists to build a full data_point, calls decide_fn through
    run_live_check() - the SAME function a batch backtest replay uses
    (see event_driven_engine.py / backtest_live_engine.py), so there is
    no second copy of the decision logic here, only state-assembly.
    """

    def __init__(self, decide_fn, cfg, portfolio, underlying_symbol, ce_symbol, pe_symbol,
                 squareoff_time, initial_candles=None):

        self.decide_fn = decide_fn
        self.cfg = cfg
        self.portfolio = portfolio
        self.underlying_symbol = underlying_symbol
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol
        self.squareoff_time = squareoff_time
        self.aggregator = CandleAggregator(initial_candles)

        self._latest = {"spot": None, "ce_ltp": None, "ce_bid": None, "ce_ask": None,
                         "pe_ltp": None, "pe_bid": None, "pe_ask": None}
        self.last_action = None

    def _past_squareoff(self, timestamp):

        return (timestamp.hour, timestamp.minute) >= self.squareoff_time

    def on_tick(self, symbol, timestamp, ltp, bid=None, ask=None):
        """
        Call once per incoming WebSocket SymbolUpdate message. Updates
        internal state; if this tick carries enough NEW information to
        act on (underlying tick -> RSI/spot changed; CE/PE tick -> that
        leg's price changed), calls decide_fn once via run_live_check().
        Ticks for symbols this runner doesn't track are ignored.

        Returns the action string if decide_fn ran this call, else None.
        """

        if symbol == self.underlying_symbol:
            self.aggregator.on_tick(timestamp, ltp)
            self._latest["spot"] = ltp
        elif symbol == self.ce_symbol:
            self._latest["ce_ltp"] = ltp
            self._latest["ce_bid"] = bid
            self._latest["ce_ask"] = ask
        elif symbol == self.pe_symbol:
            self._latest["pe_ltp"] = ltp
            self._latest["pe_bid"] = bid
            self._latest["pe_ask"] = ask
        else:
            return None

        if self._latest["spot"] is None:
            return None  # no RSI/spot context yet

        data_point = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "spot": self._latest["spot"],
            "rsi": self.aggregator.current_rsi(),
            "ce_symbol": self.ce_symbol, "ce_ltp": self._latest["ce_ltp"],
            "ce_bid": self._latest["ce_bid"], "ce_ask": self._latest["ce_ask"],
            "pe_symbol": self.pe_symbol, "pe_ltp": self._latest["pe_ltp"],
            "pe_bid": self._latest["pe_bid"], "pe_ask": self._latest["pe_ask"],
            "past_squareoff": self._past_squareoff(timestamp),
        }

        action, self.portfolio = run_live_check(self.decide_fn, self.cfg, self.portfolio, data_point)
        self.last_action = action

        return action


def connect_and_run(access_token, runner, symbols):
    """
    NOT LIVE-TESTED - see module docstring's caveat. Written to match
    the verified fyers_apiv3 SDK pattern (FyersDataSocket, on_message
    callback receiving a dict per tick, subscribe(symbols=..., data_
    type="SymbolUpdate")). Kept deliberately thin - all the actual
    logic lives in LiveTickRunner.on_tick(), already unit-tested above.
    """

    from fyers_apiv3.FyersWebsocket import data_ws  # imported here, not
    # at module level, so this module can be imported (and its tested
    # parts used) even in an environment without fyers_apiv3 installed
    # - this project's other Fyers integration uses plain `requests`
    # calls, not this SDK, so it is not yet a project dependency (see
    # requirements.txt) - add it before running this function for real.

    def on_message(message):
        timestamp = datetime.datetime.fromtimestamp(
            message.get("exch_feed_time", message.get("last_traded_time")),
            tz=datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
        )
        runner.on_tick(
            symbol=message["symbol"],
            timestamp=timestamp,
            ltp=message.get("ltp"),
            bid=message.get("bid_price"),
            ask=message.get("ask_price"),
        )

    def on_error(message):
        print(f"[fyers websocket error] {message}")

    def on_close(message):
        print(f"[fyers websocket closed] {message}")

    def on_open():
        socket.subscribe(symbols=symbols, data_type="SymbolUpdate")
        socket.keep_running()

    socket = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=on_open,
        on_close=on_close,
        on_error=on_error,
        on_message=on_message,
    )

    socket.connect()
