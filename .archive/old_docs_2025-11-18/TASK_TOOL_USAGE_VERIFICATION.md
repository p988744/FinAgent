# Task Tool Usage Verification - User Guide

## Overview

This feature allows users to **verify the tool usage** in each research task by expanding task details in the Research Plan panel. Users can see:

- **Request parameters** sent to retrieval tools
- **Execution results** with result counts and execution times
- **Sample retrieved documents** with relevance scores
- **Error messages** if tool execution failed

This transparency helps users verify that the system correctly understood their query and retrieved relevant documents.

## Visual Design

### Collapsed Task (Default State)

```
┌────────────────────────────────────────────────────────────────┐
│ ▶ ✅ 🔍 1. 搜尋玉山銀行相關裁罰文件              ~5s [已完成]  │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- `▶` - Chevron right icon (click to expand)
- `✅` - Status icon (pending/in_progress/completed/failed)
- `🔍` - Search method icon (vector/hybrid/hard search)
- Task description
- Estimated time
- Status badge

### Expanded Task (Shows Tool Usage)

```
┌────────────────────────────────────────────────────────────────┐
│ ▼ ✅ 🔍 1. 搜尋玉山銀行相關裁罰文件              ~5s [已完成]  │
│   ┌──────────────────────────────────────────────────────┐    │
│   │ 🔧 vector_search                      ✓ 8 個結果     │    │
│   │ ⏱️ 執行時間: 1250ms                                   │    │
│   │                                                        │    │
│   │ 📋 請求參數                                             │    │
│   │ {                                                      │    │
│   │   "query": "玉山銀行洗錢防制裁罰",                      │    │
│   │   "n_results": 10,                                     │    │
│   │   "relevance_threshold": 0.8                           │    │
│   │ }                                                      │    │
│   │                                                        │    │
│   │ 📄 檢索結果範例 (前 3 筆)                                │    │
│   │ ┌────────────────────────────────────────────────┐    │    │
│   │ │ 玉山銀行_洗錢防制裁罰_2020.txt              92% │    │    │
│   │ │ 金管會於2020年9月15日以金管銀法字第...          │    │    │
│   │ └────────────────────────────────────────────────┘    │    │
│   │                                                        │    │
│   │ 💡 驗證提示：                                           │    │
│   │ 您可以檢查上述請求參數和結果，確認系統是否正確理解     │    │
│   │ 您的查詢並檢索到相關文件。                              │    │
│   └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

**Expanded Elements:**
- `▼` - Chevron down icon (click to collapse)
- Tool name and result count
- Execution time
- Request parameters (JSON format)
- Sample results with relevance scores
- Verification tip

## User Workflow

### Step 1: Submit Query

1. Enter query in the Query page
2. Click "送出查詢"
3. Wait for Research Plan to be created

### Step 2: View Research Plan

The Research Plan panel shows:
- Query analysis (keywords, jurisdiction, complexity)
- List of research tasks with estimated times

### Step 3: Expand Task to Verify Tool Usage

1. **Click on a task** to expand it
2. **Review request parameters** - Verify the system understood your intent
3. **Check sample results** - Ensure retrieved documents are relevant
4. **Verify relevance scores** - Higher is better (shown as percentage)
5. **Read snippets** - Preview document content

### Step 4: Verify Results are Trustworthy

Ask yourself:
- ✅ Do the request parameters match my query intent?
- ✅ Are the retrieved documents relevant to my question?
- ✅ Are the relevance scores high enough (>80% is good)?
- ✅ Do the snippets contain information I'm looking for?

If any of these are ❌ NO, the final answer may be unreliable.

## What Information is Displayed

### 1. Tool Name

Shows which retrieval tool was used:
- `vector_search` - Semantic vector search
- `hybrid_search` - Two-stage search (metadata + vector)
- `hard_search` - Metadata-based filtering
- `multi_entity_search` - Parallel multi-entity comparison

### 2. Request Parameters

Shows exact parameters sent to the tool:

**Vector Search:**
```json
{
  "query": "玉山銀行洗錢防制裁罰",
  "n_results": 10,
  "relevance_threshold": 0.8
}
```

**Hybrid Search:**
```json
{
  "metadata_filter": {"keywords": ["洗錢防制"]},
  "vector_query": "裁罰案件",
  "n_results": 5
}
```

### 3. Execution Results

For successful execution:
- ✓ Result count (e.g., "8 個結果")
- ⏱️ Execution time (e.g., "1250ms")

For failed execution:
- ✗ Error message (e.g., "檢索結果為空：未找到符合條件的文件")

### 4. Sample Results

Shows up to 3 sample documents with:
- **Source filename** - Document identifier
- **Relevance score** - How well it matches the query (0-100%)
- **Snippet** - Preview of document content (truncated to 2 lines)

Example:
```
┌────────────────────────────────────────────────────────────┐
│ 玉山銀行_洗錢防制裁罰_2020.txt                      92%   │
│ 金管會於2020年9月15日以金管銀法字第10902345678號函...  │
└────────────────────────────────────────────────────────────┘
```

## Interpreting Relevance Scores

Relevance scores are shown as percentages (0-100%):

- **90-100%** - Highly relevant (excellent match)
- **80-89%** - Very relevant (good match)
- **70-79%** - Moderately relevant (acceptable match)
- **<70%** - Low relevance (may not be helpful)

**Note:** The system filters out results below the relevance threshold (default 0.8 = 80%).

## Common Scenarios

### Scenario 1: Successful Retrieval with Good Results

**What you see:**
- ✓ 8-10 results retrieved
- Relevance scores >85%
- Snippets clearly related to your query
- Execution time <2 seconds

**Interpretation:** The system correctly understood your query and found highly relevant documents. You can trust the final answer.

### Scenario 2: Low Result Count

**What you see:**
- ✓ Only 1-3 results retrieved
- Relevance scores 80-85%
- Snippets somewhat related

**Interpretation:** Limited information available. The answer may be incomplete. Consider refining your query or adding more documents.

### Scenario 3: Failed Retrieval

**What you see:**
- ✗ Error message: "檢索結果為空"
- No sample results

**Interpretation:** No relevant documents found. The query may be too specific, or the documents don't exist in the database. Try a broader query.

### Scenario 4: Mismatched Request Parameters

**What you see:**
- Request parameters don't match your intent
- Example: You asked about "玉山銀行" but parameters show "國泰世華銀行"

**Interpretation:** System misunderstood your query. The answer will be incorrect. Report this issue or rephrase your query.

## Technical Details

### Frontend Implementation

**Types:**
```typescript
interface ToolUsage {
  tool_name: string
  request_params: Record<string, any>
  result_count?: number
  execution_time_ms?: number
  sample_results?: Array<{
    source: string
    relevance?: number
    snippet?: string
  }>
  error?: string
}

interface PlanTask {
  id: number
  task: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  search_method: 'vector_search' | 'hard_search' | 'hybrid'
  estimated_time: number | null
  tool_usage?: ToolUsage
}
```

**State Management:**
- Task expansion state managed with `Set<number>` of expanded task IDs
- Tool usage data stored in `plan.tasks[].tool_usage`
- Real-time updates via `task_tool_usage` WebSocket messages

### Backend Integration

**WebSocket Callback:**
```python
async def on_task_tool_usage(self, task_id: int, tool_usage: dict[str, Any]):
    """Update task with tool usage information."""
    await self._send("task_tool_usage", {
        "task_id": task_id,
        "tool_usage": tool_usage,
    })
```

**Usage in Action Agent:**
```python
# After executing retrieval tool
tool_usage = {
    "tool_name": "vector_search",
    "request_params": {
        "query": query.text,
        "n_results": max_results,
        "relevance_threshold": threshold,
    },
    "result_count": len(retrieved_chunks),
    "execution_time_ms": execution_time,
    "sample_results": [
        {
            "source": chunk.source,
            "relevance": chunk.score,
            "snippet": chunk.content[:200],
        }
        for chunk in retrieved_chunks[:3]
    ],
}

if self.ui_callback:
    await self.ui_callback.on_task_tool_usage(
        task_id=task.id,
        tool_usage=tool_usage
    )
```

## Benefits for Users

### 1. Transparency

Users can see exactly how their query was processed:
- What tools were used
- What parameters were sent
- What documents were retrieved

### 2. Trust

By verifying the retrieval process, users can:
- Confirm the system understood their intent
- Check that relevant documents were found
- Assess the quality of source materials

### 3. Debugging

When results seem wrong, users can:
- Identify if the query was misunderstood
- Check if relevant documents exist
- Determine if the issue is in retrieval or synthesis

### 4. Learning

Users learn how the system works:
- Understanding different search methods
- Learning about relevance scoring
- Seeing how queries are decomposed into tasks

## Future Enhancements

### Planned Features

1. **Full Result Export**
   - Download complete list of retrieved documents (not just top 3)
   - Export in JSON or CSV format

2. **Document Preview**
   - Click on a sample result to view full document
   - Highlight matched sections

3. **Manual Refinement**
   - Edit request parameters and re-run retrieval
   - Add/remove documents from results

4. **Performance Analytics**
   - Show retrieval speed trends
   - Compare different search methods

5. **Quality Metrics**
   - Average relevance score across all results
   - Diversity score (how varied the sources are)

## Troubleshooting

### Issue 1: Tasks Not Expandable

**Symptoms:** Click on task does nothing

**Causes:**
- Task has no `tool_usage` data (tool hasn't executed yet)
- Task is still pending

**Solution:** Wait for task to complete execution before expanding

### Issue 2: Sample Results Not Showing

**Symptoms:** Tool usage expanded but no sample results

**Causes:**
- Tool execution returned 0 results
- Backend didn't send `sample_results` field

**Solution:** Check execution error message or backend logs

### Issue 3: Request Parameters Look Wrong

**Symptoms:** Parameters don't match your query

**Causes:**
- Query analysis misunderstood intent
- Bug in parameter mapping

**Solution:**
- Rephrase query to be more explicit
- Report issue with example query

### Issue 4: All Relevance Scores Low

**Symptoms:** All results <75% relevance

**Causes:**
- Query too vague or broad
- Documents don't contain exact matches
- Embedding model limitations

**Solution:**
- Use more specific keywords
- Add entity names explicitly
- Check if documents exist for this topic

## Testing the Feature

### Method 1: Demo Script (Backend Simulation)

```bash
uv run python tests/test_task_tool_usage_demo.py
```

Shows expected WebSocket messages and visual output.

### Method 2: Browser Testing (Full Integration)

**Prerequisites:**
- Backend running on port 8000
- Frontend running on port 3000

**Steps:**
1. Open http://localhost:3000
2. Go to Query page
3. Submit query: "玉山銀行洗錢防制裁罰"
4. Wait for Research Plan to appear
5. Click on a task to expand
6. Verify tool usage details are displayed

### Method 3: WebSocket Inspection

Use browser DevTools to inspect WebSocket messages:

1. Open DevTools (F12)
2. Go to Network tab → WS filter
3. Click on WebSocket connection
4. Go to Messages tab
5. Submit a query
6. Look for `task_tool_usage` messages

## Success Criteria

The feature is working correctly if:

1. ✅ Tasks with tool usage show chevron icon
2. ✅ Click expands/collapses task details
3. ✅ Request parameters are displayed in JSON format
4. ✅ Sample results show source, relevance, and snippet
5. ✅ Relevance scores are displayed as percentages
6. ✅ Error messages appear for failed executions
7. ✅ Multiple tasks can be expanded independently
8. ✅ Verification tip is always shown
9. ✅ Visual design matches specifications
10. ✅ No console errors or warnings

## Conclusion

The Task Tool Usage Verification feature provides crucial transparency into the RAG retrieval process. Users can now verify that:

- The system correctly understood their query
- Relevant documents were retrieved
- The retrieval quality is high enough to produce a trustworthy answer

This builds user trust and helps identify issues early in the query processing pipeline.
