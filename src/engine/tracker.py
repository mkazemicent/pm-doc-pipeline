"""Track changes to processed Markdown files using Git diffs."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a detected change in a processed file."""
    filepath: Path
    change_type: str  # "added" | "modified" | "deleted"
    diff_summary: str
    tickets: list[str] = field(default_factory=list)
    timestamp: str = ""


class ChangeTracker:
    """Detect changes in the processed/ directory using GitPython."""

    def __init__(self, config: dict, project_root: Path):
        self.config = config
        self.project_root = project_root
        engine_cfg = config.get("engine", {})
        self.ticket_patterns = [
            re.compile(p) for p in engine_cfg.get("ticket_patterns", [])
        ]

    def detect_changes(self, processed_dir: Path) -> list[FileChange]:
        """Compare current processed/ state against last Git commit."""
        import git

        try:
            repo = git.Repo(self.project_root)
        except git.InvalidGitRepositoryError:
            log.warning("Not a Git repo — initializing one for change tracking.")
            repo = git.Repo.init(self.project_root)

        changes: list[FileChange] = []
        now = datetime.now(timezone.utc).isoformat()

        # Untracked files = newly added
        for fpath in repo.untracked_files:
            full_path = self.project_root / fpath
            if not str(full_path).startswith(str(processed_dir)):
                continue
            content = full_path.read_text(encoding="utf-8", errors="replace")
            tickets = self._extract_tickets(content)
            changes.append(FileChange(
                filepath=full_path,
                change_type="added",
                diff_summary=f"New file: {fpath}",
                tickets=tickets,
                timestamp=now,
            ))

        # Modified / deleted files
        if repo.head.is_valid():
            diffs = repo.head.commit.diff(None)  # diff working tree vs HEAD

            for diff in diffs:
                a_path = self.project_root / (diff.a_path or "")
                b_path = self.project_root / (diff.b_path or "")

                if not (str(a_path).startswith(str(processed_dir)) or
                        str(b_path).startswith(str(processed_dir))):
                    continue

                if diff.new_file:
                    ctype = "added"
                    fpath = b_path
                elif diff.deleted_file:
                    ctype = "deleted"
                    fpath = a_path
                else:
                    ctype = "modified"
                    fpath = b_path

                # Build diff summary
                try:
                    diff_text = diff.diff.decode("utf-8", errors="replace") if diff.diff else ""
                except Exception:
                    diff_text = ""

                summary_lines = [
                    line for line in diff_text.splitlines()[:20]
                    if line.startswith("+") or line.startswith("-")
                ]
                diff_summary = "\n".join(summary_lines) or f"File {ctype}"

                # Extract tickets from changed content
                tickets = self._extract_tickets(diff_text)
                if fpath.exists():
                    tickets.extend(self._extract_tickets(
                        fpath.read_text(encoding="utf-8", errors="replace")
                    ))
                tickets = list(set(tickets))

                changes.append(FileChange(
                    filepath=fpath,
                    change_type=ctype,
                    diff_summary=diff_summary,
                    tickets=tickets,
                    timestamp=now,
                ))

        log.info("Detected %d changes in processed files.", len(changes))
        return changes

    def _extract_tickets(self, text: str) -> list[str]:
        """Find all ticket/issue references in text."""
        found: list[str] = []
        for pattern in self.ticket_patterns:
            found.extend(pattern.findall(text))
        return list(set(found))
