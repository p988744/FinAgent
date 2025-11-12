# LLM Configuration Guide

## Overview

FinAgent supports two LLM providers:
1. **OpenAI** - Cloud-based LLM with API key
2. **Local LLM** - Self-hosted models with OpenAI-compatible API (e.g., Ollama, LM Studio, vLLM)

## Quick Start

### Configure via CLI

```bash
# Show current configuration
finagent> /config

# Configure LLM interactively
finagent> /config llm
```

The interactive wizard will guide you through:
1. Choosing provider (OpenAI or Local LLM)
2. Setting model name
3. Configuring API credentials
4. Selecting embedding model

### Configure via .env File

Create or edit `.env` file in the backend directory:

#### Option 1: OpenAI (Default)

```env
USE_LOCAL_LLM=false
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Option 2: Local LLM (Ollama Example)

```env
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b
LOCAL_LLM_API_KEY=ollama

# Still need OpenAI API key for embeddings
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Supported Models

### OpenAI Models

**General Purpose:**
- `gpt-4o` - Latest GPT-4 Optimized (recommended for best quality)
- `gpt-4o-mini` - Fast and cost-effective (default, recommended)
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-4` - GPT-4
- `gpt-3.5-turbo` - Fast and cheap (may have lower quality)

**Embedding Models:**
- `text-embedding-3-small` - 1536 dimensions, $0.02/1M tokens (recommended)
- `text-embedding-3-large` - 3072 dimensions, $0.13/1M tokens
- `text-embedding-ada-002` - Legacy, 1536 dimensions

### Local LLM Models

Any model with **OpenAI-compatible API** is supported:

**Ollama Models (Popular for Chinese):**
- `qwen2.5:7b` - Alibaba Qwen 2.5, good for Chinese (recommended)
- `qwen2.5:14b` - Larger variant, better quality
- `llama3.1:8b` - Meta Llama 3.1
- `mistral:7b` - Mistral 7B

**LM Studio / vLLM:**
- Any model compatible with OpenAI API format
- Configure base URL according to your setup

## Local LLM Setup

### Method 1: Ollama (Easiest)

**Install Ollama:**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

**Start Ollama Server:**
```bash
ollama serve
```

**Pull a Model:**
```bash
# Recommended for Traditional Chinese
ollama pull qwen2.5:7b

# Alternative models
ollama pull qwen2.5:14b
ollama pull llama3.1:8b
```

**Configure FinAgent:**
```bash
finagent> /config llm
# Select: 2. 本地 LLM
# URL: http://localhost:11434/v1
# Model: qwen2.5:7b
# API Key: ollama (can be any string)
```

### Method 2: LM Studio

1. Download LM Studio from https://lmstudio.ai/
2. Load a model (e.g., Qwen 2.5, Llama 3.1)
3. Start Local Server (usually http://localhost:1234/v1)
4. Configure FinAgent:
   ```env
   USE_LOCAL_LLM=true
   LOCAL_LLM_BASE_URL=http://localhost:1234/v1
   LOCAL_LLM_MODEL=your-model-name
   LOCAL_LLM_API_KEY=lm-studio
   ```

### Method 3: vLLM

For production deployment with GPU acceleration:

```bash
# Install vLLM
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000
```

Configure:
```env
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://localhost:8000/v1
LOCAL_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LOCAL_LLM_API_KEY=vllm
```

## Performance Comparison

### OpenAI gpt-4o-mini (Default)

**Pros:**
- ✅ Fast (~40s per query)
- ✅ High quality legal analysis
- ✅ No setup required
- ✅ Good Traditional Chinese support

**Cons:**
- ❌ Costs ~$0.0015 per query
- ❌ Requires internet connection
- ❌ Data sent to OpenAI servers

**Cost:** ~$1.50/month for 1,000 queries

### Local LLM (Qwen 2.5 7B)

**Pros:**
- ✅ Free (no per-query cost)
- ✅ Complete data privacy
- ✅ No internet required (after download)
- ✅ Good Traditional Chinese support

**Cons:**
- ❌ Slower (~60-120s per query depending on hardware)
- ❌ Requires ~8GB VRAM for 7B model
- ❌ Initial setup required
- ❌ May have lower quality than GPT-4o-mini

**Cost:** $0/month (hardware costs only)

## Recommendations

### For Production (Best Quality)
- **Provider:** OpenAI
- **Model:** `gpt-4o-mini` (default)
- **Embedding:** `text-embedding-3-small`
- **Cost:** ~$2/month for 1,000 queries

### For Development/Testing
- **Provider:** Local LLM (Ollama)
- **Model:** `qwen2.5:7b`
- **Embedding:** `text-embedding-3-small` (still use OpenAI)
- **Cost:** Free

### For Maximum Privacy
- **Provider:** Local LLM (vLLM)
- **Model:** `qwen2.5:14b` (better quality)
- **Embedding:** Local embeddings (future feature)
- **Cost:** Free (but needs GPU)

## Troubleshooting

### Issue: "Connection refused" with Local LLM

**Cause:** Local LLM server not running

**Fix:**
```bash
# Ollama
ollama serve

# Or check if server is running
curl http://localhost:11434/v1/models
```

### Issue: "Model not found"

**Cause:** Model not pulled/downloaded

**Fix:**
```bash
# Ollama
ollama pull qwen2.5:7b
ollama list  # Verify model is available
```

### Issue: Slow response with local LLM

**Cause:** Running on CPU instead of GPU

**Options:**
1. Use smaller model (`qwen2.5:7b` instead of `14b`)
2. Enable GPU acceleration (CUDA for NVIDIA, Metal for Mac)
3. Use quantized models (Q4, Q5)
4. Switch to cloud provider for better performance

### Issue: Poor quality with local LLM

**Cause:** Model too small or not optimized for Traditional Chinese

**Fix:**
1. Try larger model: `qwen2.5:14b` or `qwen2.5:32b`
2. Adjust temperature in agent code
3. Use OpenAI for critical queries

## Configuration Files

**Location:** `/Users/weifanliao/PycharmProjects/finagent/backend/.env`

**Managed by:**
- `/config llm` command (recommended)
- Manual editing (advanced users)

**Applied when:**
- CLI restart required after changing configuration
- Settings loaded on startup

## Environment Variables

```env
# LLM Provider Selection
USE_LOCAL_LLM=false              # true = local LLM, false = OpenAI

# OpenAI Configuration
OPENAI_API_KEY=sk-...            # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini         # OpenAI model name
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.0           # LLM temperature (0-1)

# Local LLM Configuration
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:7b       # Local model name
LOCAL_LLM_API_KEY=ollama         # API key (can be any string)
```

## Future Enhancements

- [ ] Local embedding models (HuggingFace)
- [ ] Model performance benchmarking
- [ ] Automatic model selection based on query complexity
- [ ] Multi-provider fallback (try local, fallback to OpenAI)
- [ ] Cost tracking dashboard
- [ ] A/B testing between providers
