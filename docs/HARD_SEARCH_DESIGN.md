# Hard Search Implementation - Design Document

**Date:** 2025-11-14
**Feature:** Grep-based deep search for precise keyword matching
**Purpose:** Complement vector search with exact text matching for critical keywords

---

## Overview

### Problem

Vector search (semantic similarity) can miss exact keyword matches, especially for:
- Specific entity names (e.g., "創投", "創業投資")
- Technical terms with precise meanings
- Proper nouns and institution names
- Legal terminology requiring exact matches

### Solution

Implement a **Hard Search** system that:
1. Directly reads document files from disk
2. Uses grep-like pattern matching for must-have keywords
3. Extracts surrounding context around matches
4. Converts matches into RetrievedChunk format
5. Merges results with vector search results

---

## Architecture

### Component: HardSearcher

**Location:** `src/finagent/document_processing/hard_searcher.py`

**Purpose:** Grep-based file search with context extraction

**Methods:**

```python
class HardSearcher:
    def __init__(self, db_path: str):
        """Initialize with database connection for file paths."""

    def search(
        self,
        keywords: list[str],
        max_results: int = 10,
        context_lines: int = 3,
    ) -> list[RetrievedChunk]:
        """
        Search for exact keyword matches in documents.

        Args:
            keywords: Must-have keywords to search for
            max_results: Maximum number of chunks to return
            context_lines: Number of lines before/after match to include

        Returns:
            List of RetrievedChunk objects with matches
        """

    def _get_indexed_documents(self) -> list[dict]:
        """Get all indexed documents from database."""

    def _search_file(
        self,
        file_path: str,
        keywords: list[str],
        context_lines: int,
    ) -> list[dict]:
        """Search single file for keywords."""

    def _extract_context(
        self,
        lines: list[str],
        match_line_num: int,
        context_lines: int,
    ) -> str:
        """Extract context around match line."""

    def _convert_to_chunks(
        self,
        matches: list[dict],
        max_results: int,
    ) -> list[RetrievedChunk]:
        """Convert raw matches to RetrievedChunk format."""
```

---

## Integration Points

### 1. Action Agent Enhancement

**File:** `src/finagent/agents/action_agent.py`

**Change:** Add hard search execution when `use_hard_search` flag is True

```python
def research(self, state: AgentState) -> AgentState:
    # ... existing vector search ...

    # Hard search if enabled
    plan = state.get("plan", {})
    if plan.get("use_hard_search"):
        plan_analysis = state.get("plan_analysis", {})
        must_have_keywords = plan_analysis.get("must_have_keywords", [])

        if must_have_keywords:
            hard_searcher = HardSearcher(db_path="data/finagent.db")
            hard_chunks = hard_searcher.search(
                keywords=must_have_keywords,
                max_results=plan.get("max_results", 5),
            )

            # Merge with vector search results
            all_chunks = self._merge_chunks(retrieved_chunks, hard_chunks)
            state["retrieved_chunks"] = all_chunks
```

### 2. Chunk Merging Strategy

**Approach:** Combine vector and hard search results, deduplicating by file+position

```python
def _merge_chunks(
    self,
    vector_chunks: list[RetrievedChunk],
    hard_chunks: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """
    Merge vector and hard search chunks.

    Strategy:
    1. Keep all hard search chunks (high priority)
    2. Add vector chunks that don't overlap
    3. Sort by relevance score
    4. Limit to max_results
    """
```

---

## Search Algorithm

### File Search Process

1. **Get candidate files** from database (indexed documents only)
2. **For each file**:
   - Read file content (with error handling for encoding)
   - Split into lines
   - Search for any keyword match (OR logic)
   - Extract context (N lines before/after)
   - Record match metadata (line number, keyword matched)
3. **Convert matches** to RetrievedChunk format
4. **Score chunks** based on:
   - Number of keywords matched
   - Position in document
   - Length of context
5. **Return top N results**

### Keyword Matching

```python
# OR logic: Match any of the keywords
for keyword in keywords:
    if keyword in line:
        # Match found
        matches.append({
            "file_path": file_path,
            "line_num": line_num,
            "keyword": keyword,
            "line_text": line,
        })
```

### Context Extraction

```python
# Extract N lines before and after match
start = max(0, match_line_num - context_lines)
end = min(len(lines), match_line_num + context_lines + 1)
context = "\n".join(lines[start:end])
```

---

## Data Model

### Match Object (Internal)

```python
{
    "file_path": "data/documents/裁罰歷史資料/創投_2020.txt",
    "filename": "創投_2020.txt",
    "line_num": 42,
    "keyword": "創業投資",
    "line_text": "對創業投資事業管理規則第10條...",
    "context": "...\n前後3行文字\n...",
    "doc_metadata": {
        "document_type": "裁罰書",
        "issuing_authority": "金管會",
        "document_date": "2020-05-15",
    }
}
```

### RetrievedChunk (Output)

```python
RetrievedChunk(
    text=match["context"],
    score=0.95,  # Hard search = high score
    metadata={
        "filename": match["filename"],
        "file_path": match["file_path"],
        "line_num": match["line_num"],
        "matched_keyword": match["keyword"],
        "document_type": match["doc_metadata"]["document_type"],
        "issuing_authority": match["doc_metadata"]["issuing_authority"],
        "search_method": "hard_search",  # Mark as hard search
    }
)
```

---

## Performance Considerations

### Optimization Strategies

1. **Limit File Search**
   - Only search indexed documents (DB flag)
   - Skip files >10MB
   - Timeout per file (5 seconds)

2. **Efficient Reading**
   - Use UTF-8 encoding with error handling
   - Read line-by-line (don't load entire file)
   - Stop after N matches per file

3. **Caching**
   - Cache file list from database
   - Consider caching frequently accessed files

### Expected Performance

| Metric | Value |
|--------|-------|
| Documents to search | ~500 files |
| Average file size | 5KB |
| Total data | ~2.5MB |
| Expected time | 20-30 seconds |
| Max time (timeout) | 60 seconds |

---

## Error Handling

### File Access Errors

```python
try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
except FileNotFoundError:
    logger.warning(f"File not found: {file_path}")
    continue
except UnicodeDecodeError:
    # Try different encodings
    try:
        with open(file_path, "r", encoding="big5") as f:
            lines = f.readlines()
    except:
        logger.error(f"Cannot decode file: {file_path}")
        continue
```

### Timeout Protection

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("File search exceeded time limit")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second timeout

try:
    # Perform hard search
    results = hard_searcher.search(keywords)
finally:
    signal.alarm(0)  # Cancel alarm
```

---

## Testing Strategy

### Test Cases

1. **Exact Match Test**
   - Query: "創投公司裁罰"
   - Expected: Find documents with exact "創投" or "創業投資"
   - Verify: Matches contain must-have keywords

2. **Context Extraction Test**
   - Verify: Context includes N lines before/after match
   - Verify: No truncation in middle of sentences

3. **Merge Test**
   - Vector search finds 5 documents
   - Hard search finds 3 documents (2 overlap)
   - Expected: 6 unique documents total

4. **Performance Test**
   - Search all 500 documents
   - Expected: Complete in <30 seconds
   - Timeout: 60 seconds

### Edge Cases

- File not found (deleted after indexing)
- Empty file
- File with encoding errors
- Very large file (>10MB)
- No keyword matches
- Multiple matches in same file

---

## Integration with Workflow

### Updated Workflow

```
Planning Agent
  ↓
  Sets use_hard_search=True for complex queries
  ↓
Action Agent
  ↓
  1. Vector Search (semantic)
  2. Hard Search (if enabled)
  3. Merge Results
  4. Extract Citations
  ↓
Validation Agent
  ↓
  Validates both vector and hard search results
  ↓
Answer Agent
```

### Processing Steps Updates

```python
# In action_agent.py
if plan.get("use_hard_search"):
    state["processing_steps"].append(
        f"行動代理：執行深度搜索，搜尋關鍵字 {must_have_keywords}"
    )

    hard_chunks = hard_searcher.search(must_have_keywords)

    state["processing_steps"].append(
        f"行動代理：深度搜索找到 {len(hard_chunks)} 筆精確匹配"
    )
```

---

## Configuration

### Environment Variables (Optional)

```bash
# Hard search settings
HARD_SEARCH_ENABLED=true
HARD_SEARCH_CONTEXT_LINES=3
HARD_SEARCH_MAX_RESULTS=10
HARD_SEARCH_TIMEOUT_SECONDS=60
HARD_SEARCH_MAX_FILE_SIZE_MB=10
```

### Code Constants

```python
# In hard_searcher.py
DEFAULT_CONTEXT_LINES = 3
DEFAULT_MAX_RESULTS = 10
FILE_TIMEOUT_SECONDS = 60
MAX_FILE_SIZE_MB = 10
MAX_MATCHES_PER_FILE = 5
```

---

## Success Metrics

### Before Hard Search

**Query:** "金管會對創投公司的裁罰有哪些？"
- Vector search: 3 documents (證券投資信託, wrong type)
- Validation: ⚠️ Missing must-have keywords
- User satisfaction: Low (wrong results)

### After Hard Search

**Query:** "金管會對創投公司的裁罰有哪些？"
- Vector search: 3 documents (證券投資信託)
- Hard search: 5 documents (創投, correct type)
- Merged: 8 unique documents
- Validation: ✅ Contains must-have keywords
- User satisfaction: High (correct results)

---

## Future Enhancements

### Phase 2

1. **Regex Support** - Allow pattern matching beyond exact strings
2. **Fuzzy Matching** - Handle typos and variations
3. **Proximity Search** - Keywords within N words of each other
4. **Highlighted Matches** - Show matched keywords in context

### Phase 3

1. **Parallel File Processing** - Use multiprocessing for faster search
2. **Index Pre-filtering** - Use Jieba to create keyword index
3. **Smart Caching** - Cache search results for common queries

---

## Implementation Checklist

- [ ] Create `hard_searcher.py` module
- [ ] Implement `HardSearcher` class
- [ ] Add database integration for file paths
- [ ] Implement context extraction
- [ ] Implement chunk merging in action agent
- [ ] Add processing steps logging
- [ ] Write unit tests
- [ ] Test with complex queries
- [ ] Measure performance
- [ ] Update documentation

---

**Design Date:** 2025-11-14
**Status:** 📋 DESIGN COMPLETE
**Next:** Implementation
