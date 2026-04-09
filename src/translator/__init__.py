from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .pptx_parser import PptxParser
from .html_converter import HTMLToMarkdown
from .translator import UniversalTranslator

__all__ = [
    "PDFParser",
    "DocxParser",
    "PptxParser",
    "HTMLToMarkdown",
    "UniversalTranslator",
]
