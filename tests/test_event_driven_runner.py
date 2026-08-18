from strategy.event_driven_runner import MultiStrategyRouter, load_portfolio, save_portfolio
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
