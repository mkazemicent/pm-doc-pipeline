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

    assert len(decisions) == 2
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
