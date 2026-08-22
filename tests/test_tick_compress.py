import gzip
import os

import pytest

from run_tick_compress import completed_tick_files, compress_file, TICK_DIR


def test_completed_tick_files_excludes_todays_file(tmp_path, monkeypatch):
    monkeypatch.setattr("run_tick_compress.TICK_DIR", str(tmp_path))

    for name in ["ticks_20260818.jsonl", "ticks_20260819.jsonl", "ticks_20260820.jsonl"]:
        (tmp_path / name).write_text("{}\n")

    result = completed_tick_files("ticks_20260820.jsonl")

    assert [os.path.basename(p) for p in result] == ["ticks_20260818.jsonl", "ticks_20260819.jsonl"]


def test_completed_tick_files_ignores_already_compressed_files(tmp_path, monkeypatch):
    # A file this script already compressed (.jsonl removed, only
    # .jsonl.gz remains) must never be picked up again - "*.jsonl"
    # naturally doesn't match "*.jsonl.gz", confirming that here.
    monkeypatch.setattr("run_tick_compress.TICK_DIR", str(tmp_path))

    (tmp_path / "ticks_20260818.jsonl.gz").write_bytes(gzip.compress(b"{}\n"))
    (tmp_path / "ticks_20260819.jsonl").write_text("{}\n")

    result = completed_tick_files("ticks_20260820.jsonl")

    assert [os.path.basename(p) for p in result] == ["ticks_20260819.jsonl"]


def test_completed_tick_files_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("run_tick_compress.TICK_DIR", str(tmp_path))

    result = completed_tick_files("ticks_20260820.jsonl")

    assert result == []


def test_compress_file_shrinks_and_removes_the_original(tmp_path):
    original = tmp_path / "ticks_20260818.jsonl"
    # Real tick lines are repetitive JSON - highly compressible, same
    # as the real 21-Aug archive (44MB -> 2.86MB, ~16x). One repeated
    # line is enough to prove gzip actually shrinks it here too.
    original.write_text('{"symbol": "NSE:NIFTY2681824500CE", "ltp": 100.5}\n' * 1000)
    original_size = original.stat().st_size

    gz_path = compress_file(str(original))

    assert gz_path == str(original) + ".gz"
    assert os.path.exists(gz_path)
    assert not os.path.exists(original)
    assert os.path.getsize(gz_path) < original_size

    with gzip.open(gz_path, "rt") as f:
        content = f.read()
    assert content.count("NSE:NIFTY2681824500CE") == 1000


def test_compress_file_is_much_smaller_for_repetitive_data(tmp_path):
    original = tmp_path / "ticks_20260818.jsonl"
    line = '{"symbol": "NSE:NIFTY2681824500CE", "ltp": 100.5, "bid_price": 100.4, "ask_price": 100.6}\n'
    original.write_text(line * 5000)
    original_size = original.stat().st_size

    gz_path = compress_file(str(original))

    assert os.path.getsize(gz_path) < original_size / 5  # highly repetitive data compresses hard


def test_compress_file_raises_and_keeps_original_on_a_corrupt_write(tmp_path, monkeypatch):
    # If gzip ever produced a 0-byte or larger-than-source file (a
    # write-time corruption), the source must be LEFT IN PLACE, never
    # deleted - a day's only tick archive is not something to lose to
    # a transient bug.
    original = tmp_path / "ticks_20260818.jsonl"
    original.write_text('{"symbol": "x"}\n')

    def _broken_copyfileobj(source, dest):
        pass  # writes nothing - simulates a corrupt/empty compressed output

    monkeypatch.setattr("run_tick_compress.shutil.copyfileobj", _broken_copyfileobj)

    with pytest.raises(RuntimeError):
        compress_file(str(original))

    assert original.exists()
    assert not os.path.exists(str(original) + ".gz")
