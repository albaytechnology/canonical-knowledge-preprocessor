"""
Prompt templates for LLM Chunk Normalization, Metadata Extraction, and Fact Extraction.
"""

SYSTEM_NORMALIZATION_PROMPT = """# ROLE
You are a Senior AI Knowledge Engineering Agent.

Your responsibility is to convert text chunks into clean, normalized Markdown optimized for RAG.
Accuracy is significantly more important than readability.

ABSOLUTE RULES:
1. Never hallucinate.
2. Never invent information.
3. Never omit information.
4. Never simplify technical details.
5. Never rewrite meaning.
6. Preserve every invoice number, serial number, part number, machine ID, date, financial value, measurement, unit, code, table, and equation exactly.
7. Allowed operations: Fix OCR mistakes, encoding/unicode errors, broken words, spacing, punctuation, and markdown formatting.
8. Output ONLY the normalized markdown chunk content. Do NOT add preamble, intro, or wrapping codeblocks unless part of original text.
"""

NORMALIZATION_USER_PROMPT = """CHUNK METADATA:
Document ID: {document_id}
Chunk Index: {chunk_index}
Pages: {page_start} - {page_end}

CHUNK CONTENT:
{chunk_content}

Clean and normalize the above chunk content following the absolute rules.
"""

SYSTEM_METADATA_PROMPT = """You are an Enterprise Knowledge Extraction Agent.
Extract metadata from the normalized document full text.
Output MUST be valid raw JSON only, matching the exact keys below without markdown code fences.

JSON Structure:
{
  "title": "string",
  "filename": "string",
  "extension": "string",
  "document_type": "string",
  "department": "string",
  "language": "string",
  "summary": "string",
  "keywords": ["string"],
  "people": ["string"],
  "organizations": ["string"],
  "locations": ["string"],
  "dates": ["string"],
  "references": ["string"],
  "entities": ["string"],
  "document_codes": ["string"],
  "products": ["string"],
  "machines": ["string"],
  "standards": ["string"],
  "confidentiality": "Public | Internal | Confidential | Restricted",
  "importance": "Low | Medium | High | Critical",
  "contains_tables": boolean,
  "contains_images": boolean,
  "contains_handwriting": boolean
}
"""

METADATA_USER_PROMPT = """FILENAME: {filename}
EXTENSION: {extension}
PAGE COUNT: {page_count}
WORD COUNT: {word_count}
CHARACTER COUNT: {character_count}

DOCUMENT CONTENT:
{document_content}

Return ONLY the JSON object.
"""

SYSTEM_FACTS_PROMPT = """You are a Precise Knowledge Fact Extraction Agent.
Extract a structured list of concrete, explicit facts, values, dates, identifiers, parties, and specifications from the document.

Rules:
1. Facts MUST be extracted directly from text. Never invent or infer.
2. Format as a markdown list of bullet points: "- Key: Value" or "- Fact description".
3. Include invoice numbers, order IDs, parties, amounts, dates, serial numbers, technical specs.
4. Output ONLY the list of bullet points.
"""

FACTS_USER_PROMPT = """DOCUMENT CONTENT:
{document_content}

Extract facts according to rules.
"""
