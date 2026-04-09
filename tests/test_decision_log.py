from src.engine.decision_log import DecisionLogBuilder


TEST_CONFIG = {
    "general": {"project_name": "Test", "raw_dir": "raw", "processed_dir": "processed", "output_dir": "output"},
    "engine": {
        "ticket_patterns": [r"[A-Z]{2,10}-\d+", r"#\d+"],
        "decision_keywords": ["decided", "approved", "action item"],
        "changelog": {"group_by": "source", "max_entries": 100},
    },
}


def test_scan_finds_decision_keywords(tmp_path):
    builder = DecisionLogBuilder(TEST_CONFIG)
    md_file = tmp_path / "processed" / "local" / "notes.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text(
        "Team sync\n"
        "We decided to move launch by one week.\n"
        "Budget was approved by PM.\n"
        "This is unrelated.\n",
        encoding="utf-8",
    )

    decisions = builder.scan([md_file])

    # Adjacent keyword lines merge into one decision context window.
    assert len(decisions) == 1
    matched = {kw for d in decisions for kw in d.keywords_matched}
    assert "decided" in matched
    assert "approved" in matched


def test_scan_returns_empty_when_no_keywords(tmp_path):
    builder = DecisionLogBuilder(TEST_CONFIG)
    md_file = tmp_path / "processed" / "local" / "status.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text("General status update with no decision markers.\n", encoding="utf-8")

    decisions = builder.scan([md_file])

    assert decisions == []


def test_scan_extracts_ticket_references_from_context(tmp_path):
    builder = DecisionLogBuilder(TEST_CONFIG)
    md_file = tmp_path / "processed" / "local" / "tickets.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text(
        "Tracking PROJ-123 and #456\n"
        "Action item: finalize scope tomorrow.\n"
        "Next line\n",
        encoding="utf-8",
    )

    decisions = builder.scan([md_file])

    assert len(decisions) == 1
    assert set(decisions[0].tickets) == {"PROJ-123", "#456"}


def test_render_outputs_markdown_with_decision_entries(tmp_path):
    builder = DecisionLogBuilder(TEST_CONFIG)
    md_file = tmp_path / "processed" / "local" / "render.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text(
        "Ref PROJ-987\n"
        "We decided to ship this week.\n",
        encoding="utf-8",
    )

    decisions = builder.scan([md_file])
    rendered = builder.render(decisions)

    assert "# Decision Log" in rendered
    assert "## Decision #1" in rendered
    assert "**Source:** `processed/local/render.md`" in rendered
    assert "**Tickets:** PROJ-987" in rendered


def test_scan_deduplicates_overlapping_context(tmp_path):
    """Adjacent lines with different keywords should merge into one decision."""
    config = {
        "engine": {
            "decision_keywords": ["agreed", "approved"],
            "ticket_patterns": [],
            "decision_exclude_patterns": [],
            "max_decisions_per_file": 20,
        }
    }
    test_file = tmp_path / "test.md"
    test_file.write_text(
        "# Doc\n\n"
        "Some intro.\n\n"
        "The team agreed to prioritize reliability.\n"
        "Approved by product leadership.\n\n"
        "End.\n",
        encoding="utf-8",
    )

    builder = DecisionLogBuilder(config)
    decisions = builder.scan([test_file])

    # Should be 1 merged decision, not 2 separate ones.
    assert len(decisions) == 1
    assert "agreed" in decisions[0].keywords_matched
    assert "approved" in decisions[0].keywords_matched


def test_scan_excludes_historical_references(tmp_path):
    """Lines matching exclude patterns should not trigger decisions."""
    config = {
        "engine": {
            "decision_keywords": ["decided"],
            "ticket_patterns": [],
            "decision_exclude_patterns": [r"(?i)was decided in \d{4}", r"(?i)previously decided"],
            "max_decisions_per_file": 20,
        }
    }
    test_file = tmp_path / "test.md"
    test_file.write_text(
        "# Doc\n\n"
        "This was decided in 2019.\n"
        "We previously decided to use REST.\n"
        "We decided to switch to GraphQL.\n",
        encoding="utf-8",
    )

    builder = DecisionLogBuilder(config)
    decisions = builder.scan([test_file])

    # Only "We decided to switch to GraphQL." should match.
    assert len(decisions) == 1
    assert "GraphQL" in decisions[0].context


def test_scan_respects_per_file_cap(tmp_path):
    """Should cap decisions per file at max_decisions_per_file."""
    config = {
        "engine": {
            "decision_keywords": ["decided"],
            "ticket_patterns": [],
            "decision_exclude_patterns": [],
            "max_decisions_per_file": 3,
        }
    }
    # Create a file with many decisions (spaced apart to avoid dedup).
    lines = ["# Doc", ""]
    for i in range(10):
        lines.append(f"We decided thing {i}.")
        lines.extend(["", "", ""])
    test_file = tmp_path / "test.md"
    test_file.write_text("\n".join(lines), encoding="utf-8")

    builder = DecisionLogBuilder(config)
    decisions = builder.scan([test_file])

    assert len(decisions) == 3
