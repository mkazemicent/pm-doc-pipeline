from pathlib import Path

from src.engine.report import WeeklyReportGenerator


def _create_test_artifacts(tmp_path: Path) -> Path:
    """Create minimal output artifacts for testing."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = """---
title: "Test Project - Knowledge Base"
last_updated: "2026-04-09 12:00 UTC"
document_count: 2
decision_count: 1
---

# Test Project - Project Context

## Documents

### Local (2 files)

- **Meeting Notes** - `meeting-notes.md`
- **Roadmap** - `roadmap.md`

## Decisions

_No decisions detected yet._

## Ticket References

- PROJ-123
- #456

## Recent Changes

- `[+]` meeting-notes.md
"""
    (output_dir / "PROJECT_CONTEXT.md").write_text(context, encoding="utf-8")

    decision_log = """# Decision Log

_Generated: 2026-04-09 12:00 UTC_

**Total decisions found:** 1

## Decision #1

- **Source:** `meeting-notes.md`
- **Line:** 5
- **Keywords:** decided
- **Tickets:** PROJ-123

> We decided to use the new auth flow.
"""
    (output_dir / "DECISION_LOG.md").write_text(decision_log, encoding="utf-8")

    changelog = """# Changelog

_Generated: 2026-04-09 12:00 UTC_

**Changes detected:** 2

## local

- `[+]` **meeting-notes.md**
- `[+]` **roadmap.md**
"""
    (output_dir / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    return output_dir


def test_generate_returns_all_sections(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    report = gen.generate()

    assert "## Summary" in report
    assert "## Decisions This Period" in report
    assert "## Ticket Impact" in report
    assert "## Change Log Highlights" in report
    assert "## Risks and Follow-Ups" in report


def test_generate_extracts_ticket_references(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    report = gen.generate()

    assert "PROJ-123" in report
    assert "#456" in report


def test_generate_includes_decision_entries(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    report = gen.generate()

    assert "Decision #1" in report


def test_generate_includes_change_entries(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    report = gen.generate()

    assert "meeting-notes.md" in report


def test_write_creates_file(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    result = gen.write()

    assert result.exists()
    assert "Weekly Report" in result.read_text(encoding="utf-8")


def test_write_custom_output_path(tmp_path: Path):
    output_dir = _create_test_artifacts(tmp_path)
    gen = WeeklyReportGenerator(output_dir)
    custom_path = tmp_path / "custom" / "report.md"
    result = gen.write(custom_path)

    assert result == custom_path
    assert result.exists()


def test_generate_handles_missing_artifacts(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "PROJECT_CONTEXT.md").write_text("", encoding="utf-8")

    gen = WeeklyReportGenerator(output_dir)
    report = gen.generate()

    assert "## Summary" in report
    assert "No decisions detected" in report or "Decisions detected:** 0" in report
