"""Harvest explicitly staged local files (Word, PowerPoint, PDF, etc.)."""

import shutil
import json
from pathlib import Path

from .base import BaseHarvester

STAGING_MANIFEST = "staging_manifest.json"


class LocalHarvester(BaseHarvester):
    """Process only files that were explicitly staged via `pm-pipeline add`.

    Instead of watching directories and ingesting everything, this harvester
    reads from a staging manifest — a simple JSON list of file paths the user
    has chosen to include. This keeps the pipeline curated and Copilot-friendly.
    """

    def __init__(self, config: dict, raw_dir: Path, project_root: Path):
        super().__init__(config, raw_dir)
        self.project_root = project_root
        self.manifest_path = project_root / "config" / STAGING_MANIFEST

    def harvest(self) -> list[Path]:
        staged = self._read_manifest()
        if not staged:
            self.log.info("No files staged. Use 'pm-pipeline add <file>' to stage files.")
            return []

        downloaded: list[Path] = []
        remaining: list[dict] = []

        for entry in staged:
            source = Path(entry["source"])
            if not source.exists():
                self.log.warning("Staged file no longer exists: %s", source)
                continue

            dest = self.raw_dir / "local" / source.name
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy if newer or not present
            if not dest.exists() or source.stat().st_mtime > dest.stat().st_mtime:
                shutil.copy2(source, dest)
                self.log.info("Staged → raw: %s", dest.name)

            downloaded.append(dest)
            remaining.append(entry)  # keep in manifest

        # Update manifest (remove entries for deleted source files)
        self._write_manifest(remaining)
        self.log.info("Local: processed %d staged files.", len(downloaded))
        return downloaded

    def stage_file(self, filepath: Path) -> dict:
        """Add a file to the staging manifest. Called by `pm-pipeline add`."""
        filepath = filepath.resolve()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        supported = {".pdf", ".docx", ".pptx", ".md", ".txt", ".html", ".htm"}
        if filepath.suffix.lower() not in supported:
            raise ValueError(f"Unsupported file type: {filepath.suffix}. Supported: {', '.join(sorted(supported))}")

        staged = self._read_manifest()

        # Check for duplicates
        existing_sources = {e["source"] for e in staged}
        if str(filepath) in existing_sources:
            return {"status": "already_staged", "file": str(filepath)}

        entry = {
            "source": str(filepath),
            "name": filepath.name,
            "staged_at": self._timestamp(),
        }
        staged.append(entry)
        self._write_manifest(staged)
        return {"status": "staged", "file": str(filepath)}

    def unstage_file(self, filepath: Path) -> dict:
        """Remove a file from the staging manifest."""
        filepath = filepath.resolve()
        staged = self._read_manifest()
        before = len(staged)
        staged = [e for e in staged if e["source"] != str(filepath)]
        self._write_manifest(staged)
        removed = before - len(staged)
        return {"status": "unstaged" if removed else "not_found", "file": str(filepath)}

    def list_staged(self) -> list[dict]:
        """Return current staging manifest."""
        return self._read_manifest()

    def _read_manifest(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, entries: list[dict]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
