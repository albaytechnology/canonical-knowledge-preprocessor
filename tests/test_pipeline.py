"""
End-to-End Pipeline integration test using unittest.
"""

import os
import shutil
import tempfile
import unittest

from ckd_processor.config import PipelineConfig
from ckd_processor.pipeline import CKDPipeline


class TestPipeline(unittest.TestCase):
    def test_pipeline_end_to_end(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "knowledge")
            os.makedirs(input_dir, exist_ok=True)

            # Create sample invoice text file
            invoice_file = os.path.join(input_dir, "invoice.txt")
            with open(invoice_file, "w", encoding="utf-8") as f:
                f.write("""INVOICE # INV-2024-001
Date: 2024-01-31
Supplier: XYZ Industrial Ltd.
Customer: ABC Manufacturing Inc.

Items:
- Part # P-9912: 10 units @ 2,500 TRY = 25,000 TRY
- Part # P-8810: 2 units @ 5,000 TRY = 10,000 TRY

Total Payable: 35,000 TRY
Due Date: 2024-02-28
""")

            config = PipelineConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                parallel_workers=1
            )
            config.llm.provider = "mock"

            pipeline = CKDPipeline(config)
            results = pipeline.run_batch()

            self.assertEqual(results["total"], 1)
            self.assertEqual(results["success"], 1)

            target_md = os.path.join(output_dir, "files", "invoice.md")
            target_json = os.path.join(output_dir, "files", "invoice.knowledge.json")
            manifest_path = os.path.join(output_dir, "manifest.json")

            self.assertTrue(os.path.exists(target_md))
            self.assertTrue(os.path.exists(target_json))
            self.assertTrue(os.path.exists(manifest_path))

            with open(target_md, "r", encoding="utf-8") as f:
                md_content = f.read()
                self.assertIn("# Summary", md_content)
                self.assertIn("# Full Text", md_content)
                self.assertIn("# Extracted Facts", md_content)
                self.assertIn("INV-2024-001", md_content)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
