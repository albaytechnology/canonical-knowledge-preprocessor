"""
Unit tests for rule-based deterministic text cleaning using unittest.
"""

import unittest
from ckd_processor.utils.unicode_utils import (
    normalize_unicode,
    remove_control_characters,
    normalize_whitespace_and_lines,
    merge_broken_ocr_lines,
    rule_based_clean
)


class TestCleaner(unittest.TestCase):
    def test_normalize_unicode(self):
        raw_text = "Fatura Numarası: INV-2024-001 \u00a0 Toplam: 250,000 TRY"
        clean = normalize_unicode(raw_text)
        self.assertIn("INV-2024-001", clean)
        self.assertIn("250,000 TRY", clean)

    def test_control_character_removal(self):
        raw_text = "Hello\x00World\x07!"
        clean = remove_control_characters(raw_text)
        self.assertEqual(clean, "HelloWorld!")

    def test_rule_based_clean_preserves_identifiers(self):
        text = """
        FAKTÜRA NO: INV-9988-ABC
        Tarih: 2024-01-31
        Müşteri: ACME Corp (VAT: TR1234567890)
        Tutar: 1,250,000.50 TRY
        URL: https://example.com/invoice/INV-9988-ABC
        """
        cleaned = rule_based_clean(text)
        self.assertIn("INV-9988-ABC", cleaned)
        self.assertIn("2024-01-31", cleaned)
        self.assertIn("1,250,000.50 TRY", cleaned)
        self.assertIn("https://example.com/invoice/INV-9988-ABC", cleaned)

    def test_merge_broken_ocr_lines(self):
        broken = "This is a sentence that was broken across\ntwo lines by OCR scan error."
        merged = merge_broken_ocr_lines(broken)
        self.assertIn("across two lines", merged)


if __name__ == "__main__":
    unittest.main()
