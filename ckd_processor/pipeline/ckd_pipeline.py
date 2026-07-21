"""
CKD Pipeline Orchestrator executing full end-to-end document conversion.
"""

import json
import os
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from ckd_processor.config import PipelineConfig
from ckd_processor.parsers import get_default_parser_registry
from ckd_processor.chunking import AdaptiveChunker, get_tokenizer
from ckd_processor.llm import get_llm_client, BaseLLMClient
from ckd_processor.prompts.templates import (
    SYSTEM_NORMALIZATION_PROMPT, NORMALIZATION_USER_PROMPT,
    SYSTEM_METADATA_PROMPT, METADATA_USER_PROMPT,
    SYSTEM_FACTS_PROMPT, FACTS_USER_PROMPT
)
from ckd_processor.utils.unicode_utils import rule_based_clean
from ckd_processor.utils.hash_utils import compute_file_sha256, generate_document_id
from ckd_processor.utils.logger import setup_logger
from ckd_processor.pipeline.manifest_manager import ManifestManager
from ckd_processor.pipeline.validator import QualityValidator

logger = setup_logger("CKDPipeline")


class CKDPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.output_dir = os.path.abspath(config.output_dir)
        
        # Directory layout
        self.files_dir = os.path.join(self.output_dir, "files")
        self.cache_dir = os.path.join(self.output_dir, "cache")
        self.logs_dir = os.path.join(self.output_dir, "logs")
        self.failed_dir = os.path.join(self.output_dir, "failed")
        self.temp_dir = os.path.join(self.output_dir, "temp")
        self.manifest_path = os.path.join(self.output_dir, "manifest.json")

        self._init_directories()

        self.manifest = ManifestManager(self.manifest_path)
        self.parser_registry = get_default_parser_registry(
            enable_ocr=config.parser.enable_ocr,
            ocr_lang=config.parser.ocr_language
        )
        self.tokenizer = get_tokenizer(config.chunking.tokenizer_type)
        self.chunker = AdaptiveChunker(
            target_tokens=config.chunking.target_tokens,
            overlap_tokens=config.chunking.overlap_tokens,
            tokenizer=self.tokenizer
        )
        self.llm_client: BaseLLMClient = get_llm_client(config.llm)

    def _init_directories(self) -> None:
        for d in [self.files_dir, self.cache_dir, self.logs_dir, self.failed_dir, self.temp_dir]:
            os.makedirs(d, exist_ok=True)

    def discover_files(self, input_dir: Optional[str] = None) -> List[str]:
        target_dir = os.path.abspath(input_dir or self.config.input_dir)
        supported_exts = set(e.lower() for e in self.config.parser.supported_extensions)
        discovered = []

        if not os.path.exists(target_dir):
            logger.warning(f"Input directory does not exist: {target_dir}")
            return []

        for root, _, files in os.walk(target_dir):
            for file in files:
                ext = file.split(".")[-1].lower() if "." in file else ""
                if ext in supported_exts:
                    discovered.append(os.path.join(root, file))

        logger.info(f"Discovered {len(discovered)} supported document(s) in {target_dir}")
        return discovered

    def process_file(self, filepath: str) -> bool:
        """Process a single document end-to-end into Canonical Knowledge Document format."""
        start_time = time.time()
        filename = os.path.basename(filepath)
        ext = filepath.split(".")[-1].lower() if "." in filepath else ""
        
        try:
            sha256 = compute_file_sha256(filepath)
            document_id = generate_document_id(filepath, sha256)

            # Check resume from manifest
            if self.config.resume_from_manifest and self.manifest.is_already_processed(filepath, sha256):
                logger.info(f"Skipping unchanged file (already in manifest): {filename}")
                return True

            logger.info(f"Starting processing for document: {filename} (ID: {document_id})")

            # Step 1: Parse Document
            parser = self.parser_registry.get_parser(filepath)
            if not parser:
                raise ValueError(f"No parser registered for extension .{ext}")

            parsed_doc = parser.parse(filepath)

            # Step 2: Rule-Based Cleaning on extracted text
            cleaned_text = rule_based_clean(parsed_doc.full_raw_text)
            parsed_doc.full_raw_text = cleaned_text

            # Step 3: Adaptive Chunking
            chunks = self.chunker.chunk_document(parsed_doc, document_id)
            logger.info(f"Generated {len(chunks)} adaptive chunk(s) for {filename}")

            # Step 4: LLM Chunk Normalization
            normalized_chunks = []
            for chunk in chunks:
                norm_text = self._normalize_chunk(chunk, document_id)
                normalized_chunks.append(norm_text)

            reassembled_full_text = "\n\n".join(normalized_chunks)

            # Step 5: Metadata Extraction Pass
            metadata_dict = self._extract_metadata(
                filepath=filepath,
                filename=filename,
                ext=ext,
                full_text=reassembled_full_text,
                page_count=len(parsed_doc.pages)
            )

            # Step 6: Fact Extraction Pass
            extracted_facts_text = self._extract_facts(reassembled_full_text)

            # Step 7: Format Markdown & JSON Output
            output_basename = os.path.splitext(filename)[0]
            target_md_path = os.path.join(self.files_dir, f"{output_basename}.md")
            target_json_path = os.path.join(self.files_dir, f"{output_basename}.knowledge.json")

            md_content = self._build_canonical_markdown(
                metadata_dict=metadata_dict,
                full_text=reassembled_full_text,
                facts_text=extracted_facts_text
            )

            json_data = self._build_canonical_json(
                metadata_dict=metadata_dict,
                facts_text=extracted_facts_text,
                chunks=chunks,
                document_id=document_id,
                sha256=sha256
            )

            # Step 8: Quality Validation
            is_valid_md, md_errs = QualityValidator.validate_markdown(md_content)
            is_valid_json, json_errs = QualityValidator.validate_json_metadata(metadata_dict)

            if not (is_valid_md and is_valid_json):
                err_msg = f"Validation failed: MD errors={md_errs}, JSON errors={json_errs}"
                logger.error(err_msg)
                self._isolate_failed_file(filepath, err_msg)
                self.manifest.record_failure(document_id, filepath, sha256, err_msg, self.config.llm.model_name)
                return False

            # Step 9: Write output files
            with open(target_md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            with open(target_json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Step 10: Record Success in Manifest
            self.manifest.record_success(
                document_id=document_id,
                source_file=filepath,
                output_md=target_md_path,
                output_json=target_json_path,
                sha256=sha256,
                processing_time_ms=elapsed_ms,
                model=self.config.llm.model_name,
                chunk_count=len(chunks)
            )

            logger.info(f"Successfully processed {filename} in {elapsed_ms}ms -> {target_md_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}", exc_info=True)
            self._isolate_failed_file(filepath, str(e))
            return False

    def _normalize_chunk(self, chunk, document_id: str) -> str:
        prompt = NORMALIZATION_USER_PROMPT.format(
            document_id=document_id,
            chunk_index=chunk.metadata.chunk_index,
            page_start=chunk.metadata.page_start,
            page_end=chunk.metadata.page_end,
            chunk_content=chunk.content
        )
        return self.llm_client.generate(prompt, SYSTEM_NORMALIZATION_PROMPT)

    def _extract_metadata(self, filepath: str, filename: str, ext: str, full_text: str, page_count: int) -> Dict[str, Any]:
        word_count = len(full_text.split())
        char_count = len(full_text)

        prompt = METADATA_USER_PROMPT.format(
            filename=filename,
            extension=ext,
            page_count=page_count,
            word_count=word_count,
            character_count=char_count,
            document_content=full_text[:6000]  # First 6000 chars for metadata context
        )
        resp = self.llm_client.generate(prompt, SYSTEM_METADATA_PROMPT)

        # Parse JSON from response
        try:
            # Clean markdown code block fences if present
            clean_resp = resp.strip()
            if clean_resp.startswith("```"):
                clean_resp = clean_resp.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(clean_resp)
        except Exception:
            # Fallback default metadata dict
            data = {
                "title": os.path.splitext(filename)[0],
                "filename": filename,
                "extension": ext,
                "document_type": "Document",
                "department": "General",
                "language": "auto",
                "summary": full_text[:300] + "...",
                "keywords": [],
                "entities": [],
                "confidentiality": "Internal"
            }

        # Ensure system metrics are accurate
        data["filename"] = filename
        data["extension"] = ext
        data["page_count"] = page_count
        data["word_count"] = word_count
        data["character_count"] = char_count
        return data

    def _extract_facts(self, full_text: str) -> str:
        prompt = FACTS_USER_PROMPT.format(document_content=full_text[:8000])
        return self.llm_client.generate(prompt, SYSTEM_FACTS_PROMPT)

    def _build_canonical_markdown(self, metadata_dict: Dict[str, Any], full_text: str, facts_text: str) -> str:
        yaml_frontmatter = yaml.dump(metadata_dict, default_flow_style=False, allow_unicode=True).strip()
        summary_val = metadata_dict.get("summary", "No summary available.")

        md = f"""---
{yaml_frontmatter}
processing_version: 1.0
---

# Summary

{summary_val}

# Full Text

{full_text}

# Extracted Facts

{facts_text}
"""
        return md

    def _build_canonical_json(
        self,
        metadata_dict: Dict[str, Any],
        facts_text: str,
        chunks: List[Any],
        document_id: str,
        sha256: str
    ) -> Dict[str, Any]:
        
        chunk_metas = [c.metadata.model_dump() for c in chunks]
        facts_list = [line.strip("- ").strip() for line in facts_text.split("\n") if line.strip().startswith("-")]

        result = {
            "document_id": document_id,
            "sha256": sha256,
            "metadata": metadata_dict,
            "extracted_facts": facts_list,
            "chunks": chunk_metas
        }
        return result

    def _isolate_failed_file(self, filepath: str, reason: str) -> None:
        filename = os.path.basename(filepath)
        fail_record = os.path.join(self.failed_dir, f"{filename}.error.txt")
        try:
            with open(fail_record, "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {time.ctime()}\nFile: {filepath}\nError: {reason}\n")
        except Exception as e:
            logger.error(f"Could not record failure for {filename}: {e}")

    def run_batch(self, files: Optional[List[str]] = None) -> Dict[str, int]:
        """Run batch processing across files with parallel workers."""
        target_files = files or self.discover_files()
        if not target_files:
            logger.info("No files to process.")
            return {"total": 0, "success": 0, "failed": 0}

        success_count = 0
        failed_count = 0

        logger.info(f"Starting batch pipeline run on {len(target_files)} document(s)...")

        if self.config.parallel_workers > 1:
            with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
                futures = {executor.submit(self.process_file, f): f for f in target_files}
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        success_count += 1
                    else:
                        failed_count += 1
        else:
            for f in target_files:
                if self.process_file(f):
                    success_count += 1
                else:
                    failed_count += 1

        logger.info(f"Batch completed. Total: {len(target_files)}, Success: {success_count}, Failed: {failed_count}")
        return {"total": len(target_files), "success": success_count, "failed": failed_count}
