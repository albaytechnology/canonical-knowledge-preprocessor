"""
Mock / Rule-Based Client for offline testing, dry-runs, and deterministic fallback.
"""

import json
import re
from ckd_processor.llm.base import BaseLLMClient
from ckd_processor.utils.unicode_utils import rule_based_clean


from typing import Optional, List

class MockLLMClient(BaseLLMClient):
    """Fallback LLM engine simulating normalization, metadata extraction, and fact extraction."""

    def generate(self, prompt: str, system_prompt: str = "", images: Optional[List[str]] = None) -> str:
        # Detect mode cleanly based on system prompt identifier
        sp_lower = system_prompt.lower()
        if "knowledge extraction agent" in sp_lower or "json structure:" in sp_lower:
            return self._mock_metadata_response(prompt)
        elif "fact extraction agent" in sp_lower or "list of concrete" in sp_lower:
            return self._mock_facts_response(prompt)
        else:
            # Chunk normalization mode
            return self._mock_normalization_response(prompt)

    def _mock_normalization_response(self, prompt: str) -> str:
        # Strip prompt wrappers if present
        if "CHUNK CONTENT:" in prompt:
            chunk_part = prompt.split("CHUNK CONTENT:")[1]
            if "Clean and normalize the above chunk content" in chunk_part:
                chunk_part = chunk_part.split("Clean and normalize the above chunk content")[0]
            text = chunk_part.strip()
        else:
            text = prompt.strip()
        return rule_based_clean(text)

    def _mock_metadata_response(self, prompt: str) -> str:
        # Extract clean text from prompt
        if "DOCUMENT CONTENT:" in prompt:
            clean_prompt = prompt.split("DOCUMENT CONTENT:")[1].split("Return ONLY the JSON object")[0].strip()
        else:
            clean_prompt = prompt

        text = clean_prompt.lower()
        title = "Enterprise Document"
        for line in clean_prompt.split("\n"):
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        lang = "tur" if any(w in text for w in ["ve", "bir", "bu", "ile", "için", "tarafından", "fatura", "sözleşme"]) else "eng"
        doc_type = "Invoice" if "invoice" in text or "fatura" in text else ("Contract" if "contract" in text or "sözleşme" in text else "Technical Document")
        
        # Extract potential dates
        dates = re.findall(r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b", clean_prompt)
        
        # Extract codes
        codes = re.findall(r"\b[A-Z0-9]{2,10}[-/\._][A-Z0-9]{2,15}\b", clean_prompt)

        metadata = {
            "title": title,
            "document_type": doc_type,
            "department": {
                "value": "Engineering / Operations",
                "confidence": 0.95
            },
            "importance": {
                "value": "High",
                "confidence": 0.90
            },
            "confidentiality": {
                "value": "Internal",
                "confidence": 0.99
            },
            "language": lang,
            "summary": clean_prompt[:300] + "...",
            "keywords": ["enterprise", "knowledge", "rag", "canonical"],
            "entities": {
                "companies": [],
                "people": [],
                "products": [],
                "machines": [],
                "locations": [],
                "emails": re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", clean_prompt),
                "phones": [],
                "invoice_numbers": re.findall(r"\bINV-[-A-Za-z0-9]+\b", clean_prompt),
                "purchase_orders": re.findall(r"\bORD-[-A-Za-z0-9]+\b", clean_prompt),
                "part_numbers": list(set(codes)),
                "standards": [],
                "urls": re.findall(r"\b(?:https?://|www\.)\S+\b", clean_prompt)
            },
            "dates": list(set(dates)),
            "references": [],
            "contains_tables": "|" in clean_prompt,
            "contains_images": False,
            "contains_handwriting": False
        }
        return json.dumps(metadata, indent=2, ensure_ascii=False)

    def _mock_facts_response(self, prompt: str) -> str:
        if "DOCUMENT CONTENT:" in prompt:
            clean_prompt = prompt.split("DOCUMENT CONTENT:")[1].split("Extract facts according to rules")[0].strip()
        else:
            clean_prompt = prompt

        facts = []
        codes = re.findall(r"\b([A-Z0-9]{2,10}[-/\._][A-Z0-9]{2,15})\b", clean_prompt)
        for code in set(codes):
            facts.append(f"- Identifier Reference: {code}")

        amounts = re.findall(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?\s*(?:TRY|USD|EUR|TL|\$|€|₺))", clean_prompt)
        for amt in set(amounts):
            facts.append(f"- Financial Amount: {amt}")

        dates = re.findall(r"(\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b)", clean_prompt)
        for d in set(dates):
            facts.append(f"- Reference Date: {d}")

        if not facts:
            facts.append("- Document processed with 100% factual fidelity.")

        return "\n".join(facts)
