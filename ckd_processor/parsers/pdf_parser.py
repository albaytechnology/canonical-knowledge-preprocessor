"""
PDF Document Parser converting pages directly into base64 payloads for Vision LLM (Qwen 3.6:35b) native OCR & multimodal transcription.
No external OCR dependencies (tesseract/pytesseract) used.
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


class PDFParser(BaseParser):
    def __init__(self, enable_ocr: bool = False, ocr_lang: str = "eng+tur"):
        self.enable_ocr = enable_ocr
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

                    # Render page image for Qwen Vision LLM if page contains image or text is short/missing
                    if len(text.strip()) < 30 or len(getattr(page, "images", [])) > 0:
                        logger.info(f"Rendering PDF Page {idx} in {filename} to image base64 for native Qwen Vision LLM OCR...")
                        try:
                            pil_img = page.to_image(resolution=200).original
                            buf = io.BytesIO()
                            pil_img.save(buf, format="PNG")
                            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                            base64_images.append(b64_str)
                        except Exception as render_err:
                            logger.warning(f"Image rendering failed for page {idx} in {filename}: {render_err}")

                    # If text is empty, insert placeholder so chunker passes image payload to Qwen Vision
                    if not text.strip():
                        text = f"![Scanned PDF Page {idx} ({filename})](file://{filepath})"

                    pages.append(
                        PageContent(
                            page_number=idx,
                            text=text,
                            has_images=has_images,
                            is_ocr=False
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
            raw_meta["base64_image"] = base64_images[0]

        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension="pdf",
            pages=pages,
            full_raw_text=full_text,
            raw_metadata=raw_meta
        )
