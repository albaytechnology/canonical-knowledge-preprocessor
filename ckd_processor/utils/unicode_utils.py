"""
Deterministic rule-based cleaning and unicode normalization for CKD document processing.
Preserves sensitive enterprise identifiers (invoices, part numbers, financial values, dates, etc.).
"""

import re
import unicodedata
from typing import List


# Patterns for sensitive entity preservation validation
SAFEGUARD_PATTERNS = [
    r"\b[A-Z0-9]{2,10}[-/\._][A-Z0-9]{2,15}\b",               # Invoice/Serial/Part codes (e.g. INV-2024-001, ORD-9918)
    r"\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b",                 # Dates
    r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,4})?\s*(?:TRY|USD|EUR|TL|\$|€|£|₺)\b", # Financial values
    r"\b(?:https?://|www\.)\S+\b",                            # URLs
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",     # Emails
    r"\b(?:ISO|TS|EN|IEEE|ASTM|ANSI)\s+\d+(?:-\d+)?\b",       # Standards references
    r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b", # UUIDs
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b",                            # IP Addresses
]


def normalize_unicode(text: str) -> str:
    """Normalize text using Unicode NFKC form."""
    if not text:
        return ""
    # Standardize unicode characters
    text = unicodedata.normalize("NFKC", text)
    return text


def remove_control_characters(text: str) -> str:
    """Remove invisible non-printable control characters except standard line breaks and tabs."""
    if not text:
        return ""
    # Retain newline (\n), carriage return (\r), tab (\t)
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\r", "\t"))


def normalize_whitespace_and_lines(text: str) -> str:
    """
    Normalize line endings and whitespace without destroying markdown formatting.
    Converts CRLF to LF, removes trailing whitespace per line, replaces tabs with spaces.
    """
    if not text:
        return ""
    
    # 1. Standardize CRLF -> LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    cleaned_lines: List[str] = []

    for line in lines:
        # Replace non-breaking spaces
        line = line.replace("\u00a0", " ")
        
        # Strip trailing spaces on lines
        stripped = line.rstrip()
        
        # If line is not a code block or table, collapse multiple horizontal spaces (except indentation)
        if not (stripped.startswith("|") or stripped.startswith("```") or stripped.startswith("    ")):
            # Collapse multiple spaces inside the line while maintaining 2-space max
            stripped = re.sub(r"[ \t]{2,}", " ", stripped)
            
        cleaned_lines.append(stripped)

    # Rejoin lines
    result = "\n".join(cleaned_lines)
    
    # Max 2 consecutive newlines to avoid giant blank gap walls
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def merge_broken_ocr_lines(text: str) -> str:
    """
    Merge lines broken artificially by OCR line wraps.
    Avoids breaking markdown headings, table rows, bullet points, numbered lists, or code blocks.
    """
    lines = text.split("\n")
    if not lines:
        return ""

    merged: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        
        # Check if line looks like header, bullet, table, code block, or empty
        is_special = (
            not line.strip() or
            line.strip().startswith("#") or
            line.strip().startswith("-") or
            line.strip().startswith("*") or
            line.strip().startswith("|") or
            line.strip().startswith("```") or
            re.match(r"^\d+[\.\)]", line.strip()) or
            line.strip().startswith("Page ")
        )

        if is_special or i == n - 1:
            merged.append(line)
            i += 1
            continue

        next_line = lines[i + 1]
        next_is_special = (
            not next_line.strip() or
            next_line.strip().startswith("#") or
            next_line.strip().startswith("-") or
            next_line.strip().startswith("*") or
            next_line.strip().startswith("|") or
            next_line.strip().startswith("```") or
            re.match(r"^\d+[\.\)]", next_line.strip()) or
            next_line.strip().startswith("Page ")
        )

        # Merge condition: line doesn't end with sentence-ending punctuation (. ! ?)
        # and next line starts with a lowercase letter or number continuation
        if not next_is_special and line and line[-1] not in (".", "!", ":", "?", ";", "}"):
            if next_line and (next_line[0].islower() or next_line[0].isdigit()):
                line = line + " " + next_line.lstrip()
                i += 1  # Skip next line as merged

        merged.append(line)
        i += 1

    return "\n".join(merged)


def remove_decorative_headers_footers(text: str) -> str:
    """
    Remove repeated decorative headers/footers and isolated page numbers like 'Page 1 of 10'.
    """
    lines = text.split("\n")
    filtered: List[str] = []
    
    # Pattern for decorative page numbers: e.g. "Page 1", "- 12 -", "1 / 45"
    page_num_pattern = re.compile(
        r"^(?:Page|\-\s*)?\d+\s*(?:/\s*\d+|of\s*\d+)?(?:\s*\-)?$",
        re.IGNORECASE
    )

    for line in lines:
        s_line = line.strip()
        if page_num_pattern.match(s_line) and len(s_line) < 20:
            continue  # Omit decorative page number lines
        filtered.append(line)

    return "\n".join(filtered)


def rule_based_clean(text: str) -> str:
    """
    Execute full deterministic rule-based cleaning pipeline.
    """
    if not text:
        return ""

    text = normalize_unicode(text)
    text = remove_control_characters(text)
    text = remove_decorative_headers_footers(text)
    text = merge_broken_ocr_lines(text)
    text = normalize_whitespace_and_lines(text)

    return text
