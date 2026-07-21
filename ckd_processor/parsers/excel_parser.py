"""
Spreadsheet Parser (.xlsx, .xls, .csv) converting sheets into structured Markdown tables.
"""

import os
from typing import List
import pandas as pd

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("ExcelParser")


class ExcelParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["xlsx", "xls", "csv"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        ext = filepath.split(".")[-1].lower()
        pages: List[PageContent] = []
        
        try:
            if ext == "csv":
                df = pd.read_csv(filepath)
                md_table = df.to_markdown(index=False)
                pages.append(PageContent(page_number=1, text=f"### Sheet: Data\n\n{md_table}"))
            else:
                # Excel multi-sheet handling
                excel_file = pd.ExcelFile(filepath)
                for idx, sheet_name in enumerate(excel_file.sheet_names, start=1):
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    if not df.empty:
                        md_table = df.to_markdown(index=False)
                        pages.append(
                            PageContent(
                                page_number=idx,
                                text=f"### Sheet: {sheet_name}\n\n{md_table}"
                            )
                        )
        except Exception as e:
            logger.error(f"Error parsing spreadsheet {filename}: {e}")
            pages.append(PageContent(page_number=1, text=f"[Spreadsheet Parse Error: {e}]"))

        full_text = "\n\n".join([p.text for p in pages])
        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension=ext,
            pages=pages,
            full_raw_text=full_text,
            raw_metadata={"sheet_count": len(pages)}
        )
