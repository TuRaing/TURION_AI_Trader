import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(text):
    """
    Send a message to Telegram. Silently skips (with a console note)
    if TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not configured in .env.
    """

    if not BOT_TOKEN or not CHAT_ID:

        print("Telegram not configured (.env missing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID) - skipping notification.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(url, data={"chat_id": CHAT_ID, "text": text})

    if response.status_code != 200:
        print(f"Telegram notification failed: {response.text}")
