"""
Hash utilities for computing file SHA256 checksums and generating deterministic document identifiers.
"""

import hashlib
import os


def compute_file_sha256(filepath: str, chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of a file using streaming chunks."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_string_sha256(text: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_document_id(filepath: str, sha256_hash: Optional[str] = None) -> str:
    """Generate a unique deterministic document ID based on relative path and file hash."""
    if sha256_hash is None:
        sha256_hash = compute_file_sha256(filepath)
    basename = os.path.basename(filepath)
    short_hash = sha256_hash[:12]
    clean_name = "".join([c if c.isalnum() else "_" for c in basename])
    return f"doc_{clean_name}_{short_hash}"
