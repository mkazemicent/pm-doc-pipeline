"""Organize processed Markdown into a flat, Copilot-friendly workspace."""

import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


class Publisher:
    """Copy processed files into a flat output/ directory.

    Design principle: fewer directories = easier for Copilot to find things.
    Instead of deeply nested output, we use a flat structure:

      output/
        PROJECT_CONTEXT.md      ← Copilot's primary file (always open this)
        DECISION_LOG.md         ← All extracted decisions
        CHANGELOG.md            ← What changed this run
        docs/                   ← All processed documents (flat)
        catalogs/               ← Confluence/GitHub metadata indexes
    """

    def __init__(self, config: dict, output_dir: Path):
        self.config = config
        self.output_dir = output_dir

    def publish(
        self,
        processed_files: list[Path],
        decision_log: str,
        changelog: str,
    ) -> Path:
        """Publish everything to the output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        docs_dir = self.output_dir / "docs"
        catalogs_dir = self.output_dir / "catalogs"
        docs_dir.mkdir(exist_ok=True)
        catalogs_dir.mkdir(exist_ok=True)

        published_count = 0
        for filepath in processed_files:
            if not filepath.exists():
                continue

            # Route catalogs vs regular docs
            if "catalog" in filepath.name.lower():
                dest = catalogs_dir / filepath.name
            else:
                dest = docs_dir / filepath.name

            # Handle name collisions by prefixing source type
            if dest.exists():
                source_prefix = self._detect_source(filepath)
                dest = dest.parent / f"{source_prefix}_{dest.name}"

            shutil.copy2(filepath, dest)
            published_count += 1

        # Write decision log at top level
        dec_path = self.output_dir / "DECISION_LOG.md"
        dec_path.write_text(decision_log, encoding="utf-8")

        # Write changelog at top level
        cl_path = self.output_dir / "CHANGELOG.md"
        cl_path.write_text(changelog, encoding="utf-8")

        log.info("Published %d files to %s", published_count, self.output_dir)
        return self.output_dir

    @staticmethod
    def _detect_source(filepath: Path) -> str:
        for marker in ("confluence", "github", "webex", "local"):
            if marker in str(filepath):
                return marker
        return "doc"
