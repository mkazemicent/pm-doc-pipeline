"""Base harvester interface."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone


class BaseHarvester(ABC):
    """Base class for all data harvesters."""

    def __init__(self, config: dict, raw_dir: Path):
        self.config = config
        self.raw_dir = raw_dir
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def harvest(self) -> list[Path]:
        """Ingest data and return list of downloaded file paths."""

    def _write_raw(self, filename: str, content: str | bytes, subdir: str = "") -> Path:
        """Write raw content to the appropriate raw/ subdirectory."""
        target_dir = self.raw_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(target, mode, encoding=None if mode == "wb" else "utf-8") as f:
            f.write(content)
        self.log.info("Saved: %s", target)
        return target

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
