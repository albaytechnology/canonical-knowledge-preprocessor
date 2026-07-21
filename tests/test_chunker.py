"""
Unit tests for adaptive chunker using unittest.
"""

import unittest
from ckd_processor.chunking.adaptive_chunker import AdaptiveChunker
from ckd_processor.parsers.base import ParsedDocument, PageContent


class TestChunker(unittest.TestCase):
    def test_chunker_does_not_split_tables(self):
        table_content = """# Document Title

Introductory text before table.

| ID | Item | Price |
|---|---|---|
| 1 | Machine Part A | 5,000 TRY |
| 2 | Machine Part B | 12,000 TRY |
| 3 | Spare Motor | 3,500 TRY |

Ending text after table.
"""
        doc = ParsedDocument(
            filepath="sample.md",
            filename="sample.md",
            extension="md",
            pages=[PageContent(page_number=1, text=table_content)],
            full_raw_text=table_content
        )

        chunker = AdaptiveChunker(target_tokens=500, overlap_tokens=50)
        chunks = chunker.chunk_document(doc, "doc_test_123")

        self.assertGreaterEqual(len(chunks), 1)
        first_chunk = chunks[0].content
        self.assertIn("| ID | Item | Price |", first_chunk)
        self.assertIn("| 3 | Spare Motor | 3,500 TRY |", first_chunk)

    def test_chunker_metadata(self):
        text = "Paragraph one text.\n\nParagraph two text."
        doc = ParsedDocument(
            filepath="sample.txt",
            filename="sample.txt",
            extension="txt",
            pages=[PageContent(page_number=1, text=text)],
            full_raw_text=text
        )
        chunker = AdaptiveChunker(target_tokens=100)
        chunks = chunker.chunk_document(doc, "doc_test_456")

        self.assertEqual(len(chunks), 1)
        meta = chunks[0].metadata
        self.assertEqual(meta.document_id, "doc_test_456")
        self.assertEqual(meta.page_start, 1)
        self.assertEqual(meta.page_end, 1)


if __name__ == "__main__":
    unittest.main()
