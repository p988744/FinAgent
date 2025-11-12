"""
Document indexer for Chroma vector database.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings

from finagent.document_processing.loader import Document
from finagent.document_processing.chunker import TextChunk, ChineseTextChunker
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.config import settings


class DocumentIndexer:
    """Indexes documents into Chroma vector database."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: Optional[str] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
    ):
        """
        Initialize document indexer.

        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist database (default from settings)
            embedding_generator: EmbeddingGenerator instance (creates new if None)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_directory

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Taiwan legal research documents"},
        )

        # Initialize embedding generator
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

        # Initialize chunker
        self.chunker = ChineseTextChunker(
            chunk_size=500, chunk_overlap=50, preserve_paragraphs=True
        )

    def index_document(
        self, document: Document, additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Index a single document.

        Args:
            document: Document to index
            additional_metadata: Additional metadata to add to chunks

        Returns:
            Number of chunks indexed
        """
        # Chunk the document
        chunks = self.chunker.chunk_text(document.content, doc_id=document.id)

        if not chunks:
            return 0

        # Generate embeddings for all chunks
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings_batch(chunk_texts)

        # Prepare data for Chroma
        ids = []
        documents_list = []
        metadatas = []

        for chunk, embedding in zip(chunks, embeddings):
            # Create unique chunk ID
            chunk_id = f"{document.id}_chunk_{chunk.chunk_id}"
            ids.append(chunk_id)

            # Chunk text
            documents_list.append(chunk.text)

            # Merge metadata
            metadata = {
                "doc_id": document.id,
                "chunk_id": chunk.chunk_id,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "source": document.source,
                **document.metadata,  # Include document metadata
                **chunk.metadata,  # Include chunk metadata
            }

            if additional_metadata:
                metadata.update(additional_metadata)

            # Chroma only accepts string, int, float, or bool values
            # Convert any other types to strings
            cleaned_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    cleaned_metadata[key] = value
                elif value is not None:
                    cleaned_metadata[key] = str(value)

            metadatas.append(cleaned_metadata)

        # Add to Chroma
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents_list, metadatas=metadatas)

        return len(chunks)

    def index_documents(
        self, documents: List[Document], additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Index multiple documents.

        Args:
            documents: List of documents to index
            additional_metadata: Additional metadata for all documents

        Returns:
            Total number of chunks indexed
        """
        total_chunks = 0

        for document in documents:
            chunks_added = self.index_document(document, additional_metadata)
            total_chunks += chunks_added

        return total_chunks

    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks of a document from the index.

        Args:
            doc_id: Document ID

        Returns:
            Number of chunks deleted
        """
        # Query for all chunks of this document
        results = self.collection.get(where={"doc_id": doc_id})

        if not results or not results["ids"]:
            return 0

        # Delete all chunks
        self.collection.delete(ids=results["ids"])

        return len(results["ids"])

    def clear_collection(self):
        """Clear all documents from the collection."""
        # Delete the collection and recreate it
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Taiwan legal research documents"},
        )

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection stats
        """
        count = self.collection.count()

        # Get sample of metadata to show what's indexed
        sample = self.collection.peek(limit=1)

        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": self.persist_directory,
            "sample_metadata": sample["metadatas"][0] if sample["metadatas"] else None,
        }

    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document is already indexed.

        Args:
            doc_id: Document ID

        Returns:
            True if document exists in index
        """
        results = self.collection.get(where={"doc_id": doc_id}, limit=1)

        return bool(results and results["ids"])

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.

        Args:
            doc_id: Document ID

        Returns:
            List of chunk data dictionaries
        """
        results = self.collection.get(
            where={"doc_id": doc_id}, include=["documents", "metadatas"]
        )

        if not results or not results["ids"]:
            return []

        chunks = []
        for i, chunk_id in enumerate(results["ids"]):
            chunks.append(
                {
                    "id": chunk_id,
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )

        return chunks
