import os

from run_tick_upload import completed_tick_files, TICK_DIR


def test_completed_tick_files_excludes_todays_file(tmp_path, monkeypatch):
    monkeypatch.setattr("run_tick_upload.TICK_DIR", str(tmp_path))

    for name in ["ticks_20260818.jsonl", "ticks_20260819.jsonl", "ticks_20260820.jsonl"]:
        (tmp_path / name).write_text("{}\n")

    result = completed_tick_files("ticks_20260820.jsonl")

    assert [os.path.basename(p) for p in result] == ["ticks_20260818.jsonl", "ticks_20260819.jsonl"]


def test_completed_tick_files_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("run_tick_upload.TICK_DIR", str(tmp_path))

    result = completed_tick_files("ticks_20260820.jsonl")

    assert result == []
