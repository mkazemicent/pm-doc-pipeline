"""Extract text from PowerPoint (.pptx) files."""

import logging
from pathlib import Path

log = logging.getLogger(__name__)


class PptxParser:
    """Parse .pptx slides into Markdown using python-pptx."""

    def parse(self, filepath: Path) -> str:
        from pptx import Presentation

        log.info("Parsing PPTX: %s", filepath)
        prs = Presentation(str(filepath))
        slides_md: list[str] = []

        for slide_num, slide in enumerate(prs.slides, 1):
            parts: list[str] = [f"## Slide {slide_num}"]

            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            # First paragraph in a shape is often the title
                            if para.level == 0 and shape.shape_id == slide.shapes[0].shape_id:
                                parts.append(f"### {text}")
                            elif para.level > 0:
                                indent = "  " * (para.level - 1)
                                parts.append(f"{indent}- {text}")
                            else:
                                parts.append(text)

                if shape.has_table:
                    table = shape.table
                    for row_idx, row in enumerate(table.rows):
                        cells = [cell.text.strip().replace("|", "\\|") for cell in row.cells]
                        parts.append("| " + " | ".join(cells) + " |")
                        if row_idx == 0:
                            parts.append("| " + " | ".join(["---"] * len(cells)) + " |")

            slides_md.append("\n".join(parts))

        return "\n\n---\n\n".join(slides_md)
