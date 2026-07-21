"""
Word Document Parser (.docx, .doc) with table to markdown formatting.
"""

import os
from typing import List
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("WordParser")


class WordParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["docx", "doc"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        text_blocks: List[str] = []

        if not HAS_DOCX:
            # Fallback simple text read if docx is not installed
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text_blocks = [f.read()]
            except Exception:
                text_blocks = ["[Word Document: python-docx not installed]"]
        else:
            try:
                doc = docx.Document(filepath)
                for elem in doc.element.body:
                    # Handle paragraphs
                    if elem.tag.endswith("p"):
                        p = docx.text.paragraph.Paragraph(elem, doc)
                        if p.text.strip():
                            # Preserve heading styles if available
                            if p.style and p.style.name.startswith("Heading"):
                                level = p.style.name.replace("Heading", "").strip()
                                h_prefix = "#" * (int(level) if level.isdigit() else 2)
                                text_blocks.append(f"{h_prefix} {p.text.strip()}")
                            else:
                                text_blocks.append(p.text.strip())
                    # Handle tables
                    elif elem.tag.endswith("tbl"):
                        tbl = docx.table.Table(elem, doc)
                        md_table = self._table_to_markdown(tbl)
                        if md_table:
                            text_blocks.append(md_table)

            except Exception as e:
                logger.error(f"Error parsing Word file {filename}: {e}")
                text_blocks = [f"[Word Document Parse Error: {e}]"]

        full_text = "\n\n".join(text_blocks)
        page = PageContent(page_number=1, text=full_text)

        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension=filepath.split(".")[-1].lower(),
            pages=[page],
            full_raw_text=full_text,
            raw_metadata={"paragraph_count": len(text_blocks)}
        )

    def _table_to_markdown(self, table) -> str:
        """Convert docx table to clean Markdown table representation."""
        rows_data = []
        for row in table.rows:
            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            rows_data.append(row_cells)

        if not rows_data:
            return ""

        headers = rows_data[0]
        md_lines = ["| " + " | ".join(headers) + " |"]
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows_data[1:]:
            # Pad or truncate row to header length
            row_padded = row + [""] * (len(headers) - len(row))
            md_lines.append("| " + " | ".join(row_padded[:len(headers)]) + " |")

        return "\n".join(md_lines)
