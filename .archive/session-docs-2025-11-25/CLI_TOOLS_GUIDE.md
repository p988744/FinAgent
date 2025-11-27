# FinAgent CLI Tools Guide

**Date:** 2025-01-21
**Version:** v1.1.1

---

## Overview

FinAgent provides two powerful CLI tools for interacting with the knowledge base:

1. **`cli_research.py`** - Comprehensive research with Plan-and-Execute workflow
2. **`cli_retrieval.py`** - Direct document search with manual tool selection

---

## 1. Research CLI (`cli_research.py`)

### Purpose
Ask research questions and get comprehensive, well-structured answers using the Plan-and-Execute workflow with Query Analyzer.

### Features
- 🔍 **Query Analysis** - Understands your query before planning
- 📋 **Smart Planning** - Creates a multi-step research plan
- ⚙️  **Parallel Execution** - Executes tasks efficiently
- 📝 **Structured Reports** - Generates comprehensive research reports

### Usage

#### Command Line Mode
```bash
# Basic usage
python scripts/cli_research.py "your research question here"

# With verbose output (shows detailed progress)
python scripts/cli_research.py "your research question here" --verbose
python scripts/cli_research.py "your research question here" -v
```

#### Interactive Mode
```bash
python scripts/cli_research.py
```

Then follow the prompts to enter your questions.

### Examples

**Example 1: Factual Research**
```bash
python scripts/cli_research.py "2020年玉山銀行洗錢防制裁罰"
```

**Output:**
```
🔍 Query Understanding
────────────────────────────────────────────────────────────────────────────────
  Type:       factual
  Strategy:   hybrid
  Complexity: simple
  Entities:   2020年, 玉山銀行, 洗錢防制, 裁罰

  💡 The query seeks specific information about a 2020 case involving 玉山銀行...

📋 Research Plan
────────────────────────────────────────────────────────────────────────────────
  The system will execute 5 tasks:

  1. 🔍🔎 [hybrid_search] Search the document corpus...
  2. 🔍 [retriever] Filter the retrieved results...
  ...

📝 Research Results
================================================================================
[Comprehensive research report with analysis and citations]
```

**Example 2: Analytical Research**
```bash
python scripts/cli_research.py "分析銀行業洗錢防制的主要問題"
```

**Example 3: Comparative Research**
```bash
python scripts/cli_research.py "比較玉山銀行和台新銀行在內部控制方面的裁罰案件"
```

### Output Format

The research CLI provides:
1. **Query Understanding** - How the system interprets your query
2. **Research Plan** - The steps that will be executed
3. **Progress Indicator** - Real-time progress bar
4. **Research Results** - Comprehensive report with:
   - Executive Summary
   - Key Findings (table format)
   - Detailed Analysis
   - Conclusions
   - Citations

---

## 2. Retrieval CLI (`cli_retrieval.py`)

### Purpose
Search and retrieve documents directly from the knowledge base with manual control over which search tool to use.

### Features
- 🤖 **Auto Mode** - Let the system choose the best tool
- 🔍 **Semantic Search** - Conceptual/analytical queries
- 🔎 **Keyword Search** - Exact term matching
- 🔍🔎 **Hybrid Search** - Combined BM25 + Vector search

### Usage

#### Command Line Mode
```bash
# Auto mode (default - system chooses best tool)
python scripts/cli_retrieval.py "search query"

# Manual tool selection
python scripts/cli_retrieval.py "search query" --tool hybrid
python scripts/cli_retrieval.py "search query" --tool semantic
python scripts/cli_retrieval.py "search query" --tool keyword

# Specify number of results
python scripts/cli_retrieval.py "search query" --num 10

# Combined options
python scripts/cli_retrieval.py "search query" --tool hybrid --num 5
```

#### Interactive Mode
```bash
python scripts/cli_retrieval.py
```

Then follow the prompts to enter your searches.

#### Help
```bash
python scripts/cli_retrieval.py --help
```

### Search Tools

#### 1. Auto Mode (Default)
- Uses Query Analyzer to select the best tool
- Analyzes your query and provides reasoning
- Recommended for most use cases

```bash
python scripts/cli_retrieval.py "2020年玉山銀行洗錢防制裁罰"
```

**Output:**
```
🤖 Analyzing query to select best tool...

📊 Query Analysis:
   Type:       factual
   Strategy:   hybrid
   Complexity: simple
   Entities:   2020年, 玉山銀行, 洗錢防制, 裁罰

💡 The query seeks specific information about a 2020 case...

✅ Selected tool: hybrid
```

#### 2. Semantic Search
- Best for: Conceptual/analytical queries
- Example queries:
  - "分析銀行業洗錢防制的主要問題"
  - "內部控制缺失的法律責任"
  - "金融監管趨勢分析"

```bash
python scripts/cli_retrieval.py "分析銀行業洗錢防制的主要問題" --tool semantic
```

#### 3. Keyword Search
- Best for: Finding documents with specific exact terms (Boolean AND)
- Example queries:
  - "找出包含「金管會」和「裁罰」的文件"
  - "搜尋「內部控制」和「缺失」"

```bash
python scripts/cli_retrieval.py "找出包含「金管會」和「裁罰」的文件" --tool keyword
```

#### 4. Hybrid Search (Recommended)
- Best for: Queries with both specific terms AND concepts
- Combines: 60% semantic + 40% keyword (BM25)
- Example queries:
  - "2020年玉山銀行洗錢防制裁罰"
  - "2023年所有裁罰金額超過100萬的案件"

```bash
python scripts/cli_retrieval.py "2020年玉山銀行洗錢防制裁罰" --tool hybrid
```

### Examples

**Example 1: Auto Mode (System Chooses)**
```bash
python scripts/cli_retrieval.py "2020年玉山銀行洗錢防制裁罰" --num 3
```

**Example 2: Hybrid Search (Explicit)**
```bash
python scripts/cli_retrieval.py "2020年玉山銀行洗錢防制裁罰" --tool hybrid --num 5
```

**Example 3: Semantic Search**
```bash
python scripts/cli_retrieval.py "分析銀行業洗錢防制問題" --tool semantic --num 10
```

**Example 4: Keyword Search**
```bash
python scripts/cli_retrieval.py "金管會 裁罰 玉山銀行" --tool keyword
```

### Output Format

The retrieval CLI provides:
- Tool used (semantic, keyword, or hybrid)
- Number of documents found
- For each document:
  - Source file path
  - Content preview
  - Metadata (if available)

---

## Comparison: Research vs. Retrieval

| Feature | Research CLI | Retrieval CLI |
|---------|-------------|---------------|
| **Purpose** | Comprehensive research | Quick document search |
| **Query Analysis** | ✅ Yes | ✅ Yes (in auto mode) |
| **Planning** | ✅ Yes | ❌ No |
| **Multi-step Execution** | ✅ Yes | ❌ No |
| **Answer Synthesis** | ✅ Yes | ❌ No (returns raw documents) |
| **Tool Selection** | ✅ Automatic | ✅ Manual or Auto |
| **Speed** | Slower (~30-60s) | Faster (~3-10s) |
| **Output Format** | Structured report | Document list |
| **Best For** | Complex questions | Quick lookups |

---

## When to Use Which Tool?

### Use Research CLI When:
- ✅ You need a comprehensive answer
- ✅ Your question requires analysis or synthesis
- ✅ You want citations and structured reports
- ✅ You're okay with waiting ~30-60 seconds
- ✅ Example: "分析2020-2023年銀行業洗錢防制裁罰趨勢"

### Use Retrieval CLI When:
- ✅ You just want to find relevant documents
- ✅ You need quick results
- ✅ You want to control which search tool is used
- ✅ You're doing exploratory research
- ✅ Example: "找出所有包含玉山銀行的文件"

---

## Tips & Tricks

### Research CLI Tips

1. **Be Specific** - The more specific your question, the better the results
   ```bash
   # Good
   python scripts/cli_research.py "2020年玉山銀行因洗錢防制被罰的具體金額和原因"

   # Less good
   python scripts/cli_research.py "玉山銀行裁罰"
   ```

2. **Use Verbose Mode for Debugging**
   ```bash
   python scripts/cli_research.py "your question" --verbose
   ```

3. **Check Query Understanding** - The query insight tells you if the system understood your question correctly

### Retrieval CLI Tips

1. **Start with Auto Mode** - Let the system choose the tool
   ```bash
   python scripts/cli_retrieval.py "your search query"
   ```

2. **Use Hybrid for Most Queries** - It combines the best of both worlds
   ```bash
   python scripts/cli_retrieval.py "your search query" --tool hybrid
   ```

3. **Use Keyword for Exact Matches** - When you need ALL terms to appear
   ```bash
   python scripts/cli_retrieval.py "金管會 裁罰 2020" --tool keyword
   ```

4. **Adjust Number of Results** - More results = more comprehensive but slower
   ```bash
   python scripts/cli_retrieval.py "your search query" --num 10
   ```

---

## Troubleshooting

### Error: "Document index not available"
```bash
# Solution: Index documents first
uv run finagent reindex
```

### Error: "No results found"
```bash
# Try different search tools
python scripts/cli_retrieval.py "your query" --tool hybrid
python scripts/cli_retrieval.py "your query" --tool semantic

# Or increase number of results
python scripts/cli_retrieval.py "your query" --num 10
```

### Slow Performance
```bash
# For quick lookups, use retrieval CLI instead of research CLI
python scripts/cli_retrieval.py "your query"

# Or reduce number of results
python scripts/cli_retrieval.py "your query" --num 3
```

---

## Advanced Usage

### Batch Processing with Research CLI
```bash
# Create a file with queries (one per line)
cat > queries.txt <<EOF
2020年玉山銀行洗錢防制裁罰
分析銀行業內部控制問題
比較台新銀行和玉山銀行的裁罰案件
EOF

# Process each query
while read query; do
    echo "Processing: $query"
    python scripts/cli_research.py "$query" > "results_$(date +%s).txt"
done < queries.txt
```

### Batch Search with Retrieval CLI
```bash
# Search multiple terms
for term in "玉山銀行" "台新銀行" "國泰世華"; do
    python scripts/cli_retrieval.py "$term 洗錢防制" --tool hybrid --num 5 \
        > "search_${term}.txt"
done
```

### Exporting Results
```bash
# Save research results to file
python scripts/cli_research.py "your question" > research_report.txt

# Save retrieval results to file
python scripts/cli_retrieval.py "your search" --tool hybrid > search_results.txt
```

---

## Integration with Existing CLI

These tools complement the existing FinAgent CLI:

```bash
# Existing CLI (REPL mode)
uv run finagent

# New Research CLI (one-off research)
python scripts/cli_research.py "your question"

# New Retrieval CLI (quick search)
python scripts/cli_retrieval.py "your search"
```

---

## Next Steps

1. **Try the Research CLI** with a complex question
2. **Explore Retrieval CLI** with different tools
3. **Compare results** between auto and manual tool selection
4. **Provide feedback** on what works and what doesn't

---

## Changelog

**v1.1.1 (2025-01-21)**
- ✅ Added Query Analyzer integration
- ✅ Created Research CLI with Plan-and-Execute workflow
- ✅ Created Retrieval CLI with manual tool selection
- ✅ Added auto mode for tool selection
- ✅ Added progress indicators and formatting

---

**Need Help?**
- Run with `--help` flag for command-line help
- Check [QUERY_ANALYZER_FEATURE.md](QUERY_ANALYZER_FEATURE.md) for technical details
- See [CLAUDE.md](CLAUDE.md) for project documentation
