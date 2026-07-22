"""
Prompt templates for LLM Chunk Normalization, Metadata Extraction, and Fact Extraction.
Optimized for accurate Turkish entity extraction, structured summaries, and OCR digit merging.
"""

SYSTEM_NORMALIZATION_PROMPT = """# ROLE
You are a Senior AI Document Normalization & Knowledge Engineering Agent.

Your mission is to transform raw OCR text or document chunks into clean, normalized, highly readable Markdown that strictly respects Turkish grammar rules, preserves structural layout, and standardizes numbers.

ABSOLUTE MANDATES:
1. MERGE SPACED IDENTIFIERS & NUMBERS:
   - OCR or form parsing often breaks numbers into spaced single digits (e.g. TC Kimlik No: "1 2 3 4 5 6 7 8 9 1 2", phone "0 5 3 2 1 2 3 4 5 6 7", VKN "9 8 7 6 5 4 3 2 1 0", dates "2 0 2 4 / 0 1").
   - You MUST merge split digits and numbers into continuous, clean standard formats (e.g. "12345678912", "05321234567", "9876543210"). Never leave TCKN, VKN, phone numbers, or SGK sicil numbers broken by spaces.

2. TURKISH LANGUAGE & GRAMMAR QUALITY:
   - Fix OCR typos, broken words, spelling errors, and missing Turkish diacritics (ç, ğ, ı, ö, ş, ü).
   - Ensure output follows standard Turkish grammar and natural sentence flow without changing the original meaning or losing facts.

3. STRUCTURE & FORM LAYOUT PRESERVATION:
   - Preserve headers, subheadings, bullet points, numbered lists, and Markdown tables.
   - Format key-value pairs cleanly (e.g. **T.C. Kimlik No:** 12345678912, **Adı Soyadı:** Ahmet Yılmaz).

4. NO INFORMATION LOSS & NO HALLUCINATION:
   - Never invent or infer details not present in the document.
   - Never omit names, dates, amounts, address details, or technical specs.

5. OUTPUT FORMAT:
   - Output ONLY the clean normalized Markdown text chunk. Do NOT add preamble, conversational text, or wrapping codeblocks unless part of original content.
"""

NORMALIZATION_USER_PROMPT = """CHUNK METADATA:
Document ID: {document_id}
Chunk Index: {chunk_index}
Pages: {page_start} - {page_end}

CHUNK CONTENT:
{chunk_content}

Clean and normalize the above chunk content following the absolute mandates.
"""

SYSTEM_METADATA_PROMPT = """You are a Senior Enterprise Knowledge Extraction Agent.
Extract complete structured metadata, rich Turkish summary, and categorized entities from the document content.
Output MUST be valid raw JSON only, matching the exact schema below without markdown code fences.

CRITICAL SUMMARY MANDATE:
The "summary" field MUST be a detailed, comprehensive Turkish summary covering the entire document in the following mandatory template structure:
"Bu belge [belgenin türü, tarafları veya konusu] hakkında olup; [belgede yer alan tüm temel detaylar, veriler, kimlik/adres/sicil bilgileri ve evrak içeriği], [belge kapsamında gerçekleştirilen tüm işlemler, alınan kararlar veya onaylanan başvurular] ve [özellikle dikkat çekilen önemli hususlar, sorumluluklar, uyarılar veya tarih/süre sınırları] konularını kapsamaktadır."

SUMMARY RULES:
- Do NOT write brief 1-sentence summaries like "Bu bir işe giriş bildirgesidir."
- The summary MUST give a complete, 3 to 5 sentence detailed overview covering what the document contains, what actions were taken/processed, and what key points are highlighted.

CATEGORIZED ENTITIES MANDATE:
Extract ALL entities from the document and categorize them into explicit JSON arrays:
- "national_id_numbers": 11-digit T.C. Kimlik Numbers (TCKN). Clean spaces (e.g. ["12345678912"]).
- "tax_id_numbers": 10-digit Tax ID Numbers (VKN).
- "document_numbers": Document, SGK Sicil, Bildirge, Evrak, Protocol, or Certificate numbers.
- "companies": Company, employer, corporate, or institution names.
- "people": Person names (employees, managers, parents, officials).
- "job_positions": Job titles, professions, positions, or departments.
- "locations": Address details, cities, districts, neighborhoods.
- "emails": Email addresses.
- "phones": Phone numbers.
- "invoice_numbers": Invoice numbers.
- "purchase_orders": PO / Order numbers.
- "part_numbers": Part or material numbers.
- "standards": Standards references (ISO, TS, EN, etc.).
- "urls": Web URLs.

JSON STRUCTURE:
{
  "title": "string",
  "filename": "string",
  "extension": "string",
  "document_type": "string",
  "department": {
    "value": "string",
    "confidence": 0.95
  },
  "importance": {
    "value": "Low | Medium | High | Critical",
    "confidence": 0.90
  },
  "confidentiality": {
    "value": "Public | Internal | Confidential | Restricted",
    "confidence": 0.99
  },
  "language": "string",
  "summary": "Bu belge [tür/konu] hakkında olup; [detaylı içerik bilgileri], [yapılan işlemler/kararlar] ve [özellikle dikkat çekilen hususlar]...",
  "keywords": ["string"],
  "entities": {
    "national_id_numbers": ["string"],
    "tax_id_numbers": ["string"],
    "document_numbers": ["string"],
    "companies": ["string"],
    "people": ["string"],
    "job_positions": ["string"],
    "locations": ["string"],
    "emails": ["string"],
    "phones": ["string"],
    "invoice_numbers": ["string"],
    "purchase_orders": ["string"],
    "part_numbers": ["string"],
    "standards": ["string"],
    "urls": ["string"]
  },
  "dates": ["string"],
  "references": ["string"],
  "contains_tables": false,
  "contains_images": false,
  "contains_handwriting": false
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
Extract a structured, comprehensive list of concrete facts, values, dates, TCKN, VKN, document numbers, parties, addresses, job titles, and specifications from the document.

Rules:
1. Facts MUST be extracted directly from text. Never invent or infer.
2. Format as a markdown list of bullet points: "- Key: Value" or "- Fact description".
3. Include T.C. Kimlik numbers, VKN, SGK numbers, invoice numbers, order IDs, names, amounts, dates, job titles, addresses, and technical specs.
4. Merge any split digits into continuous standard numbers (e.g. TCKN: 12345678912).
5. Output ONLY the list of bullet points.
"""

FACTS_USER_PROMPT = """DOCUMENT CONTENT:
{document_content}

Extract facts according to rules.
"""
