# Embedding Dimension Mismatch - Analysis and Fix

## Problem Summary

**Error**: `Collection expecting embedding with dimension of 1536, got 3072`

## Root Cause

The vector database was originally indexed with **text-embedding-3-large** (3072 dimensions), but the current configuration uses **text-embedding-3-small** (1536 dimensions).

When you run a query:
1. Query embedding is generated with text-embedding-3-small (1536 dims) ← current config
2. Vector database expects text-embedding-3-large (3072 dims) ← old index
3. Dimension mismatch error occurs

## Current Status

✅ **Configuration is correct**:
- `.env` file: `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `EmbeddingGenerator` correctly reads this setting
- Expected dimensions: 1536

❌ **Vector database is empty**:
- The collection appears to have been cleared
- Need to reindex documents

## Solution

You need to **reindex all documents** with the current embedding model:

```bash
# Start the CLI
uv run finagent

# In the CLI, run reindex
finagent> /reindex

# Or reindex from scratch (clears existing index first)
finagent> /reindex --clear
```

This will:
1. Load all documents from `data/documents/`
2. Generate embeddings using `text-embedding-3-small` (1536 dims)
3. Index them into Chroma vector database
4. Queries will now work correctly

## Prevention

To avoid this issue in the future:

1. **Before changing embedding models**, clear and reindex:
   ```bash
   finagent> /reindex --clear
   ```

2. **Embedding model changes require reindexing** because:
   - Different models have different dimensions
   - text-embedding-3-small: 1536 dims
   - text-embedding-3-large: 3072 dims
   - text-embedding-ada-002: 1536 dims

3. **Choose the right model** based on your needs:
   - `text-embedding-3-small`: Faster, cheaper, 1536 dims (recommended)
   - `text-embedding-3-large`: Higher quality, more expensive, 3072 dims

## Why text-embedding-3-small is Recommended

- **Cost**: $0.02/1M tokens (vs $0.13/1M for large)
- **Speed**: Faster embedding generation
- **Quality**: Sufficient for most legal research tasks
- **Storage**: Smaller vector database size

## Current Configuration Check

Run this to verify your configuration:

```bash
uv run python -c "
from finagent.config import settings
from finagent.document_processing.embeddings import EmbeddingGenerator

print(f'Embedding model: {settings.openai_embedding_model}')
embedder = EmbeddingGenerator()
print(f'Expected dimensions: {embedder.get_embedding_dimension()}')
"
```

Expected output:
```
Embedding model: text-embedding-3-small
Expected dimensions: 1536
```

## Implementation Details

The embedding model is read from `.env` and used in:

1. **Indexing** (`DocumentIndexer`):
   - `backend/src/finagent/document_processing/indexer.py:53`
   - Creates `EmbeddingGenerator()` which reads `settings.openai_embedding_model`

2. **Retrieval** (`DocumentRetriever`):
   - `backend/src/finagent/document_processing/retriever.py:60`
   - Creates `EmbeddingGenerator()` which reads `settings.openai_embedding_model`

Both use the same configuration, so they will always match **as long as you reindex after changing the embedding model**.

## Related Files

- Configuration: `backend/.env` (line 8)
- Config module: `backend/src/finagent/config.py` (line 36-38)
- Embeddings: `backend/src/finagent/document_processing/embeddings.py`
- Indexer: `backend/src/finagent/document_processing/indexer.py`
- Retriever: `backend/src/finagent/document_processing/retriever.py`

## OpenAI API Key Issue

**Note**: During testing, we encountered an authentication error (401) with the API key in `.env`.

The API key in line 6 of `.env` appears to be invalid or truncated. You may need to update it with a valid OpenAI API key from https://platform.openai.com/api-keys

To test if your API key works:
```bash
uv run python -c "
from finagent.document_processing.embeddings import EmbeddingGenerator
embedder = EmbeddingGenerator()
embedding = embedder.generate_embedding('測試')
print(f'✓ API key is valid. Embedding dimensions: {len(embedding)}')
"
```

If this returns a 401 error, run `/config llm` to update your OpenAI API key.
