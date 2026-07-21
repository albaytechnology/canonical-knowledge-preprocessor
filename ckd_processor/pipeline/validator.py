"""
Quality Verification Module validating Markdown and JSON canonical documents before output emission.
"""

import json
from typing import Dict, Any, List, Tuple


class QualityValidator:
    """Verifies output compliance against Canonical Knowledge Document (CKD) specifications."""

    @staticmethod
    def validate_markdown(md_content: str) -> Tuple[bool, List[str]]:
        errors = []
        if not md_content or not md_content.strip():
            return False, ["Markdown content is empty."]

        # Check UTF-8 encoding validity
        try:
            md_content.encode("utf-8")
        except UnicodeEncodeError:
            errors.append("Invalid UTF-8 encoding detected.")

        # Check frontmatter delimiter
        if not md_content.startswith("---"):
            errors.append("Missing YAML frontmatter header (---).")

        # Check required section headings
        if "# Summary" not in md_content:
            errors.append("Missing '# Summary' section.")
        if "# Full Text" not in md_content:
            errors.append("Missing '# Full Text' section.")
        if "# Extracted Facts" not in md_content:
            errors.append("Missing '# Extracted Facts' section.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_json_metadata(metadata_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        required_fields = [
            "title", "filename", "extension", "document_type",
            "summary", "keywords", "entities", "confidentiality"
        ]
        for field in required_fields:
            if field not in metadata_dict:
                errors.append(f"Missing required metadata field: '{field}'")

        return len(errors) == 0, errors
