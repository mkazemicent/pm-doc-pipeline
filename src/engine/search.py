import logging
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class SearchResult:
    filepath: Path
    line_number: int
    line: str
    source_file: str  # relative name like "docs/roadmap.md"


class KnowledgeBaseSearch:
    """Search across output/ for keyword matches."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def search(self, query: str, case_sensitive: bool = False) -> list[SearchResult]:
        """Search all markdown files in output/ for the query string."""
        results: list[SearchResult] = []
        if not self.output_dir.exists():
            return results

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(query), flags)

        for filepath in sorted(self.output_dir.rglob("*.md")):
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            for line_num, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    rel = filepath.relative_to(self.output_dir)
                    results.append(
                        SearchResult(
                            filepath=filepath,
                            line_number=line_num,
                            line=line.strip(),
                            source_file=str(rel),
                        )
                    )

        return results

    def format_results(self, results: list[SearchResult], context_lines: int = 0) -> str:
        """Format search results for terminal display."""
        if not results:
            return "No matches found."

        # Group by file
        by_file: dict[str, list[SearchResult]] = {}
        for result in results:
            by_file.setdefault(result.source_file, []).append(result)

        lines: list[str] = []
        lines.append(f"Found {len(results)} match(es) across {len(by_file)} file(s):")
        lines.append("")

        for source, matches in sorted(by_file.items()):
            lines.append(f"  {source}:")
            for match in matches:
                # Truncate long lines
                display = match.line if len(match.line) <= 120 else match.line[:117] + "..."
                lines.append(f"    L{match.line_number}: {display}")
            lines.append("")

        return "\n".join(lines)
