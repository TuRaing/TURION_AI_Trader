import os

from report.push_notifier import _init_firebase

# Added 18-Aug-2026 - the Firebase Realtime Database half of the
# LIVE-DATA ARCHITECTURE plan (PROJECT_STATUS.md, 06/07-Aug): VPS ->
# WebSocket event-driven engine -> Firebase Realtime Database -> the
# Flutter app subscribes directly, no more periodic HTTP polling. This
# is a DIFFERENT Firebase product from report/push_notifier.py's
# existing integration (that's Firebase Cloud Messaging - one-way push
# notifications; this is Realtime Database - a live, subscribable data
# store) - confirmed no Realtime Database usage existed anywhere in
# this project before tonight (checked, not assumed).
#
# Reuses push_notifier.py's _init_firebase() (same FIREBASE_SERVICE_
# ACCOUNT credential, same firebase_admin app, idempotent init) rather
# than a second copy of that credential-loading logic - firebase_admin
# is already a project dependency (requirements.txt) and already
# verified installed/importable in this session (7.5.0, firebase_
# admin.db module confirmed present via real inspection, not guessed).
#
# NOT LIVE-TESTED - same class of caveat as tonight's WebSocket work:
# needs a real Firebase project with Realtime Database actually
# ENABLED (a one-time manual step in the Firebase Console, not code)
# and a real FIREBASE_DATABASE_URL, neither of which exist yet. Graceful
# degradation (never raises, same philosophy as every other channel in
# this project) IS verified - see tests/test_firebase_realtime_sync.py.

DATABASE_URL_ENV_VAR = "FIREBASE_DATABASE_URL"


def _database_url():
    return os.getenv(DATABASE_URL_ENV_VAR)


def sync_state(path, value):
    """
    Writes `value` (must be JSON-serializable) to the Firebase Realtime
    Database at `path`. Silently skips (never raises) if either
    FIREBASE_SERVICE_ACCOUNT or FIREBASE_DATABASE_URL aren't configured
    - same graceful-degradation rule as report/push_notifier.py - a
    sync failure must never break the trading pipeline itself.

    Returns
    -------
    bool - True if the write was attempted and succeeded, False if
    skipped (not configured) or failed.
    """

    if not _init_firebase():
        print("Firebase not configured (FIREBASE_SERVICE_ACCOUNT missing) - skipping realtime sync.")
        return False

    url = _database_url()

    if not url:
        print(f"Firebase Realtime Database not configured ({DATABASE_URL_ENV_VAR} missing) - skipping realtime sync.")
        return False

    from firebase_admin import db

    try:
        db.reference(path, url=url).set(value)
        return True
    except Exception as e:
        print(f"Firebase realtime sync failed for {path}: {e}")
        return False


def fetch_state(path):
    """
    Reads and returns the current value at `path`, or None if not
    configured, not reachable, or nothing is there yet - never raises,
    same graceful-degradation contract as sync_state().
    """

    if not _init_firebase():
        print("Firebase not configured (FIREBASE_SERVICE_ACCOUNT missing) - skipping realtime fetch.")
        return None

    url = _database_url()

    if not url:
        print(f"Firebase Realtime Database not configured ({DATABASE_URL_ENV_VAR} missing) - skipping realtime fetch.")
        return None

    from firebase_admin import db

    try:
        return db.reference(path, url=url).get()
    except Exception as e:
        print(f"Firebase realtime fetch failed for {path}: {e}")
        return None


def sync_portfolio(strategy_name, portfolio):
    """
    Convenience wrapper - writes one event-driven book's live portfolio
    state to /event_driven_portfolios/{strategy_name}. Intended to be
    called from strategy/event_driven_runner.py's save_all() IN
    ADDITION TO the existing local-JSON persistence, not instead of it
    - local JSON stays the source of truth this project's own
    verification/replay tooling already depends on; Firebase is purely
    a live read-path for the app, never the only copy of the data.
    """

    return sync_state(f"/event_driven_portfolios/{strategy_name}", portfolio)


# Added 18-Aug-2026 - the VPS daily-token-delivery gap flagged during
# the day's VPS/Firebase file-inventory check: fyers_trigger_run.py
# already shares each day's Fyers access_token with GitHub Actions'
# scheduled workflows (as the FYERS_ACCESS_TOKEN repo secret, via
# strategy/github_secrets.py's update_repo_secret()) once the user taps
# "Login to Fyers" in the app - but a VPS is not a GitHub Actions
# runner, so it never receives that secret. Rather than build a whole
# second login flow/app (discussed and explicitly decided against -
# would duplicate the OAuth/auth_code handling that already exists),
# fyers_trigger_run.py now ALSO writes the same real access_token here,
# right next to the existing GitHub-secret-sharing step, reusing the
# SAME Firebase Realtime Database already wired up for portfolio sync
# tonight - one more path written through the one channel, not a new
# mechanism. strategy/event_driven_runner.py's main() reads it back via
# fetch_access_token() at VPS startup each day.
_TOKEN_PATH = "/vps_config/fyers_access_token"


def sync_access_token(access_token):
    """Call once, right after generate_access_token() succeeds - see
    fyers_trigger_run.py's "Sharing today's token with the VPS" step."""

    return sync_state(_TOKEN_PATH, access_token)


# Added 20-Aug-2026 - two more consumers of the same Realtime Database
# channel, for the mobile app's new "VPS" and "Checks" tabs: live ATM
# ticks (run_tick_collector.py, one SET per tick - overwrites the
# previous value, the app only ever needs "right now", not a live
# history - that's what the local JSONL archive is for) and health-
# check results (run_pre_market_check.py / run_market_check.py, one
# PUSH per run - an append-only feed so the app can show recent runs
# with their own timestamp, not just the latest one).
_LIVE_TICKS_PATH = "/live_ticks"
_HEALTH_CHECKS_PATH = "/health_checks"
_LIVE_CANDLES_PATH = "/live_candles"
_STRATEGY_TICKS_PATH = "/strategy_ticks"
_STRATEGY_CANDLES_PATH = "/strategy_candles"


def sync_live_tick(index, leg, record):
    """Call once per tick from run_tick_collector.py, in addition to
    (not instead of) the local JSONL archive - this is the live "what's
    happening right now" path the app subscribes to; the archive is the
    durable record."""

    return sync_state(f"{_LIVE_TICKS_PATH}/{index}/{leg}", record)


def sync_live_candles(index, candles):
    """
    Added 21-Aug-2026 - real gap found live: the app's LiveChartScreen
    aggregates its own 1-min candles client-side, but had no history to
    seed from (sync_live_tick() above only ever holds the single latest
    tick) - opening the chart showed one lone building candle instead of
    a real chart. run_tick_collector.py's own LiveCandleAggregator
    (strategy/tick_collector.py) maintains the real rolling history and
    calls this ONCE PER CLOSED CANDLE (not per tick - a per-tick sync
    here would reintroduce the exact blocking-Firebase-call latency bug
    fixed the same day). One overwrite per index, same "latest state,
    not a growing feed" shape as sync_live_tick() - the app fetches this
    ONCE at startup to seed itself, then keeps updating the current
    candle live from its own existing tick stream unchanged.
    """

    return sync_state(f"{_LIVE_CANDLES_PATH}/{index}", candles)


def sync_strategy_tick(strategy_name, leg, record):
    """
    Added 21-Aug-2026, at the user's own request: a live option-premium
    chart (Entry/Target/Stop-Loss overlaid, exact - not a spot-price
    approximation, same as how a real broker app charts an option
    position against its own premium, not the underlying) for a
    specific event-driven book's CURRENT position. `leg` is "CE" or
    "PE" - strategy/event_driven_runner.py's on_message() syncs BOTH
    legs for every runner regardless of which one is currently open, so
    switching sides (a new position, possibly the other leg) never hits
    a cold path. Same "latest tick" shape as sync_live_tick() above -
    kept as a SEPARATE path (not reused) because a strategy's own ATM
    strike can differ from run_tick_collector.py's independent ATM pick
    for the same index (each picks its own at its own startup - see
    event_driven_runner.py's own module docstring), so the two are not
    interchangeable data.
    """

    return sync_state(f"{_STRATEGY_TICKS_PATH}/{strategy_name}/{leg}", record)


def sync_strategy_candles(strategy_name, leg, candles):
    """See sync_strategy_tick()'s own note - the candle-history
    equivalent, same "sync once per closed candle, not per tick"
    contract as sync_live_candles()."""

    return sync_state(f"{_STRATEGY_CANDLES_PATH}/{strategy_name}/{leg}", candles)


def sync_health_check(check_type, report_text, timestamp):
    """
    Call once per health-check run (check_type: "pre_market", "market",
    or "after_market" - run_market_check.py decides between the latter
    two by time of day, since both currently share one script). Pushes
    a new entry (Firebase auto-generated, chronologically ordered key)
    rather than overwriting, so the app's Checks tab can show a real
    feed of past runs with their own name + timestamp, not just the
    latest.
    """

    if not _init_firebase():
        print("Firebase not configured (FIREBASE_SERVICE_ACCOUNT missing) - skipping health-check sync.")
        return False

    url = _database_url()

    if not url:
        print(f"Firebase Realtime Database not configured ({DATABASE_URL_ENV_VAR} missing) - "
              "skipping health-check sync.")
        return False

    from firebase_admin import db

    try:
        db.reference(f"{_HEALTH_CHECKS_PATH}/{check_type}", url=url).push({
            "report": report_text,
            "timestamp": timestamp,
        })
        return True
    except Exception as e:
        print(f"Firebase health-check sync failed for {check_type}: {e}")
        return False


def fetch_access_token():
    """Call at VPS startup (strategy/event_driven_runner.py's main())
    to get today's real access_token. Returns None if Firebase isn't
    configured or no token has been synced yet today - the caller must
    treat that as "not logged in yet," same as fyers_auth.py's own
    get_access_token() treats a missing FYERS_ACCESS_TOKEN env var."""

    token = fetch_state(_TOKEN_PATH)

    return token if isinstance(token, str) and token else None
