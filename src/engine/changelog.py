"""Generate a Changelog from detected file changes."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from .tracker import FileChange

log = logging.getLogger(__name__)


class ChangelogGenerator:
    """Build a Markdown changelog from a list of FileChange objects."""

    def __init__(self, config: dict):
        cl_cfg = config.get("engine", {}).get("changelog", {})
        self.group_by = cl_cfg.get("group_by", "source")
        self.max_entries = cl_cfg.get("max_entries", 500)

    def generate(self, changes: list[FileChange]) -> str:
        """Create a changelog Markdown document."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Changelog",
            "",
            f"_Generated: {now}_",
            "",
            f"**Changes detected:** {len(changes)}",
            "",
        ]

        if not changes:
            lines.append("_No changes detected._")
            return "\n".join(lines)

        truncated = changes[: self.max_entries]

        if self.group_by == "source":
            grouped = self._group_by_source(truncated)
        elif self.group_by == "date":
            grouped = self._group_by_date(truncated)
        elif self.group_by == "ticket":
            grouped = self._group_by_ticket(truncated)
        else:
            grouped = {"All Changes": truncated}

        for group_name, group_changes in sorted(grouped.items()):
            lines.append(f"## {group_name}")
            lines.append("")
            for change in group_changes:
                icon = {"added": "+", "modified": "~", "deleted": "-"}.get(change.change_type, "?")
                ticket_str = f" [{', '.join(change.tickets)}]" if change.tickets else ""
                lines.append(f"- `[{icon}]` **{change.filepath.name}**{ticket_str}")
                if change.diff_summary and len(change.diff_summary) < 200:
                    lines.append(f"  > {change.diff_summary.splitlines()[0]}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _group_by_source(changes: list[FileChange]) -> dict[str, list[FileChange]]:
        groups: dict[str, list[FileChange]] = {}
        for c in changes:
            # Detect source from path
            source = "other"
            for marker in ("confluence", "github", "webex", "local"):
                if marker in str(c.filepath):
                    source = marker
                    break
            groups.setdefault(source, []).append(c)
        return groups

    @staticmethod
    def _group_by_date(changes: list[FileChange]) -> dict[str, list[FileChange]]:
        groups: dict[str, list[FileChange]] = {}
        for c in changes:
            date_str = c.timestamp[:10] if c.timestamp else "unknown"
            groups.setdefault(date_str, []).append(c)
        return groups

    @staticmethod
    def _group_by_ticket(changes: list[FileChange]) -> dict[str, list[FileChange]]:
        groups: dict[str, list[FileChange]] = {}
        for c in changes:
            if c.tickets:
                for ticket in c.tickets:
                    groups.setdefault(ticket, []).append(c)
            else:
                groups.setdefault("No Ticket", []).append(c)
        return groups
