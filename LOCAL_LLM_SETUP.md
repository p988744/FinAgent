# Local LLM Setup Guide

## Summary

Your local LLM and embedding model are now **fully configured and tested**!

## Test Results

✅ **Local LLM**: `ollama/gpt-oss:20b` - Working correctly
✅ **Local Embedding**: `bge-m3` (1024 dimensions) - Working correctly

## Configuration

### Current `.env` Settings

```bash
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
LOCAL_LLM_API_KEY=sk-8KMPicNSUAqqmN1xyI45VA
LOCAL_EMBEDDING_MODEL=bge-m3
```

### What Was Changed

1. **Added `LOCAL_EMBEDDING_MODEL` config field** ([config.py:46](backend/src/finagent/config.py#L46))
   - New field to specify local embedding model name

2. **Updated `EmbeddingGenerator`** ([embeddings.py:15-43](backend/src/finagent/document_processing/embeddings.py#L15-L43))
   - Automatically detects when `USE_LOCAL_LLM=true`
   - Uses local embedding endpoint when `LOCAL_EMBEDDING_MODEL` is set
   - Falls back to OpenAI embeddings if not configured

3. **Added embedding dimensions** ([embeddings.py:163-182](backend/src/finagent/document_processing/embeddings.py#L163-L182))
   - `bge-m3`: 1024 dims
   - `bge-large-zh`: 1024 dims
   - `bge-base-zh`: 768 dims
   - `multilingual-e5-large`: 1024 dims

4. **Updated `.env.example`** ([.env.example:7-12](backend/.env.example#L7-L12))
   - Documented local LLM configuration options

## Testing Your Setup

Run the test script anytime to verify your local LLM setup:

```bash
cd backend
uv run python test_local_llm.py
```

This will test:
- Local LLM connection and response generation
- Local embedding model connection
- Single and batch embedding generation

## Using Your Local LLM

### In CLI

Your FinAgent CLI is now configured to use your local LLM automatically:

```bash
cd backend
uv run finagent

# All queries will now use your local LLM
finagent> 玉山銀行洗錢防制裁罰
```

### Switch Between Local and OpenAI

Edit `backend/.env`:

```bash
# Use local LLM
USE_LOCAL_LLM=true

# Use OpenAI
USE_LOCAL_LLM=false
```

Then reload config without restarting:

```bash
finagent> /config reload
```

### View Current Configuration

```bash
finagent> /config
```

This shows:
- Current LLM provider (OpenAI or Local)
- Model names
- API endpoint (for local LLM)
- API key status

## Architecture

### LLM Flow

```
Query → Planning Agent (Local LLM) → Action Agent → Answer Agent (Local LLM)
```

### Embedding Flow

```
Documents → EmbeddingGenerator (Local bge-m3) → Chroma Vector DB → Retrieval
```

### OpenAI-Compatible API

Your local LLM endpoint (`https://llmgw.elandai.cloud/v1`) follows the OpenAI API standard, so the system uses the same `OpenAI` client with a custom `base_url`:

```python
client = OpenAI(
    base_url="https://llmgw.elandai.cloud/v1",
    api_key="sk-8KMPicNSUAqqmN1xyI45VA"
)
```

## Performance Considerations

### Local LLM Benefits
- ✅ Lower cost (no OpenAI API fees)
- ✅ Data privacy (all processing on your infrastructure)
- ✅ No rate limits
- ⚠️ May be slower than OpenAI GPT-4o-mini

### Embedding Model (bge-m3)
- **Dimension**: 1024 (vs OpenAI's 1536)
- **Quality**: Optimized for Chinese text
- **Speed**: Fast inference
- **Cost**: Free (self-hosted)

## Troubleshooting

### Issue: Embeddings failing

**Check**:
```bash
cd backend
uv run python test_local_llm.py
```

If embedding test fails:
1. Verify `LOCAL_EMBEDDING_MODEL` is set in `.env`
2. Check that your endpoint supports embeddings API
3. Ensure model name matches what's available on your server

### Issue: LLM responses slow

Your local LLM (`ollama/gpt-oss:20b`) is a 20B parameter model, which may be slower than smaller models. Consider:
- Using a smaller model (e.g., `qwen2.5:7b`)
- Checking server GPU availability
- Monitoring server load

### Issue: Want to use OpenAI for chat, local for embeddings

Currently, the system uses the same provider for both. To mix providers, you would need to:
1. Set `USE_LOCAL_LLM=false` (use OpenAI for chat)
2. Modify `EmbeddingGenerator.__init__()` to force local embeddings regardless of `use_local_llm`

## Next Steps

### 1. Reindex Documents with Local Embeddings

If you previously indexed documents with OpenAI embeddings, reindex with your local embedding model:

```bash
finagent> /reindex --clear
```

This will:
- Clear existing embeddings
- Re-generate all embeddings using `bge-m3`
- Rebuild vector database with 1024-dim embeddings

### 2. Test Real Queries

Try some legal research queries:

```bash
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件
finagent> 國泰世華銀行法規違規
```

### 3. Monitor Performance

Compare response quality and speed:
- Local LLM vs OpenAI
- Local embeddings (bge-m3) vs OpenAI (text-embedding-3-small)

### 4. Fine-tune Settings

Adjust temperature for your use case:

```bash
# In .env
OPENAI_TEMPERATURE=0.0  # Deterministic (current)
OPENAI_TEMPERATURE=0.3  # Slightly creative
OPENAI_TEMPERATURE=0.7  # More variety
```

Then reload:
```bash
finagent> /config reload
```

## Summary of Changes

**Files Modified**:
- [config.py](backend/src/finagent/config.py) - Added `local_embedding_model` field
- [embeddings.py](backend/src/finagent/document_processing/embeddings.py) - Auto-detect local embeddings
- [.env.example](backend/.env.example) - Documented local LLM config
- [.env](backend/.env) - Added `LOCAL_EMBEDDING_MODEL=bge-m3`

**Files Created**:
- [test_local_llm.py](backend/test_local_llm.py) - Test script for local LLM setup
- [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) - This guide

**Commits**:
- `93d4dac` - feat: add support for local embedding models

---

## Questions?

- Run `/help` in CLI for all available commands
- Check [MODEL_CONFIG_GUIDE.md](backend/MODEL_CONFIG_GUIDE.md) for advanced model configuration
- View [CLI_GUIDE.md](CLI_GUIDE.md) for complete CLI documentation

**Your local LLM setup is ready to use! 🎉**
