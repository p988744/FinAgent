"""
Chinese text chunking for legal documents.

Implements smart chunking that preserves:
- Document structure (sections, paragraphs)
- Semantic coherence
- Legal citations and references
"""

import re
from dataclasses import dataclass
from typing import Any

import jieba


@dataclass
class TextChunk:
    """Represents a chunk of text."""

    text: str  # Chunk content
    chunk_id: int  # Chunk number
    start_char: int  # Starting character position in document
    end_char: int  # Ending character position
    metadata: dict[str, Any]  # Additional metadata


class ChineseTextChunker:
    """Chunks Traditional Chinese text while preserving structure."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        preserve_paragraphs: bool = True,
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks for context
            preserve_paragraphs: Whether to avoid splitting paragraphs
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_paragraphs = preserve_paragraphs

        # Initialize jieba for Chinese word segmentation
        jieba.setLogLevel(jieba.logging.INFO)

    def chunk_text(self, text: str, doc_id: str = "unknown") -> list[TextChunk]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Full text to chunk
            doc_id: Document identifier for metadata

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # Normalize text
        text = self._normalize_text(text)

        if self.preserve_paragraphs:
            # Split by paragraphs first
            paragraphs = self._split_paragraphs(text)
            chunks = self._chunk_paragraphs(paragraphs, doc_id)
        else:
            # Simple sliding window chunking
            chunks = self._sliding_window_chunk(text, doc_id)

        return chunks

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for processing.

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        # Remove excessive whitespace
        text = re.sub(r"\n\n+", "\n\n", text)  # Max 2 consecutive newlines
        text = re.sub(r"  +", " ", text)  # Max 1 space

        # Normalize full-width/half-width numbers
        # Keep both for now - some legal docs use specific formats

        return text.strip()

    def _split_paragraphs(self, text: str) -> list[str]:
        """
        Split text into paragraphs.

        Preserves:
        - Section headers (第一章, 第二條, etc.)
        - Numbered lists
        - Legal citations

        Args:
            text: Full text

        Returns:
            List of paragraphs
        """
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\n+", text)

        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _chunk_paragraphs(self, paragraphs: list[str], doc_id: str) -> list[TextChunk]:
        """
        Chunk paragraphs while trying to preserve their integrity.

        Args:
            paragraphs: List of paragraphs
            doc_id: Document ID

        Returns:
            List of TextChunk objects
        """
        chunks = []
        current_chunk = []
        current_size = 0
        char_position = 0
        chunk_start = 0

        for para in paragraphs:
            para_len = len(para)

            # If single paragraph exceeds chunk size, split it
            if para_len > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(
                        TextChunk(
                            text=chunk_text,
                            chunk_id=len(chunks),
                            start_char=chunk_start,
                            end_char=chunk_start + len(chunk_text),
                            metadata={"doc_id": doc_id, "para_count": len(current_chunk)},
                        )
                    )
                    current_chunk = []
                    current_size = 0
                    chunk_start = char_position

                # Split long paragraph
                para_chunks = self._split_long_paragraph(para)
                for pc in para_chunks:
                    chunks.append(
                        TextChunk(
                            text=pc,
                            chunk_id=len(chunks),
                            start_char=char_position,
                            end_char=char_position + len(pc),
                            metadata={"doc_id": doc_id, "long_para": True},
                        )
                    )
                    char_position += len(pc) + 2  # +2 for \n\n

            # If adding paragraph would exceed chunk size
            elif current_size + para_len > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(
                        TextChunk(
                            text=chunk_text,
                            chunk_id=len(chunks),
                            start_char=chunk_start,
                            end_char=chunk_start + len(chunk_text),
                            metadata={"doc_id": doc_id, "para_count": len(current_chunk)},
                        )
                    )

                # Start new chunk with overlap
                if chunks and self.chunk_overlap > 0:
                    # Add last paragraph from previous chunk for overlap
                    overlap_para = current_chunk[-1] if current_chunk else ""
                    current_chunk = [overlap_para, para] if overlap_para else [para]
                    chunk_start = char_position - len(overlap_para) - 2
                    current_size = len(overlap_para) + para_len + 2
                else:
                    current_chunk = [para]
                    chunk_start = char_position
                    current_size = para_len

            # Add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_size += para_len + 2  # +2 for \n\n

            char_position += para_len + 2

        # Add final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    chunk_id=len(chunks),
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    metadata={"doc_id": doc_id, "para_count": len(current_chunk)},
                )
            )

        return chunks

    def _split_long_paragraph(self, para: str) -> list[str]:
        """
        Split a long paragraph into smaller chunks.

        Uses sentence boundaries when possible.

        Args:
            para: Long paragraph

        Returns:
            List of paragraph chunks
        """
        # Split on sentence boundaries (。！？)
        sentences = re.split(r"([。！？])", para)

        # Reconstruct sentences with punctuation
        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                full_sentences.append(sentences[i] + sentences[i + 1])
            else:
                full_sentences.append(sentences[i])

        # Combine sentences into chunks
        chunks = []
        current = []
        current_len = 0

        for sent in full_sentences:
            sent_len = len(sent)

            if current_len + sent_len > self.chunk_size and current:
                chunks.append("".join(current))
                current = [sent]
                current_len = sent_len
            else:
                current.append(sent)
                current_len += sent_len

        if current:
            chunks.append("".join(current))

        return chunks

    def _sliding_window_chunk(self, text: str, doc_id: str) -> list[TextChunk]:
        """
        Simple sliding window chunking (fallback method).

        Args:
            text: Full text
            doc_id: Document ID

        Returns:
            List of TextChunk objects
        """
        chunks = []
        text_len = len(text)
        start = 0
        chunk_id = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Try to end at sentence boundary
            if end < text_len:
                # Look for sentence end within last 50 chars
                search_start = max(start, end - 50)
                search_text = text[search_start:end]
                match = re.search(r"[。！？]\s*$", search_text)
                if match:
                    end = search_start + match.end()

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        chunk_id=chunk_id,
                        start_char=start,
                        end_char=end,
                        metadata={"doc_id": doc_id, "method": "sliding_window"},
                    )
                )
                chunk_id += 1

            # Move start position with overlap
            start = max(start + 1, end - self.chunk_overlap)

        return chunks

    def get_chunk_stats(self, chunks: list[TextChunk]) -> dict[str, Any]:
        """
        Get statistics about chunks.

        Args:
            chunks: List of chunks

        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {"count": 0}

        chunk_sizes = [len(c.text) for c in chunks]

        return {
            "count": len(chunks),
            "total_chars": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
        }
