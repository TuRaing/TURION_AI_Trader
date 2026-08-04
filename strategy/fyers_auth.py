import hashlib
import os
import re
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv, set_key, find_dotenv

# Added 04-Aug-2026 - Fyers login/auth-token flow, implemented against
# their raw REST API (not the official fyers-apiv3 SDK - that SDK's
# aiohttp dependency failed to build on this machine's Python 3.14,
# no prebuilt wheel yet and no MS C++ Build Tools installed; the raw
# HTTP approach avoids that entirely and needs nothing beyond
# `requests`, already a project dependency).
#
# Credentials (FYERS_APP_ID, FYERS_SECRET_KEY) live in .env (gitignored,
# never committed) - see strategy/fyers_auth.py's __main__ below for the
# one-time interactive login. The resulting FYERS_ACCESS_TOKEN is also
# written to .env - it is a DAILY token (Fyers invalidates it every
# trading day), so this login step needs re-running each day before the
# integration can make authenticated calls.

BASE_URL = "https://api-t1.fyers.in/api/v3"
ENV_PATH = find_dotenv()


def _app_id():
    load_dotenv(ENV_PATH, override=True)
    app_id = os.environ.get("FYERS_APP_ID")

    if not app_id:
        raise RuntimeError("FYERS_APP_ID not set in .env")

    return app_id


def _secret_key():
    load_dotenv(ENV_PATH, override=True)
    secret_key = os.environ.get("FYERS_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("FYERS_SECRET_KEY not set in .env")

    return secret_key


def _redirect_uri():
    load_dotenv(ENV_PATH, override=True)
    return os.environ.get("FYERS_REDIRECT_URI", "https://127.0.0.1")


def generate_login_url(state="turion_ai_trader"):
    """
    Builds the URL the user opens in a browser, logs into Fyers, and gets
    redirected from - the redirect URL's query string carries the
    one-time auth_code that generate_access_token() below needs.
    """

    params = {
        "client_id": _app_id(),
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "state": state,
    }

    return f"{BASE_URL}/generate-authcode?{urlencode(params)}"


def extract_auth_code(redirected_url_or_code):
    """
    Accepts either the full redirected URL (the page the browser lands
    on after login, which usually fails to load since redirect_uri is
    127.0.0.1 - the auth_code is still right there in the address bar)
    or just the bare auth_code string, and returns the bare code either
    way.
    """

    if "auth_code=" not in redirected_url_or_code:
        return redirected_url_or_code.strip()

    query = parse_qs(urlparse(redirected_url_or_code).query)
    codes = query.get("auth_code")

    if not codes:
        raise ValueError("Could not find auth_code in the given URL")

    return codes[0]


def generate_access_token(auth_code):
    """
    Exchanges a one-time auth_code (from the login redirect) for a daily
    access_token, and saves it to .env as FYERS_ACCESS_TOKEN.

    Returns
    -------
    str - the access token.
    """

    app_id = _app_id()
    secret_key = _secret_key()

    app_id_hash = hashlib.sha256(f"{app_id}:{secret_key}".encode()).hexdigest()

    response = requests.post(
        f"{BASE_URL}/validate-authcode",
        json={
            "grant_type": "authorization_code",
            "appIdHash": app_id_hash,
            "code": auth_code,
        },
        timeout=15,
    )

    data = response.json()

    if data.get("s") != "ok" or "access_token" not in data:
        raise RuntimeError(f"Fyers auth-code exchange failed: {data}")

    access_token = data["access_token"]

    set_key(ENV_PATH, "FYERS_ACCESS_TOKEN", access_token)

    return access_token


def get_access_token():
    load_dotenv(ENV_PATH, override=True)
    token = os.environ.get("FYERS_ACCESS_TOKEN")

    if not token:
        raise RuntimeError(
            "No FYERS_ACCESS_TOKEN found - run `python -m strategy.fyers_auth` "
            "to log in first (needed once per trading day)."
        )

    return token


def verify_connection():
    """
    Calls Fyers' profile endpoint as a smoke test - confirms the saved
    access token actually works.
    """

    app_id = _app_id()
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/profile",
        headers={"Authorization": f"{app_id}:{token}"},
        timeout=15,
    )

    return response.json()


if __name__ == "__main__":

    print("Open this URL in a browser and log in to Fyers:\n")
    print(generate_login_url())
    print()
    print(
        "After login, the browser will try to redirect and likely show a "
        "'can't reach this page' error - that's expected (127.0.0.1 isn't "
        "running a server). Copy the FULL address-bar URL at that point "
        "(it contains auth_code=...) and paste it below."
    )
    print()

    pasted = input("Paste the redirected URL (or just the auth_code): ").strip()
    code = extract_auth_code(pasted)

    token = generate_access_token(code)
    print(f"\nSaved FYERS_ACCESS_TOKEN to {ENV_PATH}\n")

    profile = verify_connection()

    if profile.get("s") == "ok":
        name = profile.get("data", {}).get("name", "(name unavailable)")
        print(f"Connected successfully - Fyers account: {name}")
    else:
        print(f"Token saved but the profile check failed: {profile}")
