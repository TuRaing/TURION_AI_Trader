import datetime
import os
import subprocess

# Added 20-Aug-2026 - the user's own chosen alternative to Backblaze B2
# (run_tick_upload.py) for now: instead of paying for cloud storage
# immediately, pull each COMPLETED day's tick file down from the VPS to
# THIS machine over SCP, then delete it on the VPS to free disk - a
# free stopgap for the first several days of real data, matching this
# project's own established "wait for more real data before committing
# to infra spend" pattern (see [[feedback_data_driven_patience]]).
# Meant to be run from wherever the turion_vps SSH private key lives
# (this laptop) - the VPS cannot push here itself (no way to reach a
# laptop with no public IP), so this is a "pull" script, always run
# from this side.
#
# Reuses strategy/tick_collector.py's filter_completed_filenames() -
# same shared rule run_tick_upload.py's B2 path uses, so "what counts
# as completed" can never drift between the two destinations.
#
# NOT LIVE-TESTED - no real tick files exist on the VPS yet (the
# collector itself hasn't been deployed/run there yet either).

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

VPS_HOST = "65.20.78.253"
VPS_USER = "root"
VPS_SSH_KEY = os.path.expanduser("~/.ssh/turion_vps")
VPS_TICK_DIR = "/opt/turion/TURION_AI_Trader/data/ticks"

LOCAL_ARCHIVE_DIR = os.path.join("data", "ticks_archive")


def _ssh_base():
    return ["ssh", "-i", VPS_SSH_KEY, "-o", "BatchMode=yes", f"{VPS_USER}@{VPS_HOST}"]


def list_remote_tick_files():
    """
    Bare filenames only (no path) of every *.jsonl currently in the
    VPS's tick directory - returns [] if the directory doesn't exist
    yet (collector never run) rather than raising, since that's a
    normal/expected state, not an error.
    """

    result = subprocess.run(
        _ssh_base() + [f"ls -1 {VPS_TICK_DIR}/*.jsonl 2>/dev/null || true"],
        capture_output=True, text=True, timeout=30,
    )

    return [os.path.basename(line) for line in result.stdout.splitlines() if line.strip()]


def main():

    from strategy.tick_collector import filter_completed_filenames, tick_log_filename

    remote_files = list_remote_tick_files()

    if not remote_files:
        print("No tick files on the VPS yet - nothing to sync.")
        return

    today_filename = tick_log_filename(datetime.datetime.now(IST))
    completed = filter_completed_filenames(remote_files, today_filename)

    if not completed:
        print("Only today's (still-being-written) tick file exists - nothing completed to sync yet.")
        return

    os.makedirs(LOCAL_ARCHIVE_DIR, exist_ok=True)

    for filename in completed:
        remote_path = f"{VPS_USER}@{VPS_HOST}:{VPS_TICK_DIR}/{filename}"
        local_path = os.path.join(LOCAL_ARCHIVE_DIR, filename)

        scp = subprocess.run(
            ["scp", "-i", VPS_SSH_KEY, "-o", "BatchMode=yes", remote_path, local_path],
            capture_output=True, text=True, timeout=300,
        )

        if scp.returncode != 0:
            print(f"Copy failed for {filename} (left on VPS, will retry next time): {scp.stderr.strip()}")
            continue

        remote_size_result = subprocess.run(
            _ssh_base() + [f"stat -c%s {VPS_TICK_DIR}/{filename}"],
            capture_output=True, text=True, timeout=30,
        )
        remote_size = remote_size_result.stdout.strip()
        local_size = str(os.path.getsize(local_path))

        if remote_size != local_size:
            print(f"Size mismatch for {filename} (remote {remote_size} vs local {local_size}) - "
                  f"NOT deleting from VPS, leaving local copy for inspection.")
            continue

        subprocess.run(_ssh_base() + [f"rm {VPS_TICK_DIR}/{filename}"], timeout=30)
        print(f"Synced and removed from VPS: {filename} -> {local_path}")


if __name__ == "__main__":
    main()
