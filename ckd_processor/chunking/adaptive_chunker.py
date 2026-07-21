"""
Adaptive Chunker preserving markdown tables, code blocks, headings, and lists.
Computes token ranges, character offsets, and page boundaries.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ckd_processor.chunking.tokenizer import BaseTokenizer, get_tokenizer
from ckd_processor.parsers.base import ParsedDocument


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    page_start: int
    page_end: int
    character_start: int
    character_end: int
    token_count: int


class Chunk(BaseModel):
    metadata: ChunkMetadata
    content: str


class AdaptiveChunker:
    def __init__(
        self,
        target_tokens: int = 3000,
        overlap_tokens: int = 300,
        tokenizer: Optional[BaseTokenizer] = None
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tokenizer or get_tokenizer("word")

    def chunk_document(self, doc: ParsedDocument, document_id: str) -> List[Chunk]:
        """Split ParsedDocument into structure-aware adaptive chunks."""
        # 1. Reconstruct text with explicit page markers if multiple pages exist
        text_with_markers, page_offsets = self._build_marked_text(doc)

        # 2. Extract atomic structural blocks (tables, code blocks, lists, headers, paragraphs)
        blocks = self._parse_structural_blocks(text_with_markers)

        # 3. Assemble atomic blocks into target-sized chunks with overlap
        chunks = self._assemble_chunks(blocks, text_with_marked=text_with_markers, document_id=document_id, page_offsets=page_offsets)
        return chunks

    def _build_marked_text(self, doc: ParsedDocument) -> tuple[str, List[dict]]:
        """Combine pages into a single marked string while tracking character offsets per page."""
        full_parts = []
        page_offsets = []
        current_offset = 0

        for page in doc.pages:
            marker = f"\n\n## Page {page.page_number}\n\n" if len(doc.pages) > 1 else ""
            part = marker + page.text
            start_off = current_offset
            current_offset += len(part)
            end_off = current_offset
            
            page_offsets.append({
                "page_num": page.page_number,
                "start": start_off,
                "end": end_off
            })
            full_parts.append(part)

        return "".join(full_parts), page_offsets

    def _parse_structural_blocks(self, text: str) -> List[dict]:
        """
        Decompose text into indivisible structural blocks (Code blocks, Tables, Lists, Headings, Paragraphs).
        """
        lines = text.split("\n")
        blocks = []
        i = 0
        n = len(lines)
        char_ptr = 0

        while i < n:
            line = lines[i]
            line_len_with_nl = len(line) + (1 if i < n - 1 else 0)

            # Code Block: ```...```
            if line.strip().startswith("```"):
                code_lines = [line]
                start_char = char_ptr
                char_ptr += line_len_with_nl
                i += 1
                while i < n:
                    c_line = lines[i]
                    c_len = len(c_line) + (1 if i < n - 1 else 0)
                    code_lines.append(c_line)
                    char_ptr += c_len
                    i += 1
                    if c_line.strip().startswith("```"):
                        break
                code_str = "\n".join(code_lines)
                blocks.append({
                    "type": "code_block",
                    "text": code_str,
                    "tokens": self.tokenizer.count_tokens(code_str),
                    "start": start_char,
                    "end": char_ptr
                })
                continue

            # Markdown Table: lines starting with |
            if line.strip().startswith("|"):
                table_lines = []
                start_char = char_ptr
                while i < n and lines[i].strip().startswith("|"):
                    t_line = lines[i]
                    t_len = len(t_line) + (1 if i < n - 1 else 0)
                    table_lines.append(t_line)
                    char_ptr += t_len
                    i += 1
                table_str = "\n".join(table_lines)
                blocks.append({
                    "type": "table",
                    "text": table_str,
                    "tokens": self.tokenizer.count_tokens(table_str),
                    "start": start_char,
                    "end": char_ptr
                })
                continue

            # Heading or Page Marker
            if line.strip().startswith("#"):
                h_str = line
                blocks.append({
                    "type": "heading",
                    "text": h_str,
                    "tokens": self.tokenizer.count_tokens(h_str),
                    "start": char_ptr,
                    "end": char_ptr + line_len_with_nl
                })
                char_ptr += line_len_with_nl
                i += 1
                continue

            # Paragraph or List block (gather consecutive lines until blank line or special line)
            p_lines = []
            start_char = char_ptr
            while i < n:
                curr = lines[i]
                if not curr.strip() or curr.strip().startswith("```") or curr.strip().startswith("|") or curr.strip().startswith("#"):
                    break
                p_len = len(curr) + (1 if i < n - 1 else 0)
                p_lines.append(curr)
                char_ptr += p_len
                i += 1

            if p_lines:
                p_str = "\n".join(p_lines)
                blocks.append({
                    "type": "paragraph",
                    "text": p_str,
                    "tokens": self.tokenizer.count_tokens(p_str),
                    "start": start_char,
                    "end": char_ptr
                })
            else:
                # Blank line
                char_ptr += line_len_with_nl
                i += 1

        return blocks

    def _assemble_chunks(
        self,
        blocks: List[dict],
        text_with_marked: str,
        document_id: str,
        page_offsets: List[dict]
    ) -> List[Chunk]:
        """Combine atomic blocks into target token size chunks with overlap."""
        chunks: List[Chunk] = []
        if not blocks:
            return chunks

        chunk_index = 0
        idx = 0
        n_blocks = len(blocks)

        while idx < n_blocks:
            current_blocks = []
            current_tokens = 0
            start_block_idx = idx

            while idx < n_blocks:
                b = blocks[idx]
                # If adding block exceeds target and we already have blocks, break
                if current_tokens + b["tokens"] > self.target_tokens and current_blocks:
                    break
                current_blocks.append(b)
                current_tokens += b["tokens"]
                idx += 1

            # Build chunk text
            chunk_text = "\n\n".join([b["text"] for b in current_blocks]).strip()
            if not chunk_text:
                continue

            c_start = current_blocks[0]["start"]
            c_end = current_blocks[-1]["end"]

            # Determine page start and page end
            page_start = self._find_page_number(c_start, page_offsets)
            page_end = self._find_page_number(c_end, page_offsets)

            chunk_id = f"{document_id}_chunk_{chunk_index:03d}"
            meta = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=document_id,
                chunk_index=chunk_index,
                page_start=page_start,
                page_end=page_end,
                character_start=c_start,
                character_end=c_end,
                token_count=self.tokenizer.count_tokens(chunk_text)
            )

            chunks.append(Chunk(metadata=meta, content=chunk_text))
            chunk_index += 1

            # If we reached end of blocks, done
            if idx >= n_blocks:
                break

            # Calculate overlap: step back idx to overlap token limit
            overlap_acc = 0
            step_back = 0
            for k in range(len(current_blocks) - 1, -1, -1):
                b_k = current_blocks[k]
                overlap_acc += b_k["tokens"]
                step_back += 1
                if overlap_acc >= self.overlap_tokens:
                    break

            # Set new start index for next chunk
            idx = max(start_block_idx + 1, idx - step_back)

        return chunks

    def _find_page_number(self, char_offset: int, page_offsets: List[dict]) -> int:
        if not page_offsets:
            return 1
        for p in page_offsets:
            if p["start"] <= char_offset <= p["end"]:
                return p["page_num"]
        return page_offsets[-1]["page_num"]
