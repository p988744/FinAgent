"""
Document indexer for Chroma vector database.
"""

import json
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from finagent.config import settings
from finagent.database.document_db import DocumentDatabase
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.document_processing.loader import Document
from finagent.document_processing.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Indexes documents into Chroma vector database."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: str | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
        document_db: DocumentDatabase | None = None,
        extract_metadata: bool = False,
        metadata_extractor: MetadataExtractor | None = None,
    ):
        """
        Initialize document indexer.

        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist database (default from settings)
            embedding_generator: EmbeddingGenerator instance (creates new if None)
            document_db: DocumentDatabase instance (creates new if None)
            extract_metadata: Whether to extract metadata using LLM (default: False)
            metadata_extractor: MetadataExtractor instance (creates new if extract_metadata=True)
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

        # Initialize document database
        self.document_db = document_db or DocumentDatabase()

        # Initialize metadata extraction
        self.extract_metadata = extract_metadata
        if extract_metadata:
            self.metadata_extractor = metadata_extractor or MetadataExtractor(
                use_new_model=True
            )
            logger.info("Metadata extraction enabled (LLM-powered)")
        else:
            self.metadata_extractor = None
            logger.debug("Metadata extraction disabled")

    async def index_document(
        self, document: Document, additional_metadata: dict[str, Any] | None = None
    ) -> int:
        """
        Index a single document.

        Args:
            document: Document to index
            additional_metadata: Additional metadata to add to chunks

        Returns:
            Number of chunks indexed
        """
        # Extract metadata using LLM if enabled
        extracted_metadata = None
        if self.extract_metadata and self.metadata_extractor:
            try:
                logger.info(f"Extracting metadata for document: {document.id}")
                result = await self.metadata_extractor.extract_new(
                    doc_id=document.id,
                    filename=Path(document.source).name,
                    content=document.content,
                )

                if result.success and result.metadata:
                    extracted_metadata = result.metadata
                    logger.info(
                        f"Metadata extracted: confidence={extracted_metadata.extraction_confidence:.2f}, "
                        f"time={result.processing_time:.2f}s, cost=${result.llm_cost_usd:.4f}"
                    )
                else:
                    logger.warning(
                        f"Metadata extraction failed for {document.id}: {result.error}"
                    )
            except Exception as e:
                logger.error(f"Metadata extraction error for {document.id}: {e}")
                # Continue with indexing even if metadata extraction fails

        # Chunk the document
        chunks = self.chunker.chunk_text(document.content, doc_id=document.id)

        if not chunks:
            logger.warning(f"No chunks created for document: {document.id}")
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
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents_list, metadatas=metadatas
        )

        # Write to SQLite
        try:
            # Extract file path from document source
            file_path = document.source
            filename = Path(file_path).name

            # Create content preview (first 500 chars)
            content_preview = document.content[:500] if document.content else None

            # Get file size if file exists
            file_size = None
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size

            # Detect MIME type and conditionally store full_content
            # Only text files store full_content for browser display
            # Binary files (PDF, Word) will be downloaded via file_path
            mime_type = "text/plain"  # Default
            full_content = None

            if filename.endswith(".txt"):
                mime_type = "text/plain"
                full_content = document.content  # Store for browser display
            elif filename.endswith(".pdf"):
                mime_type = "application/pdf"
                # Binary file: full_content stays None, use file_path for download
            elif filename.endswith(".docx"):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.endswith(".doc"):
                mime_type = "application/msword"
            elif filename.endswith(".html") or filename.endswith(".htm"):
                mime_type = "text/html"
                full_content = document.content

            # Prepare metadata fields for database
            db_fields = {
                "doc_id": document.id,
                "filename": filename,
                "file_path": file_path,
                "content_preview": content_preview,
                "full_content": full_content,  # Only for text files
                "mime_type": mime_type,
                "file_size": file_size,
                "custom_fields": document.metadata,
            }

            # Add extracted metadata fields if available
            if extracted_metadata:
                from datetime import datetime, timezone
                db_fields.update({
                    "document_type": extracted_metadata.document_type,
                    "issuing_authority": extracted_metadata.issuing_authority,
                    "case_number": extracted_metadata.case_number,
                    "document_date": extracted_metadata.document_date,
                    "related_institutions": json.dumps(extracted_metadata.related_institutions, ensure_ascii=False),
                    "violation_types": json.dumps(extracted_metadata.violation_types, ensure_ascii=False),
                    "penalty_amount": extracted_metadata.penalty_amount,
                    "keywords": json.dumps(extracted_metadata.keywords, ensure_ascii=False),
                    "extraction_confidence": extracted_metadata.extraction_confidence,
                    "extraction_method": extracted_metadata.extraction_method,
                    # Metadata extraction status fields
                    "metadata_extracted": True,
                    "metadata_extraction_status": "completed",
                    "metadata_last_extracted_at": datetime.now(timezone.utc).isoformat(),
                    "metadata_extraction_attempts": 1,
                    # Descriptive fields
                    "title": extracted_metadata.title,
                    "description": extracted_metadata.description,
                })
                logger.debug(
                    f"Storing metadata fields: document_type={extracted_metadata.document_type}, "
                    f"confidence={extracted_metadata.extraction_confidence}"
                )
            # Fallback: Use document.metadata if available (e.g. from process command)
            elif document.metadata:
                from datetime import datetime, timezone
                
                # Helper to safely get list/dict and dump to JSON
                def get_json_field(key, default=None):
                    val = document.metadata.get(key, default)
                    if isinstance(val, (list, dict)):
                        return json.dumps(val, ensure_ascii=False)
                    return val

                # Only update if we have meaningful metadata (check for a key field)
                if "document_type" in document.metadata or "title" in document.metadata:
                    db_fields.update({
                        "document_type": document.metadata.get("document_type"),
                        "issuing_authority": document.metadata.get("issuing_authority"),
                        "case_number": document.metadata.get("case_number"),
                        "document_date": document.metadata.get("document_date"),
                        "related_institutions": get_json_field("related_institutions", []),
                        "violation_types": get_json_field("violation_types", []),
                        "penalty_amount": document.metadata.get("penalty_amount"),
                        "keywords": get_json_field("keywords", []),
                        "extraction_confidence": document.metadata.get("extraction_confidence"),
                        "extraction_method": document.metadata.get("extraction_method"),
                        # Metadata extraction status fields
                        "metadata_extracted": True,
                        "metadata_extraction_status": "completed",
                        "metadata_last_extracted_at": datetime.now(timezone.utc).isoformat(),
                        "metadata_extraction_attempts": 1,
                        # Descriptive fields
                        "title": document.metadata.get("title"),
                        "description": document.metadata.get("description"),
                    })
                    logger.debug(
                        f"Storing metadata fields from document.metadata: {document.metadata.get('document_type')}"
                    )

            # Upsert document metadata
            self.document_db.upsert_document(**db_fields)

            # Mark as indexed with chunk count
            self.document_db.mark_as_indexed(document.id, chunk_count=len(chunks))

            logger.info(
                f"Indexed document to SQLite: {document.id} ({len(chunks)} chunks)"
            )

        except Exception as e:
            logger.error(f"Failed to write document to SQLite: {document.id} - {e}")
            # Don't fail the indexing if SQLite write fails
            # The document is still in Chroma

        return len(chunks)

    async def index_documents(
        self, documents: list[Document], additional_metadata: dict[str, Any] | None = None
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
            chunks_added = await self.index_document(document, additional_metadata)
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
            logger.warning(f"No chunks found for document: {doc_id}")
            return 0

        # Delete all chunks from Chroma
        self.collection.delete(ids=results["ids"])

        # Delete from SQLite
        try:
            deleted = self.document_db.delete_document(doc_id)
            if deleted:
                logger.info(f"Deleted document from SQLite: {doc_id}")
            else:
                logger.warning(f"Document not found in SQLite: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete document from SQLite: {doc_id} - {e}")
            # Don't fail the deletion if SQLite delete fails
            # The document is already deleted from Chroma

        return len(results["ids"])

    def clear_collection(self):
        """Clear all documents from the collection."""
        # Delete the collection and recreate it
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Taiwan legal research documents"},
        )

    def get_collection_stats(self) -> dict[str, Any]:
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

    def get_document_chunks(self, doc_id: str) -> list[dict[str, Any]]:
        """
        Get all chunks for a specific document.

        Args:
            doc_id: Document ID

        Returns:
            List of chunk data dictionaries
        """
        results = self.collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])

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
