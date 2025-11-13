"""
Embedding generation for document chunks using OpenAI.
"""

from typing import List, Optional
import asyncio

from openai import OpenAI, AsyncOpenAI
from finagent.config import settings


class EmbeddingGenerator:
    """Generates embeddings for text using OpenAI API."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize embedding generator.

        Args:
            model: Embedding model (default from settings)
            api_key: API key (default from settings)
            base_url: Base URL (default from settings)
        """
        # Get configuration
        self.model = model or settings.embedding_model
        self.api_key = api_key or settings.effective_embedding_api_key
        effective_base_url = base_url if base_url is not None else settings.effective_embedding_base_url

        # Initialize clients
        if effective_base_url:
            # Custom endpoint (e.g., Ollama, local server)
            self.client = OpenAI(api_key=self.api_key, base_url=effective_base_url)
            self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=effective_base_url)
        else:
            # OpenAI default
            self.client = OpenAI(api_key=self.api_key)
            self.async_client = AsyncOpenAI(api_key=self.api_key)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)

        Raises:
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Truncate if too long (OpenAI limit: 8191 tokens for text-embedding-3-small)
        # Rough estimate: 1 token ~= 4 chars for English, ~2 chars for Chinese
        max_chars = 8000 * 2  # ~16000 chars for Chinese
        if len(text) > max_chars:
            text = text[:max_chars]

        response = self.client.embeddings.create(input=text, model=self.model)

        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Truncate long texts
            max_chars = 8000 * 2
            batch = [t[:max_chars] if len(t) > max_chars else t for t in batch]

            # Filter empty texts
            valid_batch = [t for t in batch if t and t.strip()]

            if valid_batch:
                response = self.client.embeddings.create(input=valid_batch, model=self.model)

                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

        return all_embeddings

    async def generate_embedding_async(self, text: str) -> List[float]:
        """
        Generate embedding asynchronously.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        max_chars = 8000 * 2
        if len(text) > max_chars:
            text = text[:max_chars]

        response = await self.async_client.embeddings.create(input=text, model=self.model)

        return response.data[0].embedding

    async def generate_embeddings_batch_async(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings asynchronously in batches.

        Args:
            texts: List of texts
            batch_size: Batch size

        Returns:
            List of embeddings
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            max_chars = 8000 * 2
            batch = [t[:max_chars] if len(t) > max_chars else t for t in batch]
            valid_batch = [t for t in batch if t and t.strip()]

            if valid_batch:
                response = await self.async_client.embeddings.create(
                    input=valid_batch, model=self.model
                )

                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

        return all_embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model.

        Returns:
            Embedding dimension
        """
        # Known dimensions for OpenAI models
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
            # Common local embedding models
            "bge-m3": 1024,
            "bge-large-zh": 1024,
            "bge-base-zh": 768,
            "multilingual-e5-large": 1024,
        }

        return model_dimensions.get(self.model, 1536)
