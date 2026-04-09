import pytest

from src.harvester.local_harvester import LocalHarvester


TEST_CONFIG = {
    "general": {"project_name": "Test", "raw_dir": "raw", "processed_dir": "processed", "output_dir": "output"},
    "engine": {
        "ticket_patterns": [r"[A-Z]{2,10}-\d+", r"#\d+"],
        "decision_keywords": ["decided", "approved", "action item"],
        "changelog": {"group_by": "source", "max_entries": 100},
    },
}


def test_stage_file_adds_manifest_entry(tmp_path):
    raw_dir = tmp_path / "raw"
    source = tmp_path / "note.md"
    source.write_text("hello", encoding="utf-8")
    harvester = LocalHarvester(TEST_CONFIG, raw_dir, tmp_path)

    result = harvester.stage_file(source)

    assert result["status"] == "staged"
    staged = harvester.list_staged()
    assert len(staged) == 1
    assert staged[0]["name"] == "note.md"


def test_stage_file_duplicate_returns_already_staged(tmp_path):
    raw_dir = tmp_path / "raw"
    source = tmp_path / "dup.md"
    source.write_text("x", encoding="utf-8")
    harvester = LocalHarvester(TEST_CONFIG, raw_dir, tmp_path)

    first = harvester.stage_file(source)
    second = harvester.stage_file(source)

    assert first["status"] == "staged"
    assert second["status"] == "already_staged"
    assert len(harvester.list_staged()) == 1


def test_stage_file_rejects_unsupported_extension(tmp_path):
    raw_dir = tmp_path / "raw"
    source = tmp_path / "bad.exe"
    source.write_text("binary", encoding="utf-8")
    harvester = LocalHarvester(TEST_CONFIG, raw_dir, tmp_path)

    with pytest.raises(ValueError):
        harvester.stage_file(source)


def test_unstage_file_removes_manifest_entry(tmp_path):
    raw_dir = tmp_path / "raw"
    source = tmp_path / "remove.md"
    source.write_text("remove me", encoding="utf-8")
    harvester = LocalHarvester(TEST_CONFIG, raw_dir, tmp_path)

    harvester.stage_file(source)
    result = harvester.unstage_file(source)

    assert result["status"] == "unstaged"
    assert harvester.list_staged() == []


def test_list_staged_returns_current_manifest(tmp_path):
    raw_dir = tmp_path / "raw"
    source_a = tmp_path / "a.md"
    source_b = tmp_path / "b.txt"
    source_a.write_text("a", encoding="utf-8")
    source_b.write_text("b", encoding="utf-8")
    harvester = LocalHarvester(TEST_CONFIG, raw_dir, tmp_path)

    harvester.stage_file(source_a)
    harvester.stage_file(source_b)
    staged = harvester.list_staged()

    assert len(staged) == 2
    names = {entry["name"] for entry in staged}
    assert names == {"a.md", "b.txt"}
