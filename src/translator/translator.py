"""Universal Translator — route files to the correct parser and produce Markdown."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .pptx_parser import PptxParser
from .html_converter import HTMLToMarkdown

log = logging.getLogger(__name__)

# Map file extensions to parser types
EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".pptx": "pptx",
    ".html": "html",
    ".htm": "html",
    ".json": "json",
    ".md": "passthrough",
    ".txt": "passthrough",
    ".vtt": "vtt",
}


class UniversalTranslator:
    """Convert any supported raw file to standardized Markdown."""

    def __init__(self, config: dict, processed_dir: Path):
        self.config = config
        self.processed_dir = processed_dir
        t_cfg = config.get("translator", {})
        md_cfg = t_cfg.get("markdown", {})

        self.pdf_parser = PDFParser(
            engine=t_cfg.get("pdf_engine", "pdfplumber"),
            strip_patterns=t_cfg.get("pdf_strip_patterns", []),
        )
        self.docx_parser = DocxParser()
        self.pptx_parser = PptxParser()
        self.html_converter = HTMLToMarkdown(
            heading_style=md_cfg.get("heading_style", "ATX"),
            bullet_char=md_cfg.get("bullet_char", "-"),
            wrap_width=md_cfg.get("wrap_width", 0),
        )

    def translate(self, raw_files: list[Path]) -> list[Path]:
        """Translate a batch of raw files to Markdown. Returns output paths."""
        output_paths: list[Path] = []
        for filepath in raw_files:
            try:
                md_path = self._translate_one(filepath)
                if md_path:
                    output_paths.append(md_path)
            except Exception as exc:
                log.error("Failed to translate %s: %s", filepath, exc)
        log.info("Translated %d / %d files.", len(output_paths), len(raw_files))
        return output_paths

    def _translate_one(self, filepath: Path) -> Path | None:
        ext = filepath.suffix.lower()
        parser_type = EXTENSION_MAP.get(ext)
        if not parser_type:
            log.warning("Unsupported file type: %s", filepath)
            return None

        log.info("Translating: %s [%s]", filepath.name, parser_type)

        if parser_type == "pdf":
            body = self.pdf_parser.parse(filepath)
        elif parser_type == "docx":
            body = self.docx_parser.parse(filepath)
        elif parser_type == "pptx":
            body = self.pptx_parser.parse(filepath)
        elif parser_type == "html":
            body = self.html_converter.convert_file(filepath)
        elif parser_type == "json":
            body = self._json_to_md(filepath)
        elif parser_type == "vtt":
            body = self._vtt_to_md(filepath)
        elif parser_type == "passthrough":
            body = filepath.read_text(encoding="utf-8")
        else:
            return None

        # Write with frontmatter
        md_content = self._wrap_frontmatter(filepath, body)
        out_path = self._output_path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_content, encoding="utf-8")
        return out_path

    def _wrap_frontmatter(self, source: Path, body: str) -> str:
        """Add YAML frontmatter to the Markdown output."""
        now = datetime.now(timezone.utc).isoformat()
        # Determine source category from path
        source_type = "unknown"
        for part in source.parts:
            if part in ("confluence", "github", "webex", "local"):
                source_type = part
                break
        return (
            f"---\n"
            f"title: \"{source.stem}\"\n"
            f"source: \"{source_type}\"\n"
            f"original_file: \"{source.name}\"\n"
            f"date_harvested: \"{now}\"\n"
            f"---\n\n"
            f"{body}\n"
        )

    def _output_path(self, source: Path) -> Path:
        """Determine output path, preserving source subdirectory structure."""
        # Preserve subdirectory from raw (e.g., raw/github/repo/issues -> processed/github/repo/issues)
        raw_str = str(source)
        for marker in ("raw/confluence", "raw/github", "raw/webex", "raw/local"):
            idx = raw_str.find(marker)
            if idx != -1:
                rel = Path(raw_str[idx + 4:])  # skip "raw/"
                return self.processed_dir / rel.with_suffix(".md")

        return self.processed_dir / Path(source.name).with_suffix(".md")

    @staticmethod
    def _json_to_md(filepath: Path) -> str:
        """Convert a JSON file (e.g., GitHub issue) to readable Markdown."""
        data = json.loads(filepath.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            lines = []
            title = data.get("title", filepath.stem)
            lines.append(f"# {title}")
            lines.append("")
            for key, value in data.items():
                if key == "title":
                    continue
                if isinstance(value, list):
                    lines.append(f"**{key}:**")
                    for item in value:
                        if isinstance(item, dict):
                            summary = ", ".join(f"{k}: {v}" for k, v in item.items())
                            lines.append(f"  - {summary}")
                        else:
                            lines.append(f"  - {item}")
                else:
                    lines.append(f"**{key}:** {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = [f"# {filepath.stem}", ""]
            for item in data:
                if isinstance(item, dict):
                    summary = ", ".join(f"{k}: {v}" for k, v in item.items())
                    lines.append(f"- {summary}")
                else:
                    lines.append(f"- {item}")
            return "\n".join(lines)
        return str(data)

    @staticmethod
    def _vtt_to_md(filepath: Path) -> str:
        """Convert a WebVTT transcript to readable Markdown."""
        import re

        raw = filepath.read_text(encoding="utf-8")
        lines = raw.splitlines()
        parts: list[str] = ["# Transcript", ""]
        current_speaker = ""

        for line in lines:
            line = line.strip()
            # Skip header and blank lines
            if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                continue
            # Skip timestamp lines
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->", line):
                continue
            # Skip cue identifiers (numeric only)
            if re.match(r"^\d+$", line):
                continue
            # Detect speaker tags like "<v Speaker Name>"
            speaker_match = re.match(r"<v\s+([^>]+)>(.+)", line)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
                if speaker != current_speaker:
                    current_speaker = speaker
                    parts.append(f"\n**{speaker}:**")
                parts.append(text)
            else:
                parts.append(line)

        return "\n".join(parts)
