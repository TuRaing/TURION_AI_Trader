from base64 import b64encode

import requests
from nacl import encoding, public

# Added 05-Aug-2026 - lets a GitHub Actions run update one of this repo's
# own Actions secrets, so the daily Fyers access token (obtained once,
# via the user's morning in-app login) can be reused by separate,
# already-scheduled workflows for the rest of that trading day instead
# of requiring a fresh login for every check. Needs a PAT with
# "Secrets: write" permission (stored as the REPO_ADMIN_PAT secret,
# different/more powerful than the app's embedded Actions-only PAT -
# this one only ever runs server-side in GitHub Actions, never ships
# inside the APK). GitHub requires the secret value to be encrypted
# client-side with the repo's own public key (libsodium sealed box)
# before it will accept the update - see
# https://docs.github.com/rest/actions/secrets

GITHUB_API = "https://api.github.com"


def _encrypt(public_key_b64, secret_value):

    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))

    return b64encode(encrypted).decode("utf-8")


def update_repo_secret(owner, repo, secret_name, secret_value, admin_pat):
    """
    Encrypts and writes one repository Actions secret via GitHub's REST
    API. Raises RuntimeError on any failure - callers should treat this
    as "the token could not be shared with scheduled workflows", not a
    silent no-op.
    """

    headers = {
        "Authorization": f"Bearer {admin_pat}",
        "Accept": "application/vnd.github+json",
    }

    key_response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=15,
    )

    if key_response.status_code != 200:
        raise RuntimeError(f"Could not fetch repo public key: {key_response.status_code} {key_response.text}")

    key_data = key_response.json()
    encrypted_value = _encrypt(key_data["key"], secret_value)

    put_response = requests.put(
        f"{GITHUB_API}/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
        timeout=15,
    )

    if put_response.status_code not in (201, 204):
        raise RuntimeError(f"Could not update secret {secret_name}: {put_response.status_code} {put_response.text}")
