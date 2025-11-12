"""
Document processing module for FinAgent.

Handles document loading, chunking, embedding, and indexing for RAG.
"""

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.metadata_store import (
    DocumentMetadataStore,
    DocumentMetadata,
)
from finagent.document_processing.toc_generator import TableOfContents

__all__ = [
    "DocumentLoader",
    "ChineseTextChunker",
    "EmbeddingGenerator",
    "DocumentIndexer",
    "DocumentRetriever",
    "DocumentMetadataStore",
    "DocumentMetadata",
    "TableOfContents",
]
