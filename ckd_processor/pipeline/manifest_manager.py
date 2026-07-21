"""
Manifest Manager for state tracking, incremental execution, and pipeline metrics.
Provides root summary and individual document provenance tracking.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ckd_processor.utils.logger import setup_logger

logger = setup_logger("ManifestManager")


class DocumentManifestEntry(BaseModel):
    document_id: str
    source_file: str
    output_markdown: str
    output_json: str
    sha256: str
    processed_at: str
    processing_time_ms: int
    model: str
    chunk_count: int
    status: str = "success"
    error_message: Optional[str] = None


class ManifestManager:
    def __init__(self, manifest_path: str = "./knowledge/manifest.json"):
        self.manifest_path = manifest_path
        self.entries: Dict[str, DocumentManifestEntry] = {}
        self.last_model_used: str = "qwen3.6:35b"
        self.load()

    def load(self) -> None:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entries_data = data.get("entries", data) if isinstance(data, dict) and "entries" in data else data
                    for k, v in entries_data.items():
                        if isinstance(v, dict) and "sha256" in v:
                            self.entries[k] = DocumentManifestEntry(**v)
                logger.info(f"Loaded manifest with {len(self.entries)} processed entries.")
            except Exception as e:
                logger.warning(f"Error loading manifest from {self.manifest_path}: {e}")

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.manifest_path)), exist_ok=True)
        try:
            total = len(self.entries)
            success = sum(1 for e in self.entries.values() if e.status == "success")
            failed = sum(1 for e in self.entries.values() if e.status == "failed")
            
            root_manifest = {
                "schema_version": "1.0",
                "ckd_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "model": self.last_model_used,
                "summary": {
                    "total_documents": total,
                    "success": success,
                    "failed": failed,
                    "total_chunks": sum(e.chunk_count for e in self.entries.values() if e.status == "success")
                },
                "entries": {k: v.model_dump() for k, v in self.entries.items()}
            }

            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(root_manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving manifest to {self.manifest_path}: {e}")

    def is_already_processed(self, filepath: str, sha256_hash: str) -> bool:
        """Check if file with same sha256 hash was successfully processed."""
        entry = self.entries.get(sha256_hash)
        if entry and entry.status == "success":
            if os.path.exists(entry.output_markdown) and os.path.exists(entry.output_json):
                return True
        return False

    def record_success(
        self,
        document_id: str,
        source_file: str,
        output_md: str,
        output_json: str,
        sha256: str,
        processing_time_ms: int,
        model: str,
        chunk_count: int
    ) -> None:
        self.last_model_used = model
        entry = DocumentManifestEntry(
            document_id=document_id,
            source_file=source_file,
            output_markdown=output_md,
            output_json=output_json,
            sha256=sha256,
            processed_at=datetime.now().isoformat(),
            processing_time_ms=processing_time_ms,
            model=model,
            chunk_count=chunk_count,
            status="success"
        )
        self.entries[sha256] = entry
        self.save()

    def record_failure(
        self,
        document_id: str,
        source_file: str,
        sha256: str,
        error_msg: str,
        model: str
    ) -> None:
        self.last_model_used = model
        entry = DocumentManifestEntry(
            document_id=document_id,
            source_file=source_file,
            output_markdown="",
            output_json="",
            sha256=sha256,
            processed_at=datetime.now().isoformat(),
            processing_time_ms=0,
            model=model,
            chunk_count=0,
            status="failed",
            error_message=error_msg
        )
        self.entries[sha256] = entry
        self.save()
