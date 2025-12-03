"""
Document retriever for RAG (Retrieval-Augmented Generation).
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings

from finagent.config import settings
from finagent.document_processing.embeddings import EmbeddingGenerator


@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk."""

    id: str  # Chunk ID
    text: str  # Chunk text
    score: float  # Similarity score (distance)
    metadata: dict[str, Any]  # Chunk metadata
    doc_id: str  # Source document ID


class DocumentRetriever:
    """Retrieves relevant document chunks for queries."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: str | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
    ):
        """
        Initialize document retriever.

        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory where database is persisted
            embedding_generator: EmbeddingGenerator instance
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_directory

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist yet
            self.collection = None

        # Initialize embedding generator
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

    @lru_cache(maxsize=1000)
    def _get_query_embedding(self, query: str) -> tuple[float, ...]:
        """
        Generate and cache query embedding.
        Returns tuple (hashable) for lru_cache.
        """
        embedding = self.embedding_generator.generate_embedding(query)
        return tuple(embedding)

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Query text
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"doc_id": "doc_123"})

        Returns:
            List of RetrievedChunk objects, sorted by relevance

        Raises:
            ValueError: If collection doesn't exist or is empty
        """
        if not self.collection:
            raise ValueError(f"Collection '{self.collection_name}' does not exist")

        # Check if collection is empty
        if self.collection.count() == 0:
            raise ValueError(f"Collection '{self.collection_name}' is empty")

        # Generate query embedding (cached)
        query_embedding_tuple = self._get_query_embedding(query)
        query_embedding = list(query_embedding_tuple)

        # Query Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        # Parse results
        retrieved_chunks = []

        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                chunk = RetrievedChunk(
                    id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    score=results["distances"][0][i],
                    metadata=results["metadatas"][0][i],
                    doc_id=results["metadatas"][0][i].get("doc_id", "unknown"),
                )
                retrieved_chunks.append(chunk)

        return retrieved_chunks

    def retrieve_with_scores(
        self,
        query: str,
        n_results: int = 5,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve chunks and filter by score threshold.

        Args:
            query: Query text
            n_results: Number of results
            score_threshold: Minimum similarity score (lower is better for distance)
            filters: Metadata filters

        Returns:
            List of chunks that meet the score threshold
        """
        chunks = self.retrieve(query, n_results, filters)

        if score_threshold is not None:
            chunks = [c for c in chunks if c.score <= score_threshold]

        return chunks

    def retrieve_by_document(
        self, query: str, doc_id: str, n_results: int = 5
    ) -> list[RetrievedChunk]:
        """
        Retrieve chunks only from a specific document.

        Args:
            query: Query text
            doc_id: Document ID to search within
            n_results: Number of results

        Returns:
            List of retrieved chunks from the specified document
        """
        return self.retrieve(query, n_results, filters={"doc_id": doc_id})

    def retrieve_multiquery(
        self, queries: list[str], n_results_per_query: int = 3
    ) -> list[RetrievedChunk]:
        """
        Retrieve chunks for multiple queries and combine results.

        Useful for complex queries that benefit from multiple perspectives.

        Args:
            queries: List of query variations
            n_results_per_query: Results per query

        Returns:
            Combined and deduplicated list of chunks
        """
        all_chunks = []
        seen_ids = set()

        for query in queries:
            chunks = self.retrieve(query, n_results_per_query)

            for chunk in chunks:
                if chunk.id not in seen_ids:
                    all_chunks.append(chunk)
                    seen_ids.add(chunk.id)

        # Sort by score (lower is better)
        all_chunks.sort(key=lambda c: c.score)

        return all_chunks

    def retrieve_with_concept_filtering(
        self,
        query: str,
        n_results: int = 5,
        use_concept_filtering: bool = True,
        min_confidence: float = 0.5,
    ) -> list[RetrievedChunk]:
        """
        Retrieve chunks with optional semantic concept pre-filtering.

        Two-stage retrieval:
        1. Pre-filter: Get documents matching query concepts
        2. Vector search: Search within candidate documents

        Args:
            query: Query text
            n_results: Number of results to return
            use_concept_filtering: Whether to use concept pre-filtering
            min_confidence: Minimum confidence for concept matching

        Returns:
            List of RetrievedChunk objects
        """
        if not use_concept_filtering:
            # Standard retrieval without filtering
            return self.retrieve(query, n_results)

        # Get concepts matching the query
        from finagent.document_processing.semantic_mapper import (
            get_documents_by_concepts,
            get_query_concepts_for_filtering,
        )

        concept_keys = get_query_concepts_for_filtering(query)

        if not concept_keys:
            # No concepts matched, use standard retrieval
            return self.retrieve(query, n_results)

        # Get candidate documents
        candidate_filenames = get_documents_by_concepts(concept_keys, min_confidence=min_confidence)

        if not candidate_filenames:
            # No documents match the concepts, use standard retrieval as fallback
            return self.retrieve(query, n_results)

        # Create metadata filter for Chroma
        # Chroma uses "$or" for OR logic
        filters = {"filename": {"$in": candidate_filenames}}

        # Retrieve within candidate documents
        return self.retrieve(query, n_results, filters=filters)

    def get_context_window(self, chunk_id: str, window_size: int = 1) -> list[RetrievedChunk]:
        """
        Get surrounding chunks for context.

        Args:
            chunk_id: ID of the central chunk
            window_size: Number of chunks before/after to retrieve

        Returns:
            List of chunks including the central chunk and its neighbors
        """
        # Get the chunk metadata
        result = self.collection.get(ids=[chunk_id], include=["metadatas"])

        if not result or not result["metadatas"]:
            return []

        metadata = result["metadatas"][0]
        doc_id = metadata.get("doc_id")
        chunk_num = metadata.get("chunk_id")

        if not doc_id or chunk_num is None:
            return []

        # Get all chunks from the same document
        all_chunks = self.collection.get(
            where={"doc_id": doc_id}, include=["documents", "metadatas"]
        )

        if not all_chunks or not all_chunks["ids"]:
            return []

        # Find chunks in the window
        window_chunks = []
        for i, chunk_metadata in enumerate(all_chunks["metadatas"]):
            chunk_id_val = chunk_metadata.get("chunk_id")
            if chunk_id_val is not None:
                diff = abs(chunk_id_val - chunk_num)
                if diff <= window_size:
                    window_chunks.append(
                        RetrievedChunk(
                            id=all_chunks["ids"][i],
                            text=all_chunks["documents"][i],
                            score=0.0,  # Context chunks don't have scores
                            metadata=chunk_metadata,
                            doc_id=doc_id,
                        )
                    )

        # Sort by chunk_id
        window_chunks.sort(key=lambda c: c.metadata.get("chunk_id", 0))

        return window_chunks

    def format_context(self, chunks: list[RetrievedChunk], include_metadata: bool = True) -> str:
        """
        Format retrieved chunks as context for LLM.

        Args:
            chunks: List of retrieved chunks
            include_metadata: Whether to include metadata in output

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            if include_metadata:
                # Extract key metadata
                source = chunk.metadata.get("source", "unknown")
                filename = chunk.metadata.get("filename", "unknown")

                header = f"[文件 {i}] {filename}\n來源: {source}\n相關度: {1 - chunk.score:.2%}\n"
                context_parts.append(header)

            context_parts.append(chunk.text)
            context_parts.append("\n---\n")

        return "\n".join(context_parts)

    def collection_exists(self) -> bool:
        """Check if collection exists and is not empty."""
        return self.collection is not None and self.collection.count() > 0

    def get_stats(self) -> dict[str, Any]:
        """Get retriever statistics."""
        if not self.collection:
            return {"exists": False}

        return {
            "exists": True,
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "persist_directory": self.persist_directory,
        }
