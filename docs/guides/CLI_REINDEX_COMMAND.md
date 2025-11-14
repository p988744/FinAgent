# CLI Reindex Command

**Added:** 2025-11-14
**Feature:** Direct terminal access to reindex functionality

## Overview

The `finagent reindex` command allows you to reindex documents directly from the terminal without entering the interactive REPL. This makes it easier to:

- Test reindexing quickly
- Run reindex from scripts
- Automate document processing
- Use in CI/CD pipelines

## Usage

### Basic Commands

```bash
# Full reindex with LLM metadata generation (~25 min for 492 docs)
uv run finagent reindex

# Fast reindex without LLM metadata (~5 min for 492 docs)
uv run finagent reindex --skip-init

# Clear all existing data and rebuild from scratch
uv run finagent reindex --clear

# Clear and rebuild without confirmation prompt
uv run finagent reindex --clear --yes
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--clear` | | Clear existing index before reindexing |
| `--skip-init` | | Skip LLM metadata generation (faster) |
| `--yes` | `-y` | Skip confirmation prompt for --clear |
| `--help` | | Show help message |

## Examples

### Example 1: Quick Test Reindex
```bash
# Fast reindex for testing (skips LLM, ~5 min)
uv run finagent reindex --skip-init
```

**Expected Output:**
```
🚀 開始重新索引文件...

📄 載入文件...
✅ 找到 492 個文件

⏭️  跳過 LLM 元資料生成（使用基本元資料）

處理文件... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:05:00

📊 索引摘要
  ✅ 已索引: 492 份文件
  ⏭️  已跳過: 0 份文件
  📦 總區塊: 3056 個

💡 概念摘要
  總概念數: 150
  前 10 個概念:
    • 金管會 (120 份文件)
    • 洗錢防制 (45 份文件)
    • 玉山銀行 (25 份文件)
    ...

✅ 重新索引完成！
```

### Example 2: Full Production Reindex
```bash
# Full reindex with LLM-generated metadata (~25 min)
uv run finagent reindex
```

**Expected Output:**
```
🚀 開始重新索引文件...

📄 載入文件...
✅ 找到 492 個文件

🤖 將使用 LLM 生成文件元資料

處理文件... ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:25:00

📊 索引摘要
  ✅ 已索引: 492 份文件
  ⏭️  已跳過: 0 份文件
  📦 總區塊: 3056 個

💡 概念摘要
  總概念數: 180
  前 10 個概念:
    • 金管會 (120 份文件)
    • 洗錢防制 (45 份文件)
    ...

✅ 重新索引完成！
```

### Example 3: Clear and Rebuild
```bash
# Interactive confirmation
uv run finagent reindex --clear

# Output:
⚠️  Warning: This will delete all existing indexes and rebuild!

Continue? [y/N]: y

# Or skip confirmation with --yes
uv run finagent reindex --clear --yes
```

### Example 4: Scripting Usage
```bash
#!/bin/bash
# automated_reindex.sh

echo "Starting automated document reindex..."

# Pull latest documents from repository
git pull origin main

# Run fast reindex without confirmation
uv run finagent reindex --skip-init --yes

echo "Reindex complete!"
```

## Comparison: REPL vs CLI Command

### REPL Mode (Interactive)
```bash
# Start REPL
uv run finagent

# Inside REPL
finagent> /reindex --skip-init
finagent> /config
finagent> /history
finagent> /exit
```

**Pros:**
- Interactive exploration
- Multiple commands in one session
- Command history
- Tab completion

**Cons:**
- Manual interaction required
- Not suitable for scripting
- Need to exit to run other commands

### CLI Command (Direct)
```bash
# Direct command
uv run finagent reindex --skip-init
```

**Pros:**
- ✅ One-shot execution
- ✅ Scriptable and automatable
- ✅ No interactive input needed
- ✅ Perfect for CI/CD
- ✅ Can chain with other commands

**Cons:**
- Limited to single operation
- Need to restart for each command

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Reindex Documents

on:
  push:
    paths:
      - 'data/documents/**'

jobs:
  reindex:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Reindex documents
        run: |
          uv sync
          uv run finagent reindex --skip-init --yes
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}

      - name: Commit updated index
        run: |
          git add data/finagent.db data/vector_db/
          git commit -m "chore: automated reindex"
          git push
```

### Cron Job Example
```bash
# /etc/cron.d/finagent-reindex
# Reindex documents daily at 2 AM

0 2 * * * cd /path/to/finagent && uv run finagent reindex --skip-init --yes >> /var/log/finagent-reindex.log 2>&1
```

## Implementation Details

### File Modified
- **[src/finagent/cli/main.py](src/finagent/cli/main.py#L72-L105)** - Added `@cli.command()` for reindex

### Code Added
```python
@cli.command()
@click.option("--clear", is_flag=True, help="Clear existing index before reindexing")
@click.option("--skip-init", is_flag=True, help="Skip LLM metadata generation (faster)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def reindex(clear, skip_init, yes):
    """Reindex all documents in the data/documents directory."""
    from finagent.cli.commands.reindex import execute_reindex

    # Handle confirmation for --clear
    if clear and not yes:
        console.print()
        console.print("[bold yellow]⚠️  Warning:[/bold yellow] This will delete all existing indexes and rebuild!")
        console.print()
        if not click.confirm("Continue?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    execute_reindex(clear=clear, skip_init=skip_init, use_sequential=True)
```

## Testing

### Test Command Availability
```bash
# Check if command is registered
uv run finagent --help
# Should show:
#   Commands:
#     query    Submit a single legal research query.
#     reindex  Reindex all documents in the data/documents directory.

# Check reindex options
uv run finagent reindex --help
```

### Test Quick Reindex
```bash
# Run a fast reindex to verify it works
uv run finagent reindex --skip-init

# Verify results
sqlite3 data/finagent.db "SELECT COUNT(*) FROM documents WHERE indexed=1;"
# Should show: 492

sqlite3 data/vector_db/chroma.sqlite3 "SELECT COUNT(*) FROM embeddings;"
# Should show: ~3000+
```

## Benefits

### Before (REPL Only)
```bash
# Multi-step process
uv run finagent           # Start REPL
finagent> /reindex        # Run command
finagent> /exit           # Exit REPL
```

### After (Direct CLI)
```bash
# Single command
uv run finagent reindex --skip-init
```

### Time Saved
- REPL startup: ~2 seconds
- Manual interaction: ~5 seconds
- Total saved per run: ~7 seconds
- **For automation: Infinite** (enables scripting)

## Related Features

- `/reindex` command in REPL (interactive)
- Sequential reindex implementation
- LLM compatibility fixes
- Concept extraction system

## Next Steps

### Potential Enhancements

1. **Progress output modes**
   ```bash
   uv run finagent reindex --quiet  # Minimal output
   uv run finagent reindex --verbose  # Detailed logging
   uv run finagent reindex --json  # Machine-readable output
   ```

2. **Selective reindexing**
   ```bash
   uv run finagent reindex --limit 10  # First 10 documents only
   uv run finagent reindex --pattern "玉山*.txt"  # Matching pattern
   uv run finagent reindex --since "2024-01-01"  # Modified since date
   ```

3. **Parallel processing**
   ```bash
   uv run finagent reindex --workers 4  # Use 4 parallel workers
   ```

4. **Other commands**
   ```bash
   uv run finagent config llm  # Direct LLM configuration
   uv run finagent stats  # Show database statistics
   uv run finagent concepts  # Browse concepts
   ```

---

**Status:** ✅ Implemented and tested
**Version:** Available in current version
**Documentation:** Updated in CLAUDE.md
