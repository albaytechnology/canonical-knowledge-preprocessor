"""
Image Document Parser (.png, .jpg, .jpeg) converting images into base64 payload for Vision LLMs (Qwen 3.6:35b).
"""

import base64
import os
from typing import List

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("ImageParser")


class ImageParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["png", "jpg", "jpeg"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        ext = filepath.split(".")[-1].lower()
        
        try:
            with open(filepath, "rb") as f:
                img_bytes = f.read()
                b64_str = base64.b64encode(img_bytes).decode("utf-8")

            text = f"![Enterprise Image ({filename})](file://{filepath})"
            page = PageContent(page_number=1, text=text, has_images=True)
            
            return ParsedDocument(
                filepath=filepath,
                filename=filename,
                extension=ext,
                pages=[page],
                full_raw_text=text,
                raw_metadata={
                    "base64_image": b64_str,
                    "image_size_bytes": len(img_bytes)
                }
            )

        except Exception as e:
            logger.error(f"Error reading image file {filename}: {e}")
            page = PageContent(page_number=1, text=f"[Image File Parse Error: {e}]", has_images=True)
            return ParsedDocument(
                filepath=filepath,
                filename=filename,
                extension=ext,
                pages=[page],
                full_raw_text=page.text
            )
