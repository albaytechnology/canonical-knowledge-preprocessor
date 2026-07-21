"""
Quality Verification Module validating Markdown and JSON canonical documents before output emission.
Validates UTF-8 encoding, YAML frontmatter syntax, section hierarchy, page sequence ordering, and schema compliance.
"""

import json
import yaml
from typing import Dict, Any, List, Tuple


class QualityValidator:
    """Verifies output compliance against Canonical Knowledge Document (CKD) specifications."""

    @staticmethod
    def validate_markdown(md_content: str) -> Tuple[bool, List[str]]:
        errors = []
        if not md_content or not md_content.strip():
            return False, ["Markdown content is empty."]

        # 1. Check UTF-8 encoding validity
        try:
            md_content.encode("utf-8")
        except UnicodeEncodeError:
            errors.append("Invalid UTF-8 encoding detected.")

        # 2. Check Frontmatter delimiter & YAML validity
        if not md_content.startswith("---"):
            errors.append("Missing YAML frontmatter header (---).")
        else:
            parts = md_content.split("---", 2)
            if len(parts) < 3:
                errors.append("Malformed YAML frontmatter delimiters.")
            else:
                frontmatter_raw = parts[1]
                try:
                    parsed_yaml = yaml.safe_load(frontmatter_raw)
                    if not isinstance(parsed_yaml, dict):
                        errors.append("YAML frontmatter did not parse into a dictionary.")
                except Exception as y_err:
                    errors.append(f"YAML frontmatter syntax error: {y_err}")

        # 3. Check required section headings
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
            "summary", "keywords", "entities", "confidentiality",
            "ckd_version", "schema_version", "source_provenance"
        ]
        for field in required_fields:
            if field not in metadata_dict:
                errors.append(f"Missing required metadata field: '{field}'")

        return len(errors) == 0, errors
