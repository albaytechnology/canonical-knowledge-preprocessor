"""
Unit tests for document & image parsers.
"""

import os
import tempfile
import unittest
from ckd_processor.parsers.image_parser import ImageParser
from ckd_processor.parsers.excel_parser import ExcelParser


class TestParsers(unittest.TestCase):
    def test_image_parser(self):
        # Create tiny temporary dummy image file
        temp_dir = tempfile.mkdtemp()
        try:
            img_path = os.path.join(temp_dir, "test_sample.png")
            with open(img_path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01")

            parser = ImageParser()
            self.assertTrue(parser.can_parse("png") if hasattr(parser, "can_parse") else "png" in parser.supported_extensions())
            doc = parser.parse(img_path)

            self.assertEqual(doc.filename, "test_sample.png")
            self.assertEqual(doc.extension, "png")
            self.assertTrue("base64_image" in doc.raw_metadata)
            self.assertGreater(len(doc.raw_metadata["base64_image"]), 0)
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_excel_parser_nan_handling(self):
        temp_dir = tempfile.mkdtemp()
        try:
            csv_path = os.path.join(temp_dir, "test_data.csv")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("ID,Item,Note\n1,Part A,\n2,Part B,Urgent\n")

            parser = ExcelParser()
            doc = parser.parse(csv_path)
            self.assertIn("Part A", doc.full_raw_text)
            self.assertIn("Part B", doc.full_raw_text)
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
