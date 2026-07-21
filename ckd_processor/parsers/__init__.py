"""
Parser package entry point and registry initializer.
"""

from ckd_processor.parsers.base import ParserRegistry
from ckd_processor.parsers.pdf_parser import PDFParser
from ckd_processor.parsers.docx_parser import WordParser
from ckd_processor.parsers.excel_parser import ExcelParser
from ckd_processor.parsers.html_parser import HTMLParser
from ckd_processor.parsers.eml_parser import EMLParser
from ckd_processor.parsers.pptx_parser import PPTXParser
from ckd_processor.parsers.text_parser import TextParser


def get_default_parser_registry(enable_ocr: bool = True, ocr_lang: str = "eng+tur") -> ParserRegistry:
    """Initialize and register default document parsers."""
    registry = ParserRegistry()
    registry.register(PDFParser(enable_ocr=enable_ocr, ocr_lang=ocr_lang))
    registry.register(WordParser())
    registry.register(ExcelParser())
    registry.register(HTMLParser())
    registry.register(EMLParser())
    registry.register(PPTXParser())
    registry.register(TextParser())
    return registry
