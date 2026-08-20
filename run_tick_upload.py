import datetime
import glob
import os

# Added 20-Aug-2026 - the nightly half of the tick-archival pair (see
# run_tick_collector.py). Uploads every COMPLETED day's tick file
# (anything except today's, which is still being written) to Backblaze
# B2 via its S3-compatible API, then deletes the local copy - keeps
# the VPS's own disk to a rolling ~1-2 day buffer, matching the
# reasoning in doc/PROJECT_STATUS.md's 15-Aug "TICK-BY-TICK DATA
# STORAGE" entry (object storage recommended over block storage or a
# physical drive). Uses boto3 (already a project dependency - see
# requirements.txt) against B2's S3-compatible endpoint rather than
# adding the separate b2sdk package, for one less dependency.
#
# GRACEFULLY SKIPS (never raises) if B2 isn't configured yet - same
# convention as report/push_notifier.py and report/telegram_notifier.py
# - the collector must never be blocked on this running. Needs a B2
# account + bucket the user sets up themselves (Claude cannot create
# third-party cloud accounts) - B2_KEY_ID/B2_APPLICATION_KEY/B2_BUCKET/
# B2_ENDPOINT as env vars, same pattern as every other credential in
# this project.
#
# NOT LIVE-TESTED - no B2 bucket exists yet to upload to.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TICK_DIR = os.path.join("data", "ticks")


def _b2_client():
    import boto3

    key_id = os.getenv("B2_KEY_ID")
    app_key = os.getenv("B2_APPLICATION_KEY")
    endpoint = os.getenv("B2_ENDPOINT")

    if not (key_id and app_key and endpoint):
        return None

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=app_key,
    )


def completed_tick_files(today_filename):
    """
    Every *.jsonl file in TICK_DIR except today's (still being
    written by run_tick_collector.py, must never be touched while
    live). Thin wrapper around strategy/tick_collector.py's shared
    filter_completed_filenames() - see that function's docstring for
    why it's shared with sync_ticks_from_vps.py rather than
    duplicated.
    """

    from strategy.tick_collector import filter_completed_filenames

    all_files = glob.glob(os.path.join(TICK_DIR, "*.jsonl"))
    by_name = {os.path.basename(f): f for f in all_files}

    return [by_name[name] for name in filter_completed_filenames(by_name.keys(), today_filename)]


def main():

    from strategy.tick_collector import tick_log_filename

    bucket = os.getenv("B2_BUCKET")
    client = _b2_client()

    if client is None or not bucket:
        print("B2 not configured yet (B2_KEY_ID/B2_APPLICATION_KEY/B2_ENDPOINT/B2_BUCKET) - "
              "skipping upload, files stay local.")
        return

    today_filename = tick_log_filename(datetime.datetime.now(IST))

    for path in completed_tick_files(today_filename):
        key = f"ticks/{os.path.basename(path)}"
        try:
            client.upload_file(path, bucket, key)
            os.remove(path)
            print(f"Uploaded and removed local copy: {path} -> b2://{bucket}/{key}")
        except Exception as error:
            print(f"Upload failed for {path} (left in place, will retry tomorrow): {error}")


if __name__ == "__main__":
    main()
