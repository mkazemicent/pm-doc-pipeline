"""Extract text from PDF files using pdfplumber or PyMuPDF."""

import re
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF files to plain text, fully offline and CPU-only."""

    def __init__(self, engine: str = "pdfplumber", strip_patterns: list[str] | None = None):
        self.engine = engine
        self.strip_patterns = [re.compile(p) for p in (strip_patterns or [])]

    def parse(self, filepath: Path) -> str:
        log.info("Parsing PDF (%s): %s", self.engine, filepath)
        if self.engine == "pdfplumber":
            return self._parse_pdfplumber(filepath)
        elif self.engine == "pymupdf":
            return self._parse_pymupdf(filepath)
        else:
            raise ValueError(f"Unknown PDF engine: {self.engine}")

    def _parse_pdfplumber(self, filepath: Path) -> str:
        import pdfplumber

        pages = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                text = self._strip(text)
                if text.strip():
                    pages.append(text)
        return "\n\n---\n\n".join(pages)

    def _parse_pymupdf(self, filepath: Path) -> str:
        import fitz  # PyMuPDF

        doc = fitz.open(filepath)
        pages = []
        for page in doc:
            text = page.get_text() or ""
            text = self._strip(text)
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n---\n\n".join(pages)

    def _strip(self, text: str) -> str:
        """Remove lines matching header/footer patterns."""
        if not self.strip_patterns:
            return text
        lines = text.splitlines()
        filtered = [
            line for line in lines
            if not any(pat.match(line.strip()) for pat in self.strip_patterns)
        ]
        return "\n".join(filtered)
