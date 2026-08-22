import datetime
import glob
import gzip
import os
import shutil

# Added 22-Aug-2026, at the user's own request after checking today's
# real tick-archive size (44MB uncompressed for one full trading day,
# 21-Aug - gzip cut that to 2.86MB, ~16x smaller). Compresses every
# COMPLETED day's tick file in place, keeping the .gz LOCALLY on the
# VPS - unlike run_tick_upload.py (the other nightly half of the tick-
# archival pair), this does NOT need a cloud account (B2 isn't
# configured yet, "NOT LIVE-TESTED" per that file's own docstring) -
# useful today, cloud upload can layer on top later without changing
# anything here.
#
# completed_tick_files()/filter_completed_filenames() - same shared
# "every *.jsonl file except today's, which run_tick_collector.py is
# still writing and must never be touched mid-write" rule run_tick_
# upload.py already uses (strategy/tick_collector.py's own function,
# not duplicated here either) - written independently of run_tick_
# upload.py (not importing from it) to keep top-level scripts calling
# into strategy/, not into each other, matching this project's
# existing layering.
#
# NOTE: once B2 is configured and run_tick_upload.py actually runs, it
# globs "*.jsonl" only - a file this script already compressed (now
# "*.jsonl.gz") would need that glob updated to also pick up ".gz"
# files, or uploaded as-is by a separate follow-up. Out of scope here -
# flagging so it isn't a surprise later.

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TICK_DIR = os.path.join("data", "ticks")


def completed_tick_files(today_filename):
    """
    Every *.jsonl file in TICK_DIR except today's - see module
    docstring for why this mirrors, rather than imports,
    run_tick_upload.py's function of the same name.
    """

    from strategy.tick_collector import filter_completed_filenames

    all_files = glob.glob(os.path.join(TICK_DIR, "*.jsonl"))
    by_name = {os.path.basename(f): f for f in all_files}

    return [by_name[name] for name in filter_completed_filenames(by_name.keys(), today_filename)]


def compress_file(path):
    """
    gzip path -> path + ".gz", verifying the compressed file is real
    (non-empty, smaller than the source) BEFORE removing the original -
    a day's only tick archive must never be deleted on a partial or
    corrupt write. Returns the new .gz path.
    """

    gz_path = path + ".gz"

    with open(path, "rb") as source, gzip.open(gz_path, "wb") as dest:
        shutil.copyfileobj(source, dest)

    original_size = os.path.getsize(path)
    compressed_size = os.path.getsize(gz_path)

    if compressed_size == 0 or compressed_size >= original_size:
        os.remove(gz_path)
        raise RuntimeError(f"compressed size looks wrong ({compressed_size} bytes vs {original_size} original)")

    os.remove(path)

    return gz_path


def main():

    today_filename = f"ticks_{datetime.datetime.now(IST).strftime('%Y%m%d')}.jsonl"

    for path in completed_tick_files(today_filename):
        try:
            gz_path = compress_file(path)
            compressed_size = os.path.getsize(gz_path)
            print(f"Compressed: {path} -> {gz_path} ({compressed_size:,} bytes)")
        except Exception as error:
            print(f"Compress failed for {path} (left in place, will retry tomorrow): {error}")


if __name__ == "__main__":
    main()
