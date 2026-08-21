import concurrent.futures
import datetime

from strategy.event_driven_runner import (
    MultiStrategyRouter, load_portfolio, save_all, save_portfolio, _should_send_connection_alert,
)
from strategy import event_driven_runner


class _SpyRunner:

    def __init__(self, name):
        self.name = name
        self.calls = []

    def on_tick(self, symbol, timestamp, ltp, bid, ask):
        self.calls.append(symbol)
        return f"{self.name} saw {symbol}"


def _message(symbol, ltp=100.0):
    return {
        "symbol": symbol, "ltp": ltp, "bid_price": ltp - 0.1, "ask_price": ltp + 0.1,
        "exch_feed_time": 1755500000,
    }


def test_route_dispatches_to_the_registered_runner():
    router = MultiStrategyRouter()
    runner = _SpyRunner("a")
    router.register("NSE:NIFTY50-INDEX", runner)

    actions = router.route(_message("NSE:NIFTY50-INDEX"))

    assert actions == ["a saw NSE:NIFTY50-INDEX"]
    assert runner.calls == ["NSE:NIFTY50-INDEX"]


def test_route_ignores_unregistered_symbols():
    router = MultiStrategyRouter()
    router.register("NSE:NIFTY50-INDEX", _SpyRunner("a"))

    actions = router.route(_message("NSE:SOMEOTHER-EQ"))

    assert actions == []


def test_route_dispatches_to_multiple_runners_sharing_one_symbol():
    # Real case this project needs: e.g. two different strategies could
    # in principle watch the same underlying tick (not currently true
    # for the 4 built tonight, since each uses its own ATM strike, but
    # the router must support it - a shared symbol should never be
    # silently dropped to just one runner).
    router = MultiStrategyRouter()
    runner_a = _SpyRunner("a")
    runner_b = _SpyRunner("b")
    router.register("NSE:NIFTY50-INDEX", runner_a)
    router.register("NSE:NIFTY50-INDEX", runner_b)

    actions = router.route(_message("NSE:NIFTY50-INDEX"))

    assert set(actions) == {"a saw NSE:NIFTY50-INDEX", "b saw NSE:NIFTY50-INDEX"}
    assert runner_a.calls == ["NSE:NIFTY50-INDEX"]
    assert runner_b.calls == ["NSE:NIFTY50-INDEX"]


def test_all_symbols_lists_every_registered_symbol_once():
    router = MultiStrategyRouter()
    router.register("A", _SpyRunner("x"))
    router.register("B", _SpyRunner("x"))
    router.register("A", _SpyRunner("y"))  # same symbol, second runner

    assert sorted(router.all_symbols()) == ["A", "B"]


def test_runners_for_returns_the_registered_runners_for_a_symbol():
    router = MultiStrategyRouter()
    runner_a = _SpyRunner("a")
    runner_b = _SpyRunner("b")
    router.register("NSE:NIFTY50-INDEX", runner_a)
    router.register("NSE:NIFTY50-INDEX", runner_b)
    router.register("NSE:NIFTYBANK-INDEX", runner_b)

    assert router.runners_for("NSE:NIFTY50-INDEX") == [runner_a, runner_b]
    assert router.runners_for("NSE:NIFTYBANK-INDEX") == [runner_b]


def test_runners_for_empty_for_an_unregistered_symbol():
    router = MultiStrategyRouter()

    assert router.runners_for("NSE:SOMEOTHER-EQ") == []


class _FakePortfolioRunner:
    def __init__(self, portfolio):
        self.portfolio = portfolio


def test_save_all_only_touches_the_given_keys(tmp_path, monkeypatch):
    # Real bug fixed 21-Aug-2026: save_all() used to re-save/re-sync
    # EVERY runner on every tick regardless of which one the tick
    # actually touched - this is the regression test for the `keys`
    # filter that fixes it.
    monkeypatch.setattr(event_driven_runner, "PORTFOLIO_DIR", str(tmp_path))
    monkeypatch.setitem(event_driven_runner.STRATEGY_NAMES, "book_a", "book_a_name")
    monkeypatch.setitem(event_driven_runner.STRATEGY_NAMES, "book_b", "book_b_name")

    runners = {
        "book_a": _FakePortfolioRunner({"Cash": 111, "Position": None, "Closed Trades": []}),
        "book_b": _FakePortfolioRunner({"Cash": 222, "Position": None, "Closed Trades": []}),
    }

    save_all(runners, keys=["book_a"])

    assert load_portfolio("book_a_name")["Cash"] == 111
    assert not (tmp_path / "fyers_options_book_b_name_portfolio.json").exists()


def test_save_all_submits_firebase_sync_to_the_given_executor(tmp_path, monkeypatch):
    # Real bug fixed 21-Aug-2026: sync_portfolio() (a real cross-region
    # network call) used to run synchronously in the hot WebSocket-
    # message path - confirmed live as the dominant cause of a real
    # tick-latency incident. This confirms it's submitted to the
    # executor (background) rather than called directly.
    monkeypatch.setattr(event_driven_runner, "PORTFOLIO_DIR", str(tmp_path))
    monkeypatch.setitem(event_driven_runner.STRATEGY_NAMES, "book_a", "book_a_name")

    calls = []
    monkeypatch.setattr(
        "report.firebase_realtime_sync.sync_portfolio",
        lambda name, portfolio: calls.append((name, portfolio)),
    )

    runners = {"book_a": _FakePortfolioRunner({"Cash": 111, "Position": None, "Closed Trades": []})}

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    save_all(runners, keys=["book_a"], firebase_executor=executor)
    executor.shutdown(wait=True)  # block until the submitted sync has actually run

    assert calls == [("book_a_name", {"Cash": 111, "Position": None, "Closed Trades": []})]


def test_load_portfolio_returns_fresh_state_when_no_file_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(event_driven_runner, "PORTFOLIO_DIR", str(tmp_path))

    portfolio = load_portfolio("nonexistent_book", initial_capital=50000)

    assert portfolio == {"Cash": 50000, "Position": None, "Closed Trades": []}


def test_save_then_load_portfolio_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(event_driven_runner, "PORTFOLIO_DIR", str(tmp_path))

    original = {"Cash": 123456.78, "Position": {"Option Type": "CE"}, "Closed Trades": [{"Net PnL": 500}]}
    save_portfolio("some_book", original)

    reloaded = load_portfolio("some_book")

    assert reloaded == original


def test_connection_alert_fires_on_the_first_ever_event():
    assert _should_send_connection_alert(last_alert_at=None, now=datetime.datetime(2026, 8, 18, 10, 0, 0)) is True


def test_connection_alert_suppressed_within_the_cooldown_window():
    last = datetime.datetime(2026, 8, 18, 10, 0, 0)
    soon_after = last + datetime.timedelta(minutes=5)  # well under the 15-min cooldown

    assert _should_send_connection_alert(last, soon_after) is False


def test_connection_alert_fires_again_once_the_cooldown_has_passed():
    last = datetime.datetime(2026, 8, 18, 10, 0, 0)
    later = last + datetime.timedelta(minutes=16)  # past the 15-min cooldown

    assert _should_send_connection_alert(last, later) is True


def test_connection_alert_boundary_is_inclusive():
    last = datetime.datetime(2026, 8, 18, 10, 0, 0)
    exactly_at_cooldown = last + datetime.timedelta(seconds=900)

    assert _should_send_connection_alert(last, exactly_at_cooldown) is True
