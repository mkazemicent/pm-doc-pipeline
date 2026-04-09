"""Build a Decision Log by scanning processed Markdown for decision keywords."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class Decision:
    """A single extracted decision."""
    source_file: str
    line_number: int
    context: str  # the sentence/paragraph containing the decision
    keywords_matched: list[str]
    tickets: list[str]
    timestamp: str


class DecisionLogBuilder:
    """Scan processed Markdown files and extract decisions based on keyword matching."""

    def __init__(self, config: dict):
        engine_cfg = config.get("engine", {})
        self.keywords = engine_cfg.get("decision_keywords", [])
        self.ticket_patterns = [
            re.compile(p) for p in engine_cfg.get("ticket_patterns", [])
        ]

    def scan(self, processed_files: list[Path]) -> list[Decision]:
        """Scan files for decision-related content."""
        decisions: list[Decision] = []
        now = datetime.now(timezone.utc).isoformat()

        for filepath in processed_files:
            if not filepath.exists() or filepath.suffix != ".md":
                continue
            text = filepath.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()

            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                matched_kw = [kw for kw in self.keywords if kw.lower() in line_lower]
                if not matched_kw:
                    continue

                # Grab surrounding context (current line + 1 line before/after)
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 1)
                context = "\n".join(lines[start:end]).strip()

                # Extract ticket refs from context
                tickets: list[str] = []
                for pat in self.ticket_patterns:
                    tickets.extend(pat.findall(context))

                decisions.append(Decision(
                    source_file=self._safe_source_file(filepath),
                    line_number=line_num,
                    context=context,
                    keywords_matched=matched_kw,
                    tickets=list(set(tickets)),
                    timestamp=now,
                ))

        log.info("Found %d decisions across %d files.", len(decisions), len(processed_files))
        return decisions

    def render(self, decisions: list[Decision]) -> str:
        """Render decisions as a Markdown document."""
        lines = [
            "# Decision Log",
            "",
            f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
            "",
            f"**Total decisions found:** {len(decisions)}",
            "",
        ]

        for i, dec in enumerate(decisions, 1):
            lines.append(f"## Decision #{i}")
            lines.append("")
            lines.append(f"- **Source:** `{dec.source_file}`  ")
            lines.append(f"- **Line:** {dec.line_number}  ")
            lines.append(f"- **Keywords:** {', '.join(dec.keywords_matched)}  ")
            if dec.tickets:
                lines.append(f"- **Tickets:** {', '.join(dec.tickets)}  ")
            lines.append("")
            lines.append("> " + dec.context.replace("\n", "\n> "))
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _safe_source_file(filepath: Path) -> str:
        """Return a non-sensitive source path for logs and reports.

        Prefers a stable repository-relative path segment rooted at `processed/`.
        Falls back to filename only when the marker is not present.
        """
        parts = filepath.parts
        if "processed" in parts:
            idx = parts.index("processed")
            return "/".join(parts[idx:])
        return filepath.name
