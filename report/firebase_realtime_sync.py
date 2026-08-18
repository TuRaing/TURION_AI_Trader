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


def fetch_access_token():
    """Call at VPS startup (strategy/event_driven_runner.py's main())
    to get today's real access_token. Returns None if Firebase isn't
    configured or no token has been synced yet today - the caller must
    treat that as "not logged in yet," same as fyers_auth.py's own
    get_access_token() treats a missing FYERS_ACCESS_TOKEN env var."""

    token = fetch_state(_TOKEN_PATH)

    return token if isinstance(token, str) and token else None
