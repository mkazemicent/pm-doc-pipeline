from pathlib import Path

from src.engine.changelog import ChangelogGenerator
from src.engine.tracker import FileChange


TEST_CONFIG = {
    "general": {"project_name": "Test", "raw_dir": "raw", "processed_dir": "processed", "output_dir": "output"},
    "engine": {
        "ticket_patterns": [r"[A-Z]{2,10}-\d+", r"#\d+"],
        "decision_keywords": ["decided", "approved", "action item"],
        "changelog": {"group_by": "source", "max_entries": 100},
    },
}


def test_generate_empty_changes_returns_no_changes_message():
    generator = ChangelogGenerator(TEST_CONFIG)

    result = generator.generate([])

    assert "# Changelog" in result
    assert "_No changes detected._" in result


def test_generate_groups_by_source():
    generator = ChangelogGenerator(TEST_CONFIG)
    changes = [
        FileChange(
            filepath=Path("processed/local/notes.md"),
            change_type="added",
            diff_summary="New file",
            tickets=["PROJ-101"],
            timestamp="2026-04-09T10:00:00+00:00",
        ),
        FileChange(
            filepath=Path("processed/github/issue_7.md"),
            change_type="modified",
            diff_summary="Updated issue",
            tickets=[],
            timestamp="2026-04-09T11:00:00+00:00",
        ),
    ]

    result = generator.generate(changes)

    assert "## local" in result
    assert "## github" in result
    assert "**notes.md** [PROJ-101]" in result
    assert "**issue_7.md**" in result


def test_generate_group_by_ticket_mode():
    cfg = {
        **TEST_CONFIG,
        "engine": {**TEST_CONFIG["engine"], "changelog": {"group_by": "ticket", "max_entries": 100}},
    }
    generator = ChangelogGenerator(cfg)
    changes = [
        FileChange(
            filepath=Path("processed/local/a.md"),
            change_type="modified",
            diff_summary="changed",
            tickets=["PROJ-200"],
            timestamp="2026-04-09T12:00:00+00:00",
        ),
        FileChange(
            filepath=Path("processed/local/b.md"),
            change_type="deleted",
            diff_summary="deleted",
            tickets=[],
            timestamp="2026-04-09T12:05:00+00:00",
        ),
    ]

    result = generator.generate(changes)

    assert "## PROJ-200" in result
    assert "## No Ticket" in result


def test_generate_group_by_date_mode():
    cfg = {
        **TEST_CONFIG,
        "engine": {**TEST_CONFIG["engine"], "changelog": {"group_by": "date", "max_entries": 100}},
    }
    generator = ChangelogGenerator(cfg)
    changes = [
        FileChange(
            filepath=Path("processed/local/day1.md"),
            change_type="added",
            diff_summary="added",
            tickets=[],
            timestamp="2026-04-08T09:00:00+00:00",
        ),
        FileChange(
            filepath=Path("processed/local/day2.md"),
            change_type="added",
            diff_summary="added",
            tickets=[],
            timestamp="2026-04-09T09:00:00+00:00",
        ),
    ]

    result = generator.generate(changes)

    assert "## 2026-04-08" in result
    assert "## 2026-04-09" in result
