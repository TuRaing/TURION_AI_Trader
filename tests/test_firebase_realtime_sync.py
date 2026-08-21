from report.firebase_realtime_sync import (
    sync_state, fetch_state, sync_portfolio, sync_access_token, fetch_access_token,
    sync_live_candles, sync_strategy_tick, sync_strategy_candles, _database_url, DATABASE_URL_ENV_VAR,
)


def test_database_url_reads_the_env_var(monkeypatch):
    monkeypatch.setenv(DATABASE_URL_ENV_VAR, "https://example-default-rtdb.firebaseio.com/")

    assert _database_url() == "https://example-default-rtdb.firebaseio.com/"


def test_database_url_none_when_unset(monkeypatch):
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)

    assert _database_url() is None


def test_sync_state_skips_gracefully_when_firebase_not_configured(monkeypatch):
    # No FIREBASE_SERVICE_ACCOUNT at all - _init_firebase() returns
    # False before ever touching FIREBASE_DATABASE_URL or the network.
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT", raising=False)

    result = sync_state("/some/path", {"a": 1})

    assert result is False


def test_sync_state_skips_gracefully_when_database_url_not_configured(monkeypatch):
    # Simulate Firebase being initialised (credential present) but no
    # FIREBASE_DATABASE_URL yet - must still degrade gracefully, not
    # crash trying to reach a database with no known URL.
    monkeypatch.setattr("report.firebase_realtime_sync._init_firebase", lambda: True)
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)

    result = sync_state("/some/path", {"a": 1})

    assert result is False


def test_sync_portfolio_uses_the_expected_path(monkeypatch):
    captured = {}

    def _fake_sync_state(path, value):
        captured["path"] = path
        captured["value"] = value
        return True

    monkeypatch.setattr("report.firebase_realtime_sync.sync_state", _fake_sync_state)

    sync_portfolio("st2_threshold_eventdriven_nifty", {"Cash": 100000})

    assert captured["path"] == "/event_driven_portfolios/st2_threshold_eventdriven_nifty"
    assert captured["value"] == {"Cash": 100000}


def test_sync_live_candles_uses_the_expected_path(monkeypatch):
    captured = {}

    def _fake_sync_state(path, value):
        captured["path"] = path
        captured["value"] = value
        return True

    monkeypatch.setattr("report.firebase_realtime_sync.sync_state", _fake_sync_state)

    candles = [{"Timestamp": "2026-08-21 09:17:00", "Open": 24200.0, "High": 24250.0, "Low": 24200.0, "Close": 24230.0}]
    sync_live_candles("NIFTY", candles)

    assert captured["path"] == "/live_candles/NIFTY"
    assert captured["value"] == candles


def test_sync_strategy_tick_uses_the_expected_path(monkeypatch):
    captured = {}

    def _fake_sync_state(path, value):
        captured["path"] = path
        captured["value"] = value
        return True

    monkeypatch.setattr("report.firebase_realtime_sync.sync_state", _fake_sync_state)

    sync_strategy_tick("st2_threshold_eventdriven", "CE", {"ltp": 100.5})

    assert captured["path"] == "/strategy_ticks/st2_threshold_eventdriven/CE"
    assert captured["value"] == {"ltp": 100.5}


def test_sync_strategy_candles_uses_the_expected_path(monkeypatch):
    captured = {}

    def _fake_sync_state(path, value):
        captured["path"] = path
        captured["value"] = value
        return True

    monkeypatch.setattr("report.firebase_realtime_sync.sync_state", _fake_sync_state)

    candles = [{"Timestamp": "2026-08-21 09:17:00", "Open": 100.0, "High": 105.0, "Low": 99.0, "Close": 102.0}]
    sync_strategy_candles("st2_threshold_eventdriven", "PE", candles)

    assert captured["path"] == "/strategy_candles/st2_threshold_eventdriven/PE"
    assert captured["value"] == candles


def test_fetch_state_skips_gracefully_when_firebase_not_configured(monkeypatch):
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT", raising=False)

    assert fetch_state("/some/path") is None


def test_fetch_state_skips_gracefully_when_database_url_not_configured(monkeypatch):
    monkeypatch.setattr("report.firebase_realtime_sync._init_firebase", lambda: True)
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)

    assert fetch_state("/some/path") is None


def test_sync_access_token_writes_to_the_vps_config_path(monkeypatch):
    captured = {}

    def _fake_sync_state(path, value):
        captured["path"] = path
        captured["value"] = value
        return True

    monkeypatch.setattr("report.firebase_realtime_sync.sync_state", _fake_sync_state)

    sync_access_token("abc123token")

    assert captured["path"] == "/vps_config/fyers_access_token"
    assert captured["value"] == "abc123token"


def test_fetch_access_token_returns_the_stored_token(monkeypatch):
    monkeypatch.setattr("report.firebase_realtime_sync.fetch_state", lambda path: "abc123token")

    assert fetch_access_token() == "abc123token"


def test_fetch_access_token_none_when_nothing_synced_yet(monkeypatch):
    monkeypatch.setattr("report.firebase_realtime_sync.fetch_state", lambda path: None)

    assert fetch_access_token() is None


def test_fetch_access_token_none_when_value_is_not_a_string(monkeypatch):
    # Defensive - a corrupted/unexpected value at that path (e.g. an
    # accidental dict write) should be treated as "no valid token", not
    # silently handed to the caller as if it were one.
    monkeypatch.setattr("report.firebase_realtime_sync.fetch_state", lambda path: {"unexpected": "shape"})

    assert fetch_access_token() is None
