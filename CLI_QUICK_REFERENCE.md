# FinAgent CLI Quick Reference

## Starting the CLI

```bash
# Interactive REPL mode
uv run finagent

# Single query mode
uv run finagent query "查詢文字"

# Show help
uv run finagent --help

# Show version
uv run finagent --version
```

## REPL Commands

| Command | Shortcut | Description | Example |
|---------|----------|-------------|---------|
| Direct input | - | Submit query directly | `玉山銀行裁罰` |
| `/query <text>` | `/q` | Execute query | `/q 國泰世華銀行` |
| `/help` | `/h`, `/?` | Show help | `/help` |
| `/history` | `/hist` | View query history | `/history` |
| `/citations` | `/cite` | Show last citations | `/citations` |
| `/clear` | `/cls` | Clear screen | `/clear` |
| `/config` | - | Show configuration | `/config` |
| `/export <fmt>` | - | Export results | `/export markdown` |
| `/exit` | `/quit`, `/q!` | Exit REPL | `/exit` |

## Query Command Options

```bash
uv run finagent query TEXT [OPTIONS]

Options:
  -n, --max-results INTEGER       Max results (1-50, default: 5)
  --regulator TEXT               Filter: FSC, CBC, FTC
  --start-date TEXT              YYYY-MM-DD
  --end-date TEXT                YYYY-MM-DD
  -f, --format FORMAT            rich, json, markdown (default: rich)
```

### Examples

```bash
# Basic query
uv run finagent query "玉山銀行洗錢防制裁罰"

# With max results
uv run finagent query "2020年裁罰" -n 10

# Filter by regulator
uv run finagent query "銀行裁罰" --regulator FSC

# Date range
uv run finagent query "裁罰案件" --start-date 2020-01-01 --end-date 2020-12-31

# JSON output
uv run finagent query "國泰世華" -f json

# Markdown output
uv run finagent query "台新銀行" -f markdown > report.md

# Combined options
uv run finagent query "裁罰" -n 10 --regulator FSC --format json
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit REPL |
| `↑` | Previous command |
| `↓` | Next command |
| `Tab` | Auto-complete |
| `Ctrl+R` | Search history |

## Output Formats

### Rich (Default)
- Beautiful terminal output
- Color-coded sections
- Visual confidence bars
- Tables for precedents

### JSON
- Structured data
- Programmatic access
- Pipe to jq/other tools

```bash
uv run finagent query "text" -f json | jq '.citations'
```

### Markdown
- Documentation format
- Easy to save/share
- Tables and formatting

```bash
uv run finagent query "text" -f markdown > report.md
```

## Query Tips

### Good Queries (Specific)
✅ `玉山銀行洗錢防制裁罰`
✅ `2020年金管會裁罰案件`
✅ `國泰世華銀行內線交易`
✅ `台新銀行資訊揭露違規`

### Vague Queries (Less Effective)
❌ `銀行` (too broad)
❌ `裁罰` (too generic)
❌ `違規` (needs context)

### Query Structure
```
[機構名稱] + [違規類型] + [時間範圍]

Examples:
- 玉山銀行 + 洗錢防制 + 2020
- 國泰世華 + 內線交易 + 民國109年
- 台新銀行 + 資訊揭露 + 2019-2021
```

## Common Use Cases

### 1. Research Specific Institution
```bash
uv run finagent query "玉山銀行裁罰案件" -n 20
```

### 2. Time-based Analysis
```bash
uv run finagent query "2020年金管會裁罰" --start-date 2020-01-01 --end-date 2020-12-31
```

### 3. Violation Type Research
```bash
uv run finagent query "洗錢防制法違規案件" -n 15
```

### 4. Generate Report
```bash
uv run finagent query "國泰世華銀行裁罰" -f markdown > report_cathay.md
```

### 5. Data Extraction
```bash
# Extract all citation URLs
uv run finagent query "台新銀行" -f json | jq '.citations[].url'

# Get confidence score
uv run finagent query "text" -f json | jq '.confidence_score'

# Count findings
uv run finagent query "text" -f json | jq '.key_findings | length'
```

## Color Coding

| Color | Meaning |
|-------|---------|
| 🟢 Green | Primary sources, High confidence |
| 🟡 Yellow | Secondary sources, Medium confidence |
| 🔴 Red | Low confidence, Errors |
| 🔵 Blue | Tertiary sources, Links |
| ⚪ White | Main content |
| ⚫ Gray | Metadata |

## Citation Authority Levels

| Level | Color | Example |
|-------|-------|---------|
| **Primary** | Green | Official enforcement docs, Court judgments |
| **Secondary** | Yellow | News articles, Regulatory announcements |
| **Tertiary** | Blue | Legal commentary, Analysis |

## Environment Variables

```bash
# Backend API URL (default: http://localhost:8000)
export FINAGENT_API_URL=http://localhost:8000

# OpenAI API Key (required)
export OPENAI_API_KEY=sk-...
```

## Troubleshooting

### CLI won't start
```bash
cd backend
uv sync
```

### Backend connection error
```bash
# Check backend is running
curl http://localhost:8000/health

# Start backend
uv run uvicorn finagent.main:app --reload
```

### Chinese characters display incorrectly
```bash
export LANG=zh_TW.UTF-8
export LC_ALL=zh_TW.UTF-8
```

### Query timeout
- Reduce `--max-results`
- Use more specific query
- Add date range filters

## Piping & Scripting

### Basic Piping
```bash
# Save to file
uv run finagent query "text" -f markdown > report.md

# Extract specific fields
uv run finagent query "text" -f json | jq '.executive_summary'

# Count citations
uv run finagent query "text" -f json | jq '.citations | length'

# Filter citations by type
uv run finagent query "text" -f json | jq '.citations[] | select(.type=="enforcement_document")'
```

### Batch Processing
```bash
#!/bin/bash
# Batch query multiple banks

banks=("玉山銀行" "國泰世華銀行" "台新銀行")

for bank in "${banks[@]}"; do
  echo "Querying $bank..."
  uv run finagent query "$bank 裁罰" -f json > "${bank}_report.json"
done
```

### Scheduled Queries
```bash
# Add to crontab for daily reports
0 9 * * * cd /path/to/finagent/backend && uv run finagent query "昨日裁罰案件" -f markdown | mail -s "Daily Report" user@example.com
```

## Aliases for Convenience

Add to `.bashrc` or `.zshrc`:

```bash
# Short aliases
alias fa='uv run finagent'
alias faq='uv run finagent query'
alias faj='uv run finagent query --format json'
alias fam='uv run finagent query --format markdown'

# Usage examples:
# fa                    # Start REPL
# faq "玉山銀行"        # Quick query
# faj "text" | jq       # JSON output
# fam "text" > file.md  # Markdown to file
```

## Help Resources

| Resource | Command/Link |
|----------|--------------|
| CLI Help | `/help` in REPL or `finagent --help` |
| Query Help | `finagent query --help` |
| Full Guide | [CLI_GUIDE.md](CLI_GUIDE.md) |
| Demo | [CLI_DEMO.md](CLI_DEMO.md) |
| Implementation | [CLI_IMPLEMENTATION_SUMMARY.md](CLI_IMPLEMENTATION_SUMMARY.md) |
| API Docs | http://localhost:8000/docs |

## Quick Start Checklist

- [ ] Install dependencies: `cd backend && uv sync`
- [ ] Set OpenAI API key in `.env`
- [ ] Start backend: `uv run uvicorn finagent.main:app --reload`
- [ ] Open new terminal
- [ ] Start CLI: `uv run finagent`
- [ ] Try first query: `玉山銀行洗錢防制裁罰`
- [ ] Explore commands: `/help`
- [ ] View history: `/history`
- [ ] Check config: `/config`

## Pro Tips

1. **Tab completion** - Press Tab after `/` to see all commands
2. **Arrow keys** - Use ↑/↓ to navigate command history
3. **Direct input** - No need for `/query`, just type your question
4. **JSON + jq** - Powerful data extraction and filtering
5. **Markdown export** - Great for creating reports
6. **Regulator filter** - Narrow results by FSC/CBC/FTC
7. **Date ranges** - Focus on specific time periods
8. **Confidence check** - Green bar = reliable results
9. **Citation review** - Always verify source authority
10. **Save sessions** - Use `/export` for important research

---

**Get Started:** `uv run finagent` 🚀
