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
        self.exclude_patterns = [
            re.compile(p) for p in engine_cfg.get("decision_exclude_patterns", [])
        ]
        self.max_per_file = engine_cfg.get("max_decisions_per_file", 20)

    def scan(self, processed_files: list[Path]) -> list[Decision]:
        """Scan files for decision-related content."""
        all_decisions: list[Decision] = []
        now = datetime.now(timezone.utc).isoformat()

        for filepath in processed_files:
            if not filepath.exists() or filepath.suffix != ".md":
                continue
            text = filepath.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()

            file_decisions: list[Decision] = []

            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                matched_kw = [kw for kw in self.keywords if kw.lower() in line_lower]
                if not matched_kw:
                    continue

                # Skip if line matches any exclude pattern
                if any(pat.search(line) for pat in self.exclude_patterns):
                    continue

                # Grab surrounding context (current line + 1 line before/after)
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 1)
                context = "\n".join(lines[start:end]).strip()

                # Merge decisions that fall inside the previous context window.
                if file_decisions and self._contexts_overlap(file_decisions[-1], line_num):
                    for kw in matched_kw:
                        if kw not in file_decisions[-1].keywords_matched:
                            file_decisions[-1].keywords_matched.append(kw)
                    continue

                # Extract ticket refs from context
                tickets: list[str] = []
                for pat in self.ticket_patterns:
                    tickets.extend(pat.findall(context))

                file_decisions.append(
                    Decision(
                        source_file=self._safe_source_file(filepath),
                        line_number=line_num,
                        context=context,
                        keywords_matched=matched_kw,
                        tickets=list(set(tickets)),
                        timestamp=now,
                    )
                )

            # Apply per-file cap
            if len(file_decisions) > self.max_per_file:
                log.warning(
                    "Capped decisions for %s: %d -> %d",
                    filepath.name,
                    len(file_decisions),
                    self.max_per_file,
                )
                file_decisions = file_decisions[:self.max_per_file]

            all_decisions.extend(file_decisions)

        log.info("Found %d decisions across %d files.", len(all_decisions), len(processed_files))
        return all_decisions

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

    @staticmethod
    def _contexts_overlap(prev_decision: Decision, current_line: int) -> bool:
        """Check if current line falls within the context window of the previous decision."""
        # Context window is line -1 to line +1 (3 lines total)
        prev_end = prev_decision.line_number + 1
        return current_line <= prev_end
