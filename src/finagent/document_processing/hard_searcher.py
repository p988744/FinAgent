"""Hard Search - Grep-based document search for exact keyword matching."""

import json
import logging
import sqlite3
from pathlib import Path

from finagent.document_processing.retriever import RetrievedChunk

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONTEXT_LINES = 3
DEFAULT_MAX_RESULTS = 10
MAX_FILE_SIZE_MB = 10
MAX_MATCHES_PER_FILE = 5


class HardSearcher:
    """
    Grep-based file searcher for exact keyword matching.

    Complements vector search by finding documents with exact keyword matches,
    reading files directly from disk and extracting context around matches.
    """

    def __init__(self, db_path: str = "data/finagent.db"):
        """
        Initialize hard searcher with database connection.

        Args:
            db_path: Path to SQLite database with document metadata
        """
        self.db_path = db_path

    def search(
        self,
        keywords: list[str],
        max_results: int = DEFAULT_MAX_RESULTS,
        context_lines: int = DEFAULT_CONTEXT_LINES,
    ) -> list[RetrievedChunk]:
        """
        Search for exact keyword matches in indexed documents.

        Args:
            keywords: Must-have keywords to search for (OR logic)
            max_results: Maximum number of chunks to return
            context_lines: Number of lines before/after match to include

        Returns:
            List of RetrievedChunk objects with matches, sorted by relevance
        """
        logger.info(f"Hard search for keywords: {keywords}")

        # Get indexed documents from database
        documents = self._get_indexed_documents()
        logger.info(f"Searching {len(documents)} indexed documents")

        # Search all documents
        all_matches = []
        for doc in documents:
            try:
                matches = self._search_file(
                    file_path=doc["file_path"],
                    filename=doc["filename"],
                    doc_metadata=doc,
                    keywords=keywords,
                    context_lines=context_lines,
                )
                all_matches.extend(matches)

            except Exception as e:
                logger.warning(f"Error searching {doc['filename']}: {e}")
                continue

        logger.info(f"Hard search found {len(all_matches)} total matches")

        # Convert to chunks and return top N
        chunks = self._convert_to_chunks(all_matches, max_results)
        return chunks

    def _get_indexed_documents(self) -> list[dict]:
        """
        Get all indexed documents from database.

        Returns:
            List of document dictionaries with metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    filename,
                    file_path,
                    document_type,
                    issuing_authority,
                    document_date,
                    related_institutions,
                    violation_types
                FROM documents
                WHERE indexed = 1
                ORDER BY document_date DESC
                """
            )

            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "filename": row["filename"],
                    "file_path": row["file_path"],
                    "document_type": row["document_type"],
                    "issuing_authority": row["issuing_authority"],
                    "document_date": row["document_date"],
                    "related_institutions": row["related_institutions"],
                    "violation_types": row["violation_types"],
                })

            conn.close()
            return documents

        except Exception as e:
            logger.error(f"Error loading documents from database: {e}")
            return []

    def _search_file(
        self,
        file_path: str,
        filename: str,
        doc_metadata: dict,
        keywords: list[str],
        context_lines: int,
    ) -> list[dict]:
        """
        Search single file for keyword matches.

        Args:
            file_path: Path to file
            filename: File name
            doc_metadata: Document metadata from database
            keywords: Keywords to search for
            context_lines: Number of context lines to extract

        Returns:
            List of match dictionaries
        """
        # Check file size
        try:
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                logger.warning(f"Skipping large file {filename} ({file_size_mb:.1f}MB)")
                return []
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return []

        # Read file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try Big5 encoding (common in Taiwan)
            try:
                with open(file_path, "r", encoding="big5") as f:
                    lines = f.readlines()
            except Exception as e:
                logger.error(f"Cannot decode file {filename}: {e}")
                return []
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            return []

        # Search for keywords
        matches = []
        for line_num, line in enumerate(lines):
            # Check if any keyword is in this line
            for keyword in keywords:
                if keyword in line:
                    # Extract context
                    context = self._extract_context(lines, line_num, context_lines)

                    matches.append({
                        "file_path": file_path,
                        "filename": filename,
                        "line_num": line_num + 1,  # 1-indexed for humans
                        "keyword": keyword,
                        "line_text": line.strip(),
                        "context": context,
                        "doc_metadata": doc_metadata,
                    })

                    # Limit matches per file
                    if len(matches) >= MAX_MATCHES_PER_FILE:
                        return matches

        return matches

    def _extract_context(
        self,
        lines: list[str],
        match_line_num: int,
        context_lines: int,
    ) -> str:
        """
        Extract context around match line.

        Args:
            lines: All lines in file
            match_line_num: Line number of match (0-indexed)
            context_lines: Number of lines before/after to include

        Returns:
            Context text as string
        """
        start = max(0, match_line_num - context_lines)
        end = min(len(lines), match_line_num + context_lines + 1)

        context_lines_list = lines[start:end]
        context = "".join(context_lines_list).strip()

        return context

    def _convert_to_chunks(
        self,
        matches: list[dict],
        max_results: int,
    ) -> list[RetrievedChunk]:
        """
        Convert raw matches to RetrievedChunk format.

        Args:
            matches: List of match dictionaries
            max_results: Maximum number of chunks to return

        Returns:
            List of RetrievedChunk objects
        """
        chunks = []

        # Score matches
        # Higher score = more keywords matched + earlier in document
        for match in matches:
            # Base score: 0.95 (hard search = high confidence)
            score = 0.95

            # Boost if multiple keywords in same context
            keywords_in_context = sum(
                1 for kw in [match["keyword"]] if kw in match["context"]
            )
            score += keywords_in_context * 0.01

            # Slight boost for earlier position in document
            position_penalty = min(0.05, match["line_num"] / 10000)
            score -= position_penalty

            # Create metadata
            metadata = {
                "filename": match["filename"],
                "file_path": match["file_path"],
                "line_num": match["line_num"],
                "matched_keyword": match["keyword"],
                "search_method": "hard_search",
            }

            # Add document metadata if available
            doc_meta = match["doc_metadata"]
            if doc_meta.get("document_type"):
                metadata["document_type"] = doc_meta["document_type"]
            if doc_meta.get("issuing_authority"):
                metadata["issuing_authority"] = doc_meta["issuing_authority"]
            if doc_meta.get("document_date"):
                metadata["document_date"] = doc_meta["document_date"]

            # Parse JSON fields
            if doc_meta.get("related_institutions"):
                try:
                    metadata["related_institutions"] = json.loads(
                        doc_meta["related_institutions"]
                    )
                except:
                    pass

            if doc_meta.get("violation_types"):
                try:
                    metadata["violation_types"] = json.loads(doc_meta["violation_types"])
                except:
                    pass

            # Create chunk
            chunk = RetrievedChunk(
                id=f"hard_{match['filename']}_{match['line_num']}",
                text=match["context"],
                score=min(1.0, score),  # Cap at 1.0
                metadata=metadata,
                doc_id=match["filename"],
            )

            chunks.append(chunk)

        # Sort by score (descending) and return top N
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:max_results]
