import pytest

from strategy.execution_backend import PaperExecutionBackend, resolve_execution_backend


def test_paper_backend_on_open_does_not_raise():
    PaperExecutionBackend().on_open({"index": "NIFTY"}, {"Option Type": "CE"})


def test_paper_backend_on_close_does_not_raise():
    PaperExecutionBackend().on_close({"index": "NIFTY"}, {"Net PnL": 500})


def test_resolve_paper_mode_returns_a_paper_backend():
    backend = resolve_execution_backend("paper")

    assert isinstance(backend, PaperExecutionBackend)


def test_resolve_live_mode_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        resolve_execution_backend("live")


def test_resolve_unknown_mode_raises_value_error():
    with pytest.raises(ValueError):
        resolve_execution_backend("sandbox")
