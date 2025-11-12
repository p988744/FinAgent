# Automatic Configuration Guide

## Overview

The system now automatically detects whether to use OpenAI or local models based on what you provide in `.env`. **No flags needed!**

## How It Works

### Default: OpenAI

By default, the system uses OpenAI for everything. Just provide your API key:

```bash
OPENAI_API_KEY=sk-proj-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Override with Local LLM

To use a local LLM, just provide these three settings:

```bash
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_API_KEY=sk-xxx
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
```

The system will **automatically detect** and use your local LLM instead of OpenAI for chat/completion.

### Override with Local Embedding

To use a local embedding model, just provide the model name:

```bash
LOCAL_EMBEDDING_MODEL=bge-m3
```

The system will **automatically detect** and use your local embedding model instead of OpenAI.

## Configuration Examples

### Example 1: OpenAI Only (Default)

```bash
# .env
OPENAI_API_KEY=sk-proj-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Local settings are empty - will use OpenAI
LOCAL_LLM_BASE_URL=
LOCAL_LLM_API_KEY=
LOCAL_LLM_MODEL=
LOCAL_EMBEDDING_MODEL=
```

**Result**: Uses OpenAI for everything ✓

### Example 2: Both Local

```bash
# .env
OPENAI_API_KEY=sk-proj-xxx  # Still needed for fallback

# Local LLM configured - will override OpenAI
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_API_KEY=sk-xxx
LOCAL_LLM_MODEL=ollama/gpt-oss:20b

# Local embedding configured - will override OpenAI
LOCAL_EMBEDDING_MODEL=bge-m3
```

**Result**: Uses local LLM and local embedding ✓

### Example 3: Local LLM + OpenAI Embedding

```bash
# .env
OPENAI_API_KEY=sk-proj-xxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Local LLM configured
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_API_KEY=sk-xxx
LOCAL_LLM_MODEL=ollama/gpt-oss:20b

# No local embedding - will use OpenAI
LOCAL_EMBEDDING_MODEL=
```

**Result**: Uses local LLM + OpenAI embedding ✓

### Example 4: OpenAI LLM + Local Embedding

```bash
# .env
OPENAI_API_KEY=sk-proj-xxx
OPENAI_MODEL=gpt-4o-mini

# No local LLM - will use OpenAI
LOCAL_LLM_BASE_URL=
LOCAL_LLM_API_KEY=
LOCAL_LLM_MODEL=

# Local embedding configured
LOCAL_EMBEDDING_MODEL=bge-m3
LOCAL_EMBEDDING_BASE_URL=https://embedding-server.example.com/v1
LOCAL_EMBEDDING_API_KEY=sk-xxx
```

**Result**: Uses OpenAI LLM + local embedding ✓

## Detection Logic

### For Chat/Completion LLM

The system checks if **all three** are provided:
1. `LOCAL_LLM_BASE_URL` (not empty)
2. `LOCAL_LLM_API_KEY` (not empty)
3. `LOCAL_LLM_MODEL` (not empty)

If all three exist → Use local LLM
Otherwise → Use OpenAI

### For Embeddings

The system checks if `LOCAL_EMBEDDING_MODEL` is provided:

If `LOCAL_EMBEDDING_MODEL` exists → Use local embedding
Otherwise → Use OpenAI

**For local embedding URL and API key:**
- If `LOCAL_EMBEDDING_BASE_URL` is empty → Use `LOCAL_LLM_BASE_URL`
- If `LOCAL_EMBEDDING_API_KEY` is empty → Use `LOCAL_LLM_API_KEY`

## Switching Providers

### Switch from OpenAI to Local

**Before:**
```bash
# Using OpenAI
LOCAL_LLM_BASE_URL=
LOCAL_LLM_MODEL=
LOCAL_LLM_API_KEY=
```

**After:**
```bash
# Now using local
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
LOCAL_LLM_API_KEY=sk-xxx
```

Then reload:
```bash
finagent> /config reload
```

### Switch from Local to OpenAI

**Before:**
```bash
# Using local
LOCAL_LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LOCAL_LLM_MODEL=ollama/gpt-oss:20b
LOCAL_LLM_API_KEY=sk-xxx
```

**After:**
```bash
# Now using OpenAI
LOCAL_LLM_BASE_URL=
LOCAL_LLM_MODEL=
LOCAL_LLM_API_KEY=
```

Then reload:
```bash
finagent> /config reload
```

## Advantages of Auto-Detection

✅ **Simpler**: No `USE_LOCAL_LLM` or `USE_LOCAL_EMBEDDING` flags needed
✅ **Intuitive**: Just provide the settings you want to use
✅ **Flexible**: Easy to switch between providers
✅ **No Breaking Changes**: Existing configs still work (flags are now auto-detected)
✅ **Less Error-Prone**: Can't forget to set flags after providing settings

## Checking Current Configuration

### In CLI

```bash
finagent> /config
```

Shows which provider is active for each component:

```
┌─────────────────────────────────────┐
│           LLM 設定                  │
├─────────────────────────────────────┤
│ 聊天 LLM 提供者    │ 本地 LLM        │
│   ├─ URL          │ https://...     │
│   ├─ 模型          │ ollama/gpt-... │
│   └─ API Key      │ ***            │
│                                     │
│ 嵌入模型提供者      │ 本地嵌入模型     │
│   ├─ 模型          │ bge-m3         │
│   ├─ URL          │ https://...    │
│   └─ API Key      │ ***            │
└─────────────────────────────────────┘
```

### Via Test Script

```bash
cd backend
uv run python test_local_llm.py
```

Shows detected configuration:

```
📋 Settings:
   Chat LLM Provider: Local
     ├─ URL: https://llmgw.elandai.cloud/v1
     └─ Model: ollama/gpt-oss:20b
   Embedding Provider: Local
     ├─ URL: https://llmgw.elandai.cloud/v1 (shared with LLM)
     └─ Model: bge-m3
```

## Environment Variables Reference

### OpenAI Configuration (Always Needed)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key (used as fallback) |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | No | Default: `text-embedding-3-small` |
| `OPENAI_TEMPERATURE` | No | Default: `0.0` |

### Local LLM Override (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `LOCAL_LLM_BASE_URL` | For local LLM | OpenAI-compatible endpoint URL |
| `LOCAL_LLM_API_KEY` | For local LLM | API key for local LLM |
| `LOCAL_LLM_MODEL` | For local LLM | Model name |

**If all three are provided → Uses local LLM**

### Local Embedding Override (Optional)

| Variable | Required | Description |
|----------|----------|-------------|
| `LOCAL_EMBEDDING_MODEL` | For local embedding | Model name (e.g., `bge-m3`) |
| `LOCAL_EMBEDDING_BASE_URL` | No | Defaults to `LOCAL_LLM_BASE_URL` |
| `LOCAL_EMBEDDING_API_KEY` | No | Defaults to `LOCAL_LLM_API_KEY` |

**If `LOCAL_EMBEDDING_MODEL` is provided → Uses local embedding**

## Troubleshooting

### Issue: "Still using OpenAI even though I provided local settings"

**Check**: Make sure **all three** local LLM settings are provided:
```bash
LOCAL_LLM_BASE_URL=https://...   # ✓ Must be set
LOCAL_LLM_API_KEY=sk-xxx         # ✓ Must be set
LOCAL_LLM_MODEL=ollama/gpt-oss   # ✓ Must be set
```

If any one is missing, the system uses OpenAI.

### Issue: "Embedding still using local even though I want OpenAI"

**Solution**: Remove or empty the `LOCAL_EMBEDDING_MODEL` variable:
```bash
LOCAL_EMBEDDING_MODEL=  # Empty = use OpenAI
```

### Issue: "How do I know which provider is active?"

**Solution**: Run `/config` in CLI or `uv run python test_local_llm.py`

### Issue: "Can I use different endpoints for LLM and embedding?"

**Yes**: Provide `LOCAL_EMBEDDING_BASE_URL`:
```bash
LOCAL_LLM_BASE_URL=https://llm-server.com/v1
LOCAL_EMBEDDING_BASE_URL=https://embedding-server.com/v1
LOCAL_EMBEDDING_MODEL=bge-m3
```

## Migration from Old Config

### Old Format (with flags)

```bash
USE_LOCAL_LLM=true  # ❌ No longer needed
USE_LOCAL_EMBEDDING=true  # ❌ No longer needed
LOCAL_LLM_BASE_URL=...
LOCAL_LLM_MODEL=...
```

### New Format (auto-detected)

```bash
# Just provide the settings, system auto-detects
LOCAL_LLM_BASE_URL=...
LOCAL_LLM_API_KEY=...
LOCAL_LLM_MODEL=...
```

**No action required**: The flags are ignored now (system uses auto-detection).

## Summary

| Configuration | What to Provide | Detection Result |
|--------------|-----------------|------------------|
| OpenAI only | Just `OPENAI_API_KEY` | ✅ Uses OpenAI |
| Local LLM only | `LOCAL_LLM_*` (all 3) | ✅ Uses local LLM |
| Local embedding only | `LOCAL_EMBEDDING_MODEL` | ✅ Uses local embedding |
| Mixed | Provide what you want to override | ✅ Auto-detected correctly |

**Simple rule**: Provide the settings → System uses them!

For more details, see:
- [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) - Local LLM setup guide
- [SEPARATE_PROVIDERS_GUIDE.md](SEPARATE_PROVIDERS_GUIDE.md) - Provider comparison
- [CLI_GUIDE.md](CLI_GUIDE.md) - CLI documentation
