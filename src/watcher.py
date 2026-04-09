"""Watch a directory and auto-run the pipeline when files change."""

import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt", ".html", ".htm"}


class PipelineWatcher:
    """Watch a directory for new/modified files and trigger pipeline runs."""

    def __init__(self, watch_dir: Path, config_path: Path, project_root: Path):
        self.watch_dir = watch_dir.resolve()
        self.config_path = config_path
        self.project_root = project_root
        self._known_files: dict[str, float] = {}  # path -> mtime

    def scan_once(self) -> list[Path]:
        """Scan for new or modified supported files. Returns list of changed files."""
        changed: list[Path] = []
        if not self.watch_dir.exists():
            return changed

        for filepath in self.watch_dir.iterdir():
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            key = str(filepath)
            mtime = filepath.stat().st_mtime

            if key not in self._known_files or self._known_files[key] < mtime:
                changed.append(filepath)
                self._known_files[key] = mtime

        return changed

    def run_loop(self, interval: int = 30, on_change=None):
        """Poll watch_dir every interval seconds. Calls on_change(changed_files) when files change."""
        log.info("Watching %s every %ds for changes...", self.watch_dir, interval)
        log.info("Supported: %s", ", ".join(sorted(SUPPORTED_EXTENSIONS)))
        log.info("Press Ctrl+C to stop.")

        # Initial scan to set baseline
        initial = self.scan_once()
        if initial and on_change:
            on_change(initial)

        while True:
            try:
                time.sleep(interval)
                changed = self.scan_once()
                if changed and on_change:
                    on_change(changed)
            except KeyboardInterrupt:
                log.info("Watcher stopped.")
                break
