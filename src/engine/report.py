"""Generate deterministic weekly reports from pipeline output artifacts."""

import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """Generate a deterministic weekly report from pipeline output artifacts."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate(self) -> str:
        """Read output artifacts and produce a structured markdown report."""
        context_path = self.output_dir / "PROJECT_CONTEXT.md"
        decision_path = self.output_dir / "DECISION_LOG.md"
        changelog_path = self.output_dir / "CHANGELOG.md"

        context_text = context_path.read_text(encoding="utf-8") if context_path.exists() else ""
        decision_text = decision_path.read_text(encoding="utf-8") if decision_path.exists() else ""
        changelog_text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""

        doc_count = context_text.count("- **") if context_text else 0
        decisions = [line for line in decision_text.splitlines() if line.startswith("## Decision #")]
        changes = [line for line in changelog_text.splitlines() if line.startswith("- `[")]

        tickets: list[str] = []
        in_tickets = False
        for line in context_text.splitlines():
            if line.startswith("## Ticket References"):
                in_tickets = True
                continue
            if in_tickets and line.startswith("## "):
                break
            if in_tickets and line.startswith("- "):
                tickets.append(line[2:].strip())

        source_counts: dict[str, str] = {}
        for line in context_text.splitlines():
            if line.startswith("### ") and "(" in line and "files)" in line:
                source_counts[line] = line

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        lines = [
            "---",
            f'title: "Weekly Report - {report_date}"',
            f'generated: "{now}"',
            "---",
            "",
            f"# Weekly Report - {report_date}",
            "",
            "## Summary",
            "",
            f"- **Documents in knowledge base:** {doc_count}",
            f"- **Decisions detected:** {len(decisions)}",
            f"- **Changes this period:** {len(changes)}",
            f"- **Tickets referenced:** {len(tickets)}",
            f"- **Source groups:** {len(source_counts)}",
            "",
        ]

        lines.append("## Decisions This Period")
        lines.append("")
        if decisions:
            decision_blocks: list[list[str]] = []
            current_block: list[str] = []
            for line in decision_text.splitlines():
                if line.startswith("## Decision #"):
                    if current_block:
                        decision_blocks.append(current_block)
                    current_block = [line, ""]
                    continue
                if current_block and (line.startswith("- **") or line.startswith("> ")):
                    current_block.append(line)
                elif current_block and line.strip() == "":
                    current_block.append(line)
            if current_block:
                decision_blocks.append(current_block)

            for block in decision_blocks:
                lines.extend(block)
                lines.append("")
        else:
            lines.append("_No decisions detected._")
            lines.append("")

        lines.append("## Ticket Impact")
        lines.append("")
        if tickets:
            for ticket in tickets:
                lines.append(f"- {ticket}")
            lines.append("")
        else:
            lines.append("_No ticket references found._")
            lines.append("")

        lines.append("## Change Log Highlights")
        lines.append("")
        if changes:
            for change in changes[:20]:
                lines.append(change)
            if len(changes) > 20:
                lines.append(f"- _...and {len(changes) - 20} more (see CHANGELOG.md)_")
            lines.append("")
        else:
            lines.append("_No changes detected._")
            lines.append("")

        lines.append("## Risks and Follow-Ups")
        lines.append("")
        lines.append("_Review decisions above and add manual notes here._")
        lines.append("")

        return "\n".join(lines)

    def write(self, output_path: Path | None = None) -> Path:
        """Generate report and write to file."""
        report = self.generate()
        target = output_path or (self.output_dir / "reports" / "WEEKLY_REPORT.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        log.info("Weekly report generated at %s", target)
        return target
