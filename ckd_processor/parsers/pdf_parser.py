"""
PDF Document Parser supporting native text extraction, page-to-image base64 rendering for Vision LLMs, and smart OCR fallback.
"""

import base64
import io
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
        base64_images: List[str] = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    has_images = len(getattr(page, "images", [])) > 0 or len(text.strip()) < 30
                    is_ocr = False

                    # Scanned page detection: text is missing or extremely short (< 30 chars)
                    if len(text.strip()) < 30:
                        logger.info(f"PDF Page {idx} in {filename} appears to be scanned image/short text. Rendering image & performing OCR...")
                        try:
                            pil_img = page.to_image(resolution=200).original
                            
                            # Convert page to PNG base64 for Vision LLMs (Qwen 3.6:35b)
                            buf = io.BytesIO()
                            pil_img.save(buf, format="PNG")
                            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                            base64_images.append(b64_str)

                            # Apply Tesseract OCR if enabled
                            if self.enable_ocr:
                                ocr_text = pytesseract.image_to_string(pil_img, lang=self.ocr_lang)
                                if len(ocr_text.strip()) > len(text.strip()):
                                    text = ocr_text
                                    is_ocr = True

                        except Exception as ocr_err:
                            logger.warning(f"Image rendering/OCR failed for page {idx} in {filename}: {ocr_err}")

                    # If text is STILL empty after OCR or page render, insert image reference placeholder
                    if not text.strip():
                        text = f"![Scanned PDF Page {idx} ({filename})](file://{filepath})"

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
            reader = PdfReader(filepath)
            pages = []
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if not text.strip():
                    text = f"![Scanned PDF Page {idx} ({filename})](file://{filepath})"
                pages.append(PageContent(page_number=idx, text=text))

        full_text = "\n\n".join([p.text for p in pages])
        raw_meta = {
            "total_pages": len(pages)
        }
        if base64_images:
            raw_meta["base64_images"] = base64_images
            raw_meta["base64_image"] = base64_images[0]  # First page image for primary vision payload

        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension="pdf",
            pages=pages,
            full_raw_text=full_text,
            raw_metadata=raw_meta
        )
