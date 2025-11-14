"""Vector store helper functions for accessing Chroma database."""

import chromadb
from chromadb.config import Settings

from finagent.config import settings


class VectorStore:
    """Wrapper for Chroma collection to provide a consistent interface."""

    def __init__(self, client: chromadb.PersistentClient, collection_name: str):
        """Initialize vector store wrapper.

        Args:
            client: Chroma persistent client
            collection_name: Name of the collection
        """
        self._client = client
        self._collection = client.get_or_create_collection(name=collection_name)

    @property
    def collection(self):
        """Get the underlying Chroma collection."""
        return self._collection


def get_vector_store(collection_name: str = "legal_documents") -> VectorStore:
    """
    Get or create a Chroma vector store instance.

    This is a helper function for accessing the vector database
    in a consistent way across the application.

    Args:
        collection_name: Name of the Chroma collection (default: "legal_documents")

    Returns:
        VectorStore wrapper instance
    """
    # Initialize Chroma client
    client = chromadb.PersistentClient(
        path=settings.chroma_persist_directory,
        settings=Settings(anonymized_telemetry=False),
    )

    return VectorStore(client, collection_name)


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get Chroma database client.

    Returns:
        Chroma persistent client
    """
    return chromadb.PersistentClient(
        path=settings.chroma_persist_directory,
        settings=Settings(anonymized_telemetry=False),
    )
