"""
Spreadsheet Parser (.xlsx, .xls, .csv) converting sheets into clean, structured Markdown tables.
Handles multi-sheet workbooks, cell newline sanitization, and NaN cleanup.
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
                md_table = self._clean_and_convert_df(df)
                pages.append(PageContent(page_number=1, text=f"### Sheet: Data\n\n{md_table}"))
            else:
                # Excel multi-sheet handling (.xlsx, .xls)
                excel_file = pd.ExcelFile(filepath)
                for idx, sheet_name in enumerate(excel_file.sheet_names, start=1):
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    if not df.empty:
                        md_table = self._clean_and_convert_df(df)
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

    def _clean_and_convert_df(self, df: pd.DataFrame) -> str:
        """Sanitize dataframe cells and convert to pristine Markdown table."""
        # Replace NaN with empty string
        df = df.fillna("")

        # Sanitize internal newlines in cell values to maintain valid Markdown table rows
        df = df.map(lambda val: str(val).replace("\r\n", " ").replace("\n", " ").strip() if not isinstance(val, (int, float)) else val)

        try:
            return df.to_markdown(index=False)
        except Exception:
            # Fallback manual tabbed/markdown conversion if tabulate fails
            headers = [str(c) for c in df.columns]
            rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
            for _, row in df.iterrows():
                row_cells = [str(val) for val in row.values]
                rows.append("| " + " | ".join(row_cells) + " |")
            return "\n".join(rows)
