"""
Configuration management for CKD Processor using Pydantic and YAML.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field
import yaml


class LLMConfig(BaseModel):
    provider: str = Field(default="ollama", description="LLM provider: ollama, openai, or mock")
    model_name: str = Field(default="qwen3.6:35b", description="LLM model identifier")
    api_base: str = Field(default="http://172.16.10.142:11434", description="Base URL for LLM API")
    api_key: Optional[str] = Field(default=None, description="API Key if required")
    temperature: float = Field(default=0.0, description="Temperature for deterministic outputs")
    max_tokens: int = Field(default=4096, description="Max response tokens")
    timeout: int = Field(default=180, description="Timeout in seconds for LLM call")
    max_retries: int = Field(default=3, description="Max retries for failed LLM calls")


class ChunkingConfig(BaseModel):
    target_tokens: int = Field(default=3000, description="Target chunk size in tokens (2500-4000)")
    overlap_tokens: int = Field(default=300, description="Chunk overlap tokens (250-400)")
    tokenizer_type: str = Field(default="word", description="Tokenizer type: word or tiktoken")
    respect_headings: bool = Field(default=True, description="Avoid breaking markdown headings")
    respect_tables: bool = Field(default=True, description="Avoid breaking tables")
    respect_code_blocks: bool = Field(default=True, description="Avoid breaking code blocks")


class ParserConfig(BaseModel):
    enable_ocr: bool = Field(default=False, description="Local pytesseract OCR disabled; Qwen model handles OCR directly")
    ocr_language: str = Field(default="eng+tur", description="OCR language pack")
    max_file_size_mb: int = Field(default=100, description="Max file size limit in MB")
    supported_extensions: List[str] = Field(
        default_factory=lambda: [
            "pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md",
            "html", "htm", "eml", "msg", "pptx", "ppt", "xml", "json", "log"
        ]
    )


class PipelineConfig(BaseModel):
    input_dir: str = Field(default="./input_docs", description="Source directory containing documents")
    output_dir: str = Field(default="./knowledge", description="Output directory for CKD structure")
    parallel_workers: int = Field(default=4, description="Number of parallel processing workers")
    resume_from_manifest: bool = Field(default=True, description="Skip already processed unchanged files")
    cache_enabled: bool = Field(default=True, description="Enable caching for normalized chunks")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)

    @classmethod
    def load_from_yaml(cls, filepath: str) -> "PipelineConfig":
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()

    def save_to_yaml(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, allow_unicode=True)
