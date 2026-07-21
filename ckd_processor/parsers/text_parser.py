"""
Text Document Parser for plain text and structured text (.txt, .md, .xml, .json, .log).
"""

import os
from typing import List

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("TextParser")


class TextParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["txt", "md", "xml", "json", "log"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        ext = filepath.split(".")[-1].lower()

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if ext == "json":
                # Wrap JSON in codeblock if needed
                content = f"```json\n{content}\n```"
            elif ext == "xml":
                content = f"```xml\n{content}\n```"
            elif ext == "log":
                content = f"```log\n{content}\n```"

        except Exception as e:
            logger.error(f"Error reading text file {filename}: {e}")
            content = f"[Text Read Error: {e}]"

        page = PageContent(page_number=1, text=content)
        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension=ext,
            pages=[page],
            full_raw_text=content,
            raw_metadata={"char_count": len(content)}
        )
