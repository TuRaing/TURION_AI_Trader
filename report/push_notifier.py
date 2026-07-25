import json
import os

BOT_INITIALIZED = False


def _init_firebase():
    """
    Lazily initialise the Firebase Admin SDK from the FIREBASE_SERVICE_ACCOUNT
    env var (the service account key's JSON content, stored as a GitHub
    Secret - never committed to the repo). Returns True if ready to send.
    """

    global BOT_INITIALIZED

    if BOT_INITIALIZED:
        return True

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not service_account_json:
        return False

    import firebase_admin
    from firebase_admin import credentials

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(service_account_json))
            firebase_admin.initialize_app(cred)
    except Exception as e:
        # A malformed/wrong FIREBASE_SERVICE_ACCOUNT secret must never take
        # down the trading pipeline with it - same graceful-degradation
        # rule as everything else in this module.
        print(f"Firebase misconfigured (FIREBASE_SERVICE_ACCOUNT invalid) - skipping push notification: {e}")
        return False

    BOT_INITIALIZED = True
    return True


def send_push_notification(title, body):
    """
    Push a notification to every app instance subscribed to the
    "trade_alerts" topic (all installs of the TURION AI Trader app -
    topic messaging avoids having to track individual device tokens).
    Silently skips (with a console note) if FIREBASE_SERVICE_ACCOUNT isn't
    configured, and never raises - a push-notification failure must never
    break the trading pipeline, same philosophy as the other engines that
    degrade gracefully instead of crashing.
    """

    if not _init_firebase():

        print("Firebase not configured (FIREBASE_SERVICE_ACCOUNT missing) - skipping push notification.")
        return

    from firebase_admin import messaging

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        topic="trade_alerts",
    )

    try:
        messaging.send(message)
        print("Push notification sent successfully.")
    except Exception as e:
        print(f"Push notification failed: {e}")
