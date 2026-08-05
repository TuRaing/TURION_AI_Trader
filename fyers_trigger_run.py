import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from strategy.fyers_auth import generate_access_token, verify_connection
from strategy.fyers_daily_tasks import run_all_tasks
from strategy.github_secrets import update_repo_secret

# Added 04-Aug-2026, UPDATED 05-Aug-2026 - the single entry point the
# "Login to Fyers" in-app WebView button triggers (via a GitHub Actions
# workflow_dispatch, see .github/workflows/fyers_trigger.yml). Takes the
# one-time auth_code from the app, exchanges it for today's access_token,
# runs every Fyers data task once immediately, AND (05-Aug) shares that
# access_token with the rest of the trading day by writing it to the
# FYERS_ACCESS_TOKEN repo secret - Fyers tokens are valid all day, not
# just for one call, so this is what lets the separately-scheduled
# fyers_scheduled_check.yml/fyers_squareoff.yml workflows keep checking
# positions every few minutes for the rest of the day without the user
# logging in again. Needs REPO_ADMIN_PAT (a "Secrets: write"-scoped PAT,
# set up by the user, server-side only - never embedded in the app,
# unlike the Actions-only PAT the WebView button itself uses) - if that
# secret isn't configured yet, this step is skipped with a warning
# rather than failing the whole run (keeps the original one-shot trigger
# working even before continuous automation is fully set up).


def main():

    auth_code = os.environ.get("FYERS_AUTH_CODE")

    if not auth_code:
        print("FYERS_AUTH_CODE not set - nothing to do.")
        sys.exit(1)

    print("Exchanging auth_code for today's access token...")
    generate_access_token(auth_code)

    profile = verify_connection()

    if profile.get("s") != "ok":
        print(f"Login verification failed - aborting before running anything: {profile}")
        sys.exit(1)

    name = profile.get("data", {}).get("name", "(name unavailable)")
    print(f"Connected as {name}. Running today's Fyers tasks...")

    print("\n--- Sharing today's token with scheduled workflows ---")
    admin_pat = os.environ.get("REPO_ADMIN_PAT")
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")

    if not admin_pat or not repo_full_name:
        print("REPO_ADMIN_PAT/GITHUB_REPOSITORY not set - skipping "
              "(scheduled workflows won't have today's token; only this "
              "one-shot run happens).")
    else:
        try:
            owner, repo = repo_full_name.split("/")
            access_token = os.environ["FYERS_ACCESS_TOKEN"]
            update_repo_secret(owner, repo, "FYERS_ACCESS_TOKEN", access_token, admin_pat)
            print("Shared today's token as the FYERS_ACCESS_TOKEN repo secret.")
        except Exception as error:
            print(f"Could not share today's token (continuing): {error}")

    run_all_tasks()

    print("\nDone.")


if __name__ == "__main__":
    main()
