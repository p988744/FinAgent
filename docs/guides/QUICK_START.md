# FinAgent Quick Start Guide

**Updated:** 2025-11-14

## Installation

```bash
# Clone repository
git clone <your-repo-url>
cd finagent

# Install dependencies
uv sync
```

## First Time Setup

### 1. Configure LLM (Required)

Create `.env` file in the backend directory:

```bash
# Option 1: OpenAI (Official)
LLM_API_KEY=sk-proj-xxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Option 2: ELand GPT-OSS (Tested ✅)
LLM_API_KEY=sk-8KMPicNSUAqqmN1xyxxxx
LLM_BASE_URL=https://llmgw.elandai.cloud/v1
LLM_MODEL=ollama/gpt-oss:20b
EMBEDDING_MODEL=bge-m3

# Option 3: Ollama (Local)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_MODEL=nomic-embed-text
```

### 2. Add Your Documents

```bash
# Put your TXT documents in data/documents/
cp your_documents/*.txt data/documents/

# Supports recursive subdirectories
data/documents/
├── bank_penalties/
│   ├── 玉山銀行_洗錢防制_2020.txt
│   └── 國泰世華_內線交易_2021.txt
└── regulations/
    └── 金管會_法規_2023.txt
```

### 3. Index Documents

Choose one of these options:

#### Option A: Fast Mode (Recommended for first test)
```bash
# ~5 minutes for 492 documents
# Uses basic metadata (filename, type, etc.)
uv run finagent reindex --skip-init
```

#### Option B: Full Mode (Recommended for production)
```bash
# ~25 minutes for 492 documents
# Uses LLM to generate rich metadata
uv run finagent reindex
```

#### Option C: Clear and Rebuild
```bash
# Clear all existing data and rebuild
uv run finagent reindex --clear --yes
```

## Basic Usage

### Interactive Mode (REPL)

```bash
# Start interactive CLI
uv run finagent

# Inside the REPL:
finagent> 玉山銀行洗錢防制裁罰
finagent> 2020年金管會裁罰案件
finagent> /help
finagent> /config
finagent> /history
finagent> /exit
```

### Single Query Mode

```bash
# Run single query from terminal
uv run finagent query "玉山銀行洗錢防制裁罰"

# With options
uv run finagent query "2020年金管會裁罰" --max-results 10 --format json
```

### Reindex Mode

```bash
# Fast reindex (no LLM)
uv run finagent reindex --skip-init

# Full reindex (with LLM)
uv run finagent reindex

# Clear and rebuild
uv run finagent reindex --clear --yes
```

## Common Workflows

### Workflow 1: First Time Setup
```bash
# 1. Install
uv sync

# 2. Configure .env
echo "LLM_API_KEY=sk-xxx" > .env
echo "LLM_MODEL=gpt-4o-mini" >> .env

# 3. Add documents
cp ~/documents/*.txt data/documents/

# 4. Fast index for testing
uv run finagent reindex --skip-init

# 5. Test query
uv run finagent query "玉山銀行"

# 6. Full reindex for production (optional)
uv run finagent reindex
```

### Workflow 2: Adding New Documents
```bash
# 1. Add new files
cp new_documents/*.txt data/documents/

# 2. Reindex (only new files will be processed)
uv run finagent reindex --skip-init

# 3. Query should now include new documents
uv run finagent query "新增文件關鍵字"
```

### Workflow 3: Changing LLM Model
```bash
# 1. Update .env
# Change LLM_MODEL=gpt-4o-mini to LLM_MODEL=gpt-4o

# 2. Optional: Regenerate metadata with new model
uv run finagent reindex --clear --yes

# 3. Test with new model
uv run finagent query "test query"
```

### Workflow 4: Daily Automated Reindex
```bash
# Create automated_reindex.sh
cat > automated_reindex.sh << 'EOF'
#!/bin/bash
cd /path/to/finagent
git pull origin main
uv run finagent reindex --skip-init --yes
git add data/finagent.db data/vector_db/
git commit -m "chore: automated reindex $(date +%Y-%m-%d)"
git push
EOF

chmod +x automated_reindex.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /path/to/finagent/automated_reindex.sh" | crontab -
```

## Verification

### Check Database
```bash
# Check documents in database
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents WHERE indexed=1;"
# Expected: Number of TXT files

# Check vector chunks
sqlite3 data/vector_db/chroma.sqlite3 "SELECT COUNT(*) FROM embeddings;"
# Expected: ~3000+ for 492 documents

# Check concepts
sqlite3 data/finagent.db "SELECT COUNT(*) FROM concepts;"
# Expected: 100-200 concepts
```

### Run Tests
```bash
# Test metadata generator
uv run python test_metadata_generator.py

# Test LLM endpoint
uv run python test_llm_endpoint.py

# Run full test suite
uv run pytest
```

## Troubleshooting

### Issue: "LLM returned empty response"

**Solution:** The endpoint doesn't support `response_format`. This has been fixed in the latest version.

```bash
# Verify fix is applied
grep "use_response_format" src/finagent/document_processing/metadata_generator.py
# Should show: use_response_format = not base_url or "api.openai.com" in base_url
```

### Issue: "Documents not saved to database"

**Solution:** Fixed in latest version. Verify with:

```bash
# Check if documents are being saved
uv run finagent reindex --skip-init
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents WHERE indexed=1;"
# Should match number of files
```

### Issue: "Vector DB empty"

**Solution:** Run reindex to populate:

```bash
uv run finagent reindex --skip-init
```

### Issue: "Configuration not applied"

**Solution:** Reload configuration:

```bash
# In REPL mode
finagent> /config reload

# Or restart CLI
uv run finagent
```

## Performance Tips

### Fast Testing
```bash
# Use --skip-init for quick testing
uv run finagent reindex --skip-init  # ~5 min
```

### Production Quality
```bash
# Use full mode for rich metadata
uv run finagent reindex  # ~25 min
```

### Cost Optimization
```bash
# Use local models to avoid API costs
# Set in .env:
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
```

### Performance Metrics (492 documents)

| Mode | Time | Metadata Quality | Cost |
|------|------|------------------|------|
| Fast (--skip-init) | ~5 min | Basic | Free |
| Full (with LLM) | ~25 min | Rich | ~$0.75 |
| With local model | ~30 min | Rich | Free |

## Key Commands Reference

```bash
# Setup
uv sync                              # Install dependencies
uv run finagent --version           # Check version

# Interactive mode
uv run finagent                      # Start REPL

# Direct query
uv run finagent query "文字"         # Single query

# Reindex
uv run finagent reindex              # Full reindex with LLM
uv run finagent reindex --skip-init  # Fast reindex without LLM
uv run finagent reindex --clear      # Clear and rebuild

# Help
uv run finagent --help               # Main help
uv run finagent query --help         # Query help
uv run finagent reindex --help       # Reindex help
```

## Next Steps

1. **Try your first query**
   ```bash
   uv run finagent query "玉山銀行"
   ```

2. **Explore interactive mode**
   ```bash
   uv run finagent
   finagent> /help
   ```

3. **Configure for your use case**
   ```bash
   # Edit .env file
   # Choose LLM model (OpenAI/ELand/Ollama)
   # Adjust settings
   ```

4. **Add your documents**
   ```bash
   cp your_docs/*.txt data/documents/
   uv run finagent reindex --skip-init
   ```

5. **Set up automation** (optional)
   ```bash
   # See "Workflow 4: Daily Automated Reindex" above
   ```

## Documentation

- **[README.md](README.md)** - Project overview
- **[CLAUDE.md](CLAUDE.md)** - Development guide
- **[CLI_REINDEX_COMMAND.md](CLI_REINDEX_COMMAND.md)** - Reindex command guide
- **[LLM_COMPATIBILITY_FIX.md](LLM_COMPATIBILITY_FIX.md)** - LLM compatibility details
- **[SEQUENTIAL_REINDEX_COMPLETE.md](SEQUENTIAL_REINDEX_COMPLETE.md)** - Sequential reindex architecture

## Support

- **Issues:** Check existing issues or create new ones on GitHub
- **Testing:** Run `uv run python test_llm_endpoint.py` to diagnose LLM issues
- **Logs:** Check terminal output for detailed error messages

---

**Quick Start Complete!** 🎉

You're now ready to use FinAgent for legal research on Taiwan financial documents.
