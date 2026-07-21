"""
PDF Document Parser supporting native text extraction and smart OCR fallback.
"""

import os
from typing import List
import pdfplumber
from pypdf import PdfReader

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("PDFParser")

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class PDFParser(BaseParser):
    def __init__(self, enable_ocr: bool = True, ocr_lang: str = "eng+tur"):
        self.enable_ocr = enable_ocr and HAS_OCR
        self.ocr_lang = ocr_lang

    def supported_extensions(self) -> List[str]:
        return ["pdf"]

    def parse(self, filepath: str) -> ParsedDocument:
        pages: List[PageContent] = []
        filename = os.path.basename(filepath)
        
        try:
            with pdfplumber.open(filepath) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    has_images = len(page.images) > 0
                    is_ocr = False

                    # Smart OCR Trigger: Page has < 30 chars of text but contains images
                    if self.enable_ocr and len(text.strip()) < 30 and has_images:
                        logger.info(f"PDF Page {idx} in {filename} appears to be scanned image. Applying OCR...")
                        try:
                            pil_img = page.to_image(resolution=200).original
                            ocr_text = pytesseract.image_to_string(pil_img, lang=self.ocr_lang)
                            if len(ocr_text.strip()) > len(text.strip()):
                                text = ocr_text
                                is_ocr = True
                        except Exception as ocr_err:
                            logger.warning(f"OCR failed for page {idx} in {filename}: {ocr_err}")

                    pages.append(
                        PageContent(
                            page_number=idx,
                            text=text,
                            has_images=has_images,
                            is_ocr=is_ocr
                        )
                    )
        except Exception as e:
            logger.warning(f"pdfplumber extraction encountered issue on {filename}: {e}. Fallback to PyPDF...")
            # Fallback to PyPDF if pdfplumber fails
            reader = PdfReader(filepath)
            pages = []
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append(PageContent(page_number=idx, text=text))

        full_text = "\n\n".join([p.text for p in pages])
        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension="pdf",
            pages=pages,
            full_raw_text=full_text,
            raw_metadata={"total_pages": len(pages)}
        )
