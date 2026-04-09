from src.engine.search import KnowledgeBaseSearch


def _create_output(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    docs_dir = output_dir / "docs"
    docs_dir.mkdir()

    (docs_dir / "roadmap.md").write_text(
        "# Roadmap\n\nWe will ship auth feature in Q3.\nTicket: PROJ-123\n",
        encoding="utf-8",
    )
    (docs_dir / "notes.md").write_text(
        "# Meeting Notes\n\nDiscussed the auth feature timeline.\nNo blockers.\n",
        encoding="utf-8",
    )
    (output_dir / "DECISION_LOG.md").write_text(
        "# Decision Log\n\n## Decision #1\n\nWe decided to use OAuth2.\n",
        encoding="utf-8",
    )
    return output_dir


def test_search_finds_keyword_across_files(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("auth feature")

    assert len(results) >= 2
    files = {result.source_file for result in results}
    assert "docs/roadmap.md" in files
    assert "docs/notes.md" in files


def test_search_finds_ticket_reference(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("PROJ-123")

    assert len(results) == 1
    assert results[0].source_file == "docs/roadmap.md"


def test_search_case_insensitive_by_default(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results_lower = searcher.search("roadmap")
    results_upper = searcher.search("ROADMAP")

    assert len(results_lower) == len(results_upper)


def test_search_case_sensitive_flag(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("ROADMAP", case_sensitive=True)

    # "ROADMAP" in uppercase doesn't appear in test data.
    assert len(results) == 0


def test_search_no_results(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("xyznonexistent")

    assert len(results) == 0


def test_search_empty_output_dir(tmp_path):
    output_dir = tmp_path / "output"
    # Intentionally do not create output_dir.
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("anything")

    assert len(results) == 0


def test_format_results_no_matches(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("xyznonexistent")
    formatted = searcher.format_results(results)

    assert "No matches found" in formatted


def test_format_results_groups_by_file(tmp_path):
    output_dir = _create_output(tmp_path)
    searcher = KnowledgeBaseSearch(output_dir)

    results = searcher.search("auth feature")
    formatted = searcher.format_results(results)

    assert "docs/roadmap.md" in formatted
    assert "docs/notes.md" in formatted
