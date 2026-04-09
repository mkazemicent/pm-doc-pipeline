"""Convert HTML (e.g., from Confluence) to clean Markdown."""

import logging
from pathlib import Path

log = logging.getLogger(__name__)


class HTMLToMarkdown:
    """Convert HTML content to Markdown using markdownify."""

    def __init__(self, heading_style: str = "ATX", bullet_char: str = "-", wrap_width: int = 0):
        self.heading_style = heading_style
        self.bullet_char = bullet_char
        self.wrap_width = wrap_width

    def convert(self, html: str) -> str:
        from markdownify import markdownify as md

        result = md(
            html,
            heading_style=self.heading_style,
            bullets=self.bullet_char,
            wrap=self.wrap_width > 0,
            wrap_width=self.wrap_width if self.wrap_width > 0 else 80,
            strip=["script", "style"],
        )
        return self._clean(result)

    def convert_file(self, filepath: Path) -> str:
        log.info("Converting HTML: %s", filepath)
        html = filepath.read_text(encoding="utf-8")
        return self.convert(html)

    @staticmethod
    def _clean(text: str) -> str:
        """Post-process converted markdown."""
        import re

        # Collapse 3+ blank lines into 2, including whitespace-only lines
        text = re.sub(r"\n\s*\n(\s*\n)+", "\n\n", text)
        # Remove trailing whitespace on each line
        text = "\n".join(line.rstrip() for line in text.splitlines())
        return text.strip() + "\n"
