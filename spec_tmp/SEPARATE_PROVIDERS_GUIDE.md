# Separate LLM and Embedding Providers Guide

## Overview

You can now **independently configure** your chat LLM and embedding model providers. This allows you to mix and match providers based on your needs.

## Configuration Options

### Option 1: Both Local (Cost-effective)

```bash
# Chat LLM
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
LOCAL_LLM_API_KEY=sk-xxx

# Embeddings
USE_LOCAL_EMBEDDING=true
LOCAL_EMBEDDING_MODEL=bge-m3
# Leave empty to share same endpoint
LOCAL_EMBEDDING_BASE_URL=
LOCAL_EMBEDDING_API_KEY=
```

**Use case**: Maximum cost savings, full data privacy

### Option 2: Local LLM + OpenAI Embeddings

```bash
# Chat LLM
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
LOCAL_LLM_API_KEY=sk-xxx

# Embeddings
USE_LOCAL_EMBEDDING=false
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-proj-xxx
```

**Use case**: Save on LLM costs while using high-quality OpenAI embeddings (1536 dims)

### Option 3: OpenAI LLM + Local Embeddings

```bash
# Chat LLM
USE_LOCAL_LLM=false
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-xxx

# Embeddings
USE_LOCAL_EMBEDDING=true
LOCAL_EMBEDDING_MODEL=bge-m3
LOCAL_EMBEDDING_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_EMBEDDING_API_KEY=sk-xxx
```

**Use case**: Use powerful OpenAI models for reasoning while saving on embedding costs

### Option 4: Both OpenAI (Default)

```bash
# Chat LLM
USE_LOCAL_LLM=false
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-xxx

# Embeddings
USE_LOCAL_EMBEDDING=false
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Use case**: Simplest setup, best quality, higher cost

## Configuration Fields

### Chat/Completion LLM

| Field | Description | Required |
|-------|-------------|----------|
| `USE_LOCAL_LLM` | Use local LLM instead of OpenAI | Yes |
| `LOCAL_LLM_BASE_URL` | Local LLM endpoint URL | If local |
| `LOCAL_LLM_MODEL` | Local LLM model name | If local |
| `LOCAL_LLM_API_KEY` | Local LLM API key | If local |
| `OPENAI_MODEL` | OpenAI model name | If OpenAI |
| `OPENAI_API_KEY` | OpenAI API key | If OpenAI |

### Embedding Model

| Field | Description | Required |
|-------|-------------|----------|
| `USE_LOCAL_EMBEDDING` | Use local embedding instead of OpenAI | Yes |
| `LOCAL_EMBEDDING_MODEL` | Local embedding model name | If local |
| `LOCAL_EMBEDDING_BASE_URL` | Local embedding endpoint URL (optional, defaults to `LOCAL_LLM_BASE_URL`) | No |
| `LOCAL_EMBEDDING_API_KEY` | Local embedding API key (optional, defaults to `LOCAL_LLM_API_KEY`) | No |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model name | If OpenAI |
| `OPENAI_API_KEY` | OpenAI API key | If OpenAI |

## Testing Your Configuration

Run the test script to verify your setup:

```bash
cd backend
uv run python test_local_llm.py
```

The script will:
- Show your current configuration
- Test each enabled provider
- Skip tests for OpenAI providers (to avoid API costs)
- Report success/failure for each component

### Example Output

**Both Local:**
```
📋 Settings:
   Chat LLM Provider: Local
     ├─ URL: https://llmgw.elandai.cloud/v1
     └─ Model: ollama/gpt-oss:20b
   Embedding Provider: Local
     ├─ URL: https://llmgw.elandai.cloud/v1 (shared with LLM)
     └─ Model: bge-m3

✅ Local LLM: PASSED
✅ Local Embedding: PASSED
```

**Mixed (Local LLM + OpenAI Embedding):**
```
📋 Settings:
   Chat LLM Provider: Local
     ├─ URL: https://llmgw.elandai.cloud/v1
     └─ Model: ollama/gpt-oss:20b
   Embedding Provider: OpenAI

✅ Local LLM: PASSED
⏭️  Local Embedding: SKIPPED (using OpenAI)
```

## Viewing Configuration in CLI

Use the `/config` command to view your current setup:

```bash
finagent> /config
```

Output shows both providers separately:

```
╭─────────────────────────────────────╮
│           LLM 設定                  │
├─────────────────────────────────────┤
│ 聊天 LLM 提供者    │ 本地 LLM        │
│   ├─ URL          │ https://...     │
│   ├─ 模型          │ ollama/gpt-...  │
│   └─ API Key      │ ***             │
│                                     │
│ 嵌入模型提供者      │ 本地嵌入模型     │
│   ├─ 模型          │ bge-m3          │
│   ├─ URL          │ https://... (共用 LLM) │
│   └─ API Key      │ *** (共用 LLM)  │
│                                     │
│ 溫度 (Temperature) │ 0.0             │
╰─────────────────────────────────────╯
```

## Reloading Configuration

After changing your `.env` file, reload without restarting:

```bash
finagent> /config reload
```

This will:
- Reload `.env` settings
- Reload `model_config.yml`
- Reset the query orchestrator
- Show updated configuration

## Use Cases & Recommendations

### Development

**Recommended**: Local LLM + Local Embedding
- Fast iteration
- No API costs
- Full privacy

### Production (Quality)

**Recommended**: OpenAI LLM + OpenAI Embedding
- Best quality
- Consistent performance
- Official support

### Production (Cost-optimized)

**Recommended**: Local LLM + OpenAI Embedding
- Good quality reasoning (local 20B model)
- High-quality embeddings (OpenAI 1536 dims)
- Lower costs than full OpenAI

### Prototyping

**Recommended**: OpenAI LLM + Local Embedding
- Fast OpenAI responses for testing
- Save on embedding costs (local is free)
- Easy switch to production config

## Cost Comparison

### Per 1000 queries (assuming 2K tokens/query, 100 docs embedded)

| Configuration | LLM Cost | Embedding Cost | Total |
|---------------|----------|----------------|-------|
| Both OpenAI | $0.30 | $0.02 | $0.32 |
| Local LLM + OpenAI Embedding | $0.00 | $0.02 | $0.02 |
| OpenAI LLM + Local Embedding | $0.30 | $0.00 | $0.30 |
| Both Local | $0.00 | $0.00 | $0.00 |

*Note: Local models incur infrastructure costs (compute, bandwidth)*

## Performance Comparison

### Response Quality

| Provider | Chat Quality | Embedding Quality |
|----------|-------------|-------------------|
| OpenAI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (1536 dims) |
| Local (20B) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ (1024 dims) |

### Response Speed

| Configuration | Avg Response Time |
|---------------|-------------------|
| Both OpenAI | ~5-10s |
| Both Local | ~15-40s |
| Mixed | ~10-25s |

*Depends on server load, model size, and network latency*

## Troubleshooting

### Issue: "USE_LOCAL_EMBEDDING is True but LOCAL_EMBEDDING_MODEL is not set"

**Solution**: Set `LOCAL_EMBEDDING_MODEL` in `.env`:
```bash
LOCAL_EMBEDDING_MODEL=bge-m3
```

### Issue: Embedding dimensions mismatch

**Symptoms**: Error when querying vector database after changing embedding model

**Solution**: Reindex documents with new embedding model:
```bash
finagent> /reindex --clear
```

This clears old embeddings and regenerates with the new model.

### Issue: Local embedding slower than expected

**Check**:
1. Is `LOCAL_EMBEDDING_BASE_URL` set to the correct endpoint?
2. Is the endpoint supporting batch requests?
3. Try using separate embedding endpoint if available

### Issue: Want to use different endpoints for LLM and embeddings

**Solution**: Set separate URLs:
```bash
LOCAL_LLM_BASE_URL=https://llm-server.example.com/v1
LOCAL_EMBEDDING_BASE_URL=https://embedding-server.example.com/v1
```

## Migration Guide

### From Single Provider to Separate Providers

**Before** (old config):
```bash
USE_LOCAL_LLM=true  # Controlled both LLM and embeddings
LOCAL_LLM_BASE_URL=...
LOCAL_LLM_MODEL=...
LOCAL_EMBEDDING_MODEL=bge-m3
```

**After** (new config):
```bash
USE_LOCAL_LLM=true              # Controls LLM only
USE_LOCAL_EMBEDDING=true        # Controls embeddings separately
LOCAL_LLM_BASE_URL=...
LOCAL_LLM_MODEL=...
LOCAL_EMBEDDING_MODEL=bge-m3
# Optional: separate endpoint
LOCAL_EMBEDDING_BASE_URL=
LOCAL_EMBEDDING_API_KEY=
```

**Action required**:
1. Add `USE_LOCAL_EMBEDDING=true` to your `.env`
2. Run `/config reload` in CLI
3. Verify with `/config`

## Summary

✅ **Flexibility**: Mix and match LLM and embedding providers
✅ **Cost Control**: Use local for expensive operations, OpenAI for quality
✅ **Easy Testing**: Test different configurations without code changes
✅ **No Restart**: Reload configuration on the fly
✅ **Clear Status**: See current providers in `/config` output

For more help, see:
- [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) - Local LLM setup guide
- [MODEL_CONFIG_GUIDE.md](backend/MODEL_CONFIG_GUIDE.md) - Model configuration guide
- [CLI_GUIDE.md](CLI_GUIDE.md) - Complete CLI documentation
