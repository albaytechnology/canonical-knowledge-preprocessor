"""
HTML Parser (.html, .htm) converting web documents into clean Markdown.
"""

import os
from typing import List
import html2text
from bs4 import BeautifulSoup

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("HTMLParser")


class HTMLParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["html", "htm"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

            # Extract title if present
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string if soup.title else filename

            # Convert to markdown
            h2t = html2text.HTML2Text()
            h2t.ignore_links = False
            h2t.ignore_images = False
            h2t.body_width = 0
            md_text = h2t.handle(html_content)

        except Exception as e:
            logger.error(f"Error parsing HTML {filename}: {e}")
            md_text = f"[HTML Parse Error: {e}]"
            title = filename

        page = PageContent(page_number=1, text=md_text)
        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension=filepath.split(".")[-1].lower(),
            pages=[page],
            full_raw_text=md_text,
            raw_metadata={"title": title}
        )
