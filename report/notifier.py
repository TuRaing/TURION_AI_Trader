from report.telegram_notifier import send_telegram_message
from report.push_notifier import send_push_notification


def notify(text, title="TURION AI Trader"):
    """
    Send a trade alert on every configured channel - Telegram (existing)
    and the TURION AI Trader app's push notifications (Firebase Cloud
    Messaging). Each channel fails independently and silently (see their
    own modules) so a channel being unconfigured or down never blocks
    the other or the trading pipeline itself.
    """

    send_telegram_message(text)
    send_push_notification(title, text)
