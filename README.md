# Canonical Knowledge Document (CKD) Preprocessor for RAG

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![RAG Pipeline](https://img.shields.io/badge/RAG-Enterprise--Grade-orange.svg)]()
[![Vision LLM](https://img.shields.io/badge/Multimodal-Qwen%203.6%3A35B-purple.svg)]()

> **Transform heterogeneous enterprise documents and images into lossless, normalized Canonical Knowledge Documents (`.md` & `.knowledge.json`) optimized for RAGFlow, LlamaIndex, GraphRAG, Elasticsearch, Weaviate, Qdrant, and Milvus.**

---

## 💡 Why Canonical Knowledge Documents (CKD)?

In enterprise Retrieval-Augmented Generation (RAG) architectures, converting documents directly into ad-hoc text chunks for a single vector database or RAG tool creates vendor lock-in and leads to significant information loss. When migrating from RAGFlow to LlamaIndex, GraphRAG, or Elasticsearch, organizations are forced to re-parse and re-extract millions of files.

The **Canonical Knowledge Document (CKD) Preprocessor** solves this by establishing a **single, deterministic, standardized source of truth**:

1. **Lossless Document & Image Normalization**: Converts raw enterprise documents and images (`.png`, `.jpeg`, `.jpg`) into uniform, clean Markdown format.
2. **Qwen 3.6:35b Vision Integration**: Native multimodal image transcription directly via Qwen 3.6:35b Vision LLM payload—no external OCR dependency required.
3. **Entity Safeguard Engine**: Invariant protection for critical business identifiers (invoice numbers, serial numbers, financial values, tax IDs, dates, URLs, code snippets, and legal clauses).
4. **Adaptive Structure-Aware Chunking**: Preserves Markdown tables, code blocks, bullet lists, and legal clauses without splitting them across boundaries.
5. **Metadata & Fact Extraction**: Produces structured `.knowledge.json` metadata alongside every `.md` file.

---

## 🏗️ System Architecture

```text
                  RAW ENTERPRISE DOCUMENTS & IMAGES
  (PDF, DOCX, XLSX, CSV, PNG, JPG, JPEG, EML, PPTX, HTML, XML, JSON, TXT, LOG)
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │      Multi-Format Parser Layer      │
                 │ (pdfplumber, pandas, Image Base64)  │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │  Deterministic Rule-Based Cleaning  │
                 │ (NFKC, Whitespace, Line Merging,    │
                 │  Entity Safeguard Protection)       │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │     Adaptive Structure Chunker      │
                 │  (2500–4000 Tokens, Overlap 250–400, │
                 │   Table/Code/List Integrity Guard)  │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │  Qwen 3.6:35B Multimodal LLM Engine │
                 │ (Vision OCR & Chunk Normalization)  │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │     Quality Verification Gate       │
                 │   (Validates UTF-8, Frontmatter,    │
                 │    Summary, Facts, JSON Schema)     │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                   CANONICAL KNOWLEDGE OUTPUT (knowledge/)
                 ├── files/
                 │   ├── invoice_2024_001.md
                 │   ├── invoice_2024_001.knowledge.json
                 │   ├── scanned_receipt.md
                 │   └── scanned_receipt.knowledge.json
                 └── manifest.json
```

---

## 📁 Output Directory Layout

The processor generates a clean, scalable output structure under `knowledge/`:

```text
knowledge/
├── files/
│   ├── invoice_2024_001.md              # Canonical Markdown file
│   ├── invoice_2024_001.knowledge.json # Full metadata & extracted facts
│   ├── diagram_spec.md
│   └── diagram_spec.knowledge.json
│
├── cache/
│   ├── normalized_chunks/
│   └── metadata/
│
├── logs/
│   └── ckd_pipeline.log                 # Structured execution logs
│
├── failed/                              # Isolated failed documents for inspection
│
├── temp/                                # Temporary workspace
│
└── manifest.json                        # Global hash tracking & metrics
```

### `manifest.json` Schema

Every processed document/image is tracked by its SHA-256 hash in `manifest.json` for **instant incremental processing** and **resume support**:

```json
{
  "70050cc3043aada0d5fec6d22b6a2a8c083b14a1310327d2afa47a5840d90f35": {
    "document_id": "doc_invoice_2024_001_txt_70050cc3043a",
    "source_file": "/workspace/input_docs/invoice_2024_001.txt",
    "output_markdown": "/workspace/knowledge/files/invoice_2024_001.md",
    "output_json": "/workspace/knowledge/files/invoice_2024_001.knowledge.json",
    "sha256": "70050cc3043aada0d5fec6d22b6a2a8c083b14a1310327d2afa47a5840d90f35",
    "processed_at": "2026-07-21T14:28:36.744120",
    "processing_time_ms": 7,
    "model": "qwen3.6:35b",
    "chunk_count": 1,
    "status": "success",
    "error_message": null
  }
}
```

---

## ⚡ Quick Start

### 1. Installation

Clone the repository and install requirements:

```bash
git clone https://github.com/albaytechnology/canonical-knowledge-preprocessor.git
cd canonical-knowledge-preprocessor

pip install -r requirements.txt
```

### 2. Initialize Configuration & Directories

Initialize the default `config.yaml` and `./input_docs` directory:

```bash
python main.py init
```

### 3. Run Preprocessing Pipeline

Place your documents and images (`.png`, `.jpeg`, `.jpg`) inside `./input_docs/` and execute:

```bash
# Run using default Ollama Qwen 3.6:35b (http://172.16.10.142:11434)
python main.py process

# Run with Mock / Offline engine for rapid dry-run testing
python main.py process --provider mock

# Process custom input folder with 8 parallel thread workers
python main.py process --input /path/to/enterprise_docs --workers 8
```

### 4. Inspect Manifest & Status Summary

View real-time conversion statistics:

```bash
python main.py status
```

---

## 🛠️ Supported Formats & Parser Registry

The pipeline features an extensible **Parser Registry Architecture** (`BaseParser` abstraction):

| Format Category | Supported Extensions | Parser Engine |
| :--- | :--- | :--- |
| **Images (Vision)** | `.png`, `.jpg`, `.jpeg` | `ImageParser` + Base64 Vision Payload to **Qwen 3.6:35B** |
| **PDF Documents** | `.pdf` | `pdfplumber` + PyPDF |
| **Word Documents** | `.docx`, `.doc` | `python-docx` (Preserves headings & table structure) |
| **Spreadsheets** | `.xlsx`, `.xls`, `.csv` | `pandas` + `openpyxl` (Converts sheets into clean Markdown tables) |
| **Web & Markup** | `.html`, `.htm` | `html2text` + `BeautifulSoup4` |
| **Email Communications** | `.eml`, `.msg` | Python `email` standard library (Extracts headers & body) |
| **Presentations** | `.pptx`, `.ppt` | `python-pptx` (Extracts slide titles & body shapes) |
| **Plain & Structured Text** | `.txt`, `.md`, `.xml`, `.json`, `.log` | Native UTF-8 streaming parser |

---

## ⚙️ Configuration (`config.yaml`)

Customize pipeline options in `config.yaml`:

```yaml
input_dir: "./input_docs"
output_dir: "./knowledge"
parallel_workers: 4
resume_from_manifest: true
cache_enabled: true

llm:
  provider: "ollama" # Options: ollama, openai, mock
  model_name: "qwen3.6:35b"
  api_base: "http://172.16.10.142:11434"
  api_key: null
  temperature: 0.0
  max_tokens: 4096
  timeout: 180
  max_retries: 3

chunking:
  target_tokens: 3000
  overlap_tokens: 300
  tokenizer_type: "word" # Options: word, tiktoken

parser:
  enable_ocr: false # Qwen 3.6:35b handles vision OCR directly
  max_file_size_mb: 100
  supported_extensions:
    - pdf
    - docx
    - doc
    - xlsx
    - xls
    - csv
    - txt
    - md
    - html
    - htm
    - eml
    - msg
    - pptx
    - ppt
    - xml
    - json
    - log
    - png
    - jpg
    - jpeg
```

---

## 🧪 Testing

Run the automated test suite:

```bash
python3 -m unittest discover -s tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed for **[Albay Technology](https://github.com/albaytechnology)** Enterprise AI Solutions.
