# Dynamic Planning Web UI Integration

This document describes the integration of the Dynamic Planning system (Query Analysis + Tool Selection) into the Web UI.

## Overview

The Dynamic Planning system automatically analyzes user queries and selects the most appropriate tools to execute them. This information is now displayed in real-time in the Web UI.

## Architecture Components

### Backend Changes

1. **WebSocket Callback Enhancement** ([src/finagent/api/routes/websocket.py](src/finagent/api/routes/websocket.py))
   - Added `on_dynamic_plan_analysis()` method to `WebSocketUICallback`
   - Sends `dynamic_plan_analysis` WebSocket event with:
     - `query_analysis`: Intent, entities, temporal constraints, complexity
     - `selected_tools`: Tools chosen with reasons and parameters

2. **Query Analyzer** ([src/finagent/agents/query_analyzer.py](src/finagent/agents/query_analyzer.py))
   - Classifies queries into 6 intent types:
     - `general_search`: General keyword search
     - `temporal`: Time-related queries (latest, past, specific date)
     - `comprehensive`: Complete listings (all records)
     - `specific_file`: Specific file access
     - `comparison`: Multi-entity comparison
     - `entity_specific`: Specific entity information
   - Extracts entities, temporal constraints, complexity level

3. **Tool Selector** ([src/finagent/agents/tool_selector.py](src/finagent/agents/tool_selector.py))
   - Selects appropriate tools based on query analysis
   - 6 available tools:
     - `vector_search`: Semantic vector search
     - `metadata_search`: Metadata-based filtering (temporal queries)
     - `list_documents`: Exhaustive document listing
     - `read_file`: Direct file access
     - `hybrid_search`: Two-stage search (metadata + vector)
     - `multi_entity_search`: Parallel multi-entity comparison

### Frontend Changes

1. **Type Definitions** ([frontend/src/types/query.ts](frontend/src/types/query.ts))
   ```typescript
   interface DynamicQueryAnalysis {
     intent: string
     entities: string[]
     has_temporal_constraint: boolean
     temporal_type: string | null
     complexity: 'simple' | 'medium' | 'complex'
     requires_multi_entity: boolean
     requires_exhaustive_search: boolean
   }

   interface SelectedTool {
     tool_name: string
     reason: string
     parameters: Record<string, any>
     execution_order: number
   }

   interface DynamicPlanAnalysis {
     query_analysis: DynamicQueryAnalysis
     selected_tools: SelectedTool[]
   }
   ```
   - Added `dynamic_plan_analysis` to `WSMessageType`

2. **DynamicPlanPanel Component** ([frontend/src/components/query/DynamicPlanPanel.tsx](frontend/src/components/query/DynamicPlanPanel.tsx))
   - Displays query analysis results:
     - Intent badge with color coding
     - Extracted entities
     - Complexity indicator
     - Feature tags (temporal, multi-entity, exhaustive)
   - Shows selected tools:
     - Tool name with icon
     - Selection reason
     - Parameters used
     - Execution order

3. **QueryPage Integration** ([frontend/src/pages/QueryPage.tsx](frontend/src/pages/QueryPage.tsx))
   - Added state management for `dynamicPlan`
   - Handles `dynamic_plan_analysis` WebSocket messages
   - Displays DynamicPlanPanel below Research Plan Panel

## Visual Design

### Query Analysis Section

- **Intent Badge**: Color-coded by intent type
  - Blue: Temporal
  - Purple: Comprehensive
  - Green: Specific file
  - Orange: Comparison
  - Indigo: Entity-specific
  - Gray: General search

- **Complexity Badge**: Traffic light colors
  - Green: Simple
  - Yellow: Medium
  - Red: Complex

- **Feature Tags**: Small badges indicating special requirements
  - Clock icon: Temporal constraint
  - Tag icon: Multi-entity
  - Search icon: Exhaustive search

### Selected Tools Section

- **Tool Cards**: Each tool displayed with:
  - Icon emoji (🔍 🔄 📋 📄 etc.)
  - Tool name (localized to Traditional Chinese)
  - Execution order number
  - Selection reason
  - Parameters (key-value pairs)

## Example Queries and Tool Selection

### Query 1: Temporal/Latest
**Query**: "玉山銀行最近一次的罰款紀錄"

**Analysis**:
- Intent: `temporal`
- Entities: ["玉山銀行"]
- Temporal type: `latest`
- Complexity: `medium`

**Selected Tool**: `metadata_search`
- Reason: 查詢最近一次記錄
- Parameters: `{ entity: "玉山銀行" }`

### Query 2: Comprehensive Listing
**Query**: "玉山銀行過去所有的裁罰紀錄"

**Analysis**:
- Intent: `comprehensive`
- Entities: ["玉山銀行"]
- Requires exhaustive: `true`
- Complexity: `medium`

**Selected Tool**: `list_documents`
- Reason: 需要完整清單
- Parameters: `{ entity: "玉山銀行" }`

### Query 3: Specific File
**Query**: "「國泰世華銀行_內線交易_2021.txt」這個檔案的摘要"

**Analysis**:
- Intent: `specific_file`
- Entities: ["國泰世華銀行"]
- Complexity: `medium`

**Selected Tool**: `vector_search` (fallback)
- Reason: 一般語義搜尋
- Parameters: `{ top_k: 10, relevance_threshold: 0.8 }`

### Query 4: Multi-Entity Comparison
**Query**: "玉山銀行與國泰世華銀行的裁罰紀錄比較"

**Analysis**:
- Intent: `comparison`
- Entities: ["玉山銀行", "國泰世華銀行"]
- Requires multi-entity: `true`
- Complexity: `medium`

**Selected Tool**: `multi_entity_search`
- Reason: 比較查詢需要多實體搜尋
- Parameters: `{ entities: ["玉山銀行", "國泰世華銀行"], top_k_per_entity: 5 }`

## Testing the Feature

### Method 1: Demo Script (Backend Only)

Run the demo script to see query analysis and tool selection output:

```bash
uv run python tests/test_dynamic_planning_demo.py
```

This will analyze 4 test queries and show the JSON payload that would be sent to the frontend.

### Method 2: Full Web UI Test

**Prerequisites**:
- Backend server running on port 8000
- Frontend dev server running

**Steps**:
1. Start the backend (if not already running):
   ```bash
   ENABLE_DEMO_DELAY=true uv run python -m uvicorn finagent.main:app --reload --port 8000
   ```

2. Start the frontend (if not already running):
   ```bash
   npm --prefix frontend run dev
   ```

3. Open browser to `http://localhost:3000`

4. Go to the Query page

5. Enter one of the test queries:
   - "玉山銀行最近一次的罰款紀錄"
   - "玉山銀行過去所有的裁罰紀錄"
   - "玉山銀行與國泰世華銀行的裁罰紀錄比較"

6. Observe the **動態規劃分析** panel appear with:
   - Query analysis details
   - Selected tools with parameters

### Method 3: WebSocket Client Test

Test the WebSocket connection directly:

```bash
uv run python tests/test_dynamic_planning_ws_client.py
```

This will connect to the WebSocket endpoint and display all messages received.

## Integration Status

### ✅ Completed

1. Backend WebSocket callback enhanced
2. Frontend types updated
3. DynamicPlanPanel component created
4. QueryPage integration completed
5. Test scripts created

### ⚠️ Pending

To fully activate the feature, the orchestrator needs to call the query analyzer and tool selector:

```python
# In orchestrator or planning agent
from finagent.agents.query_analyzer import QueryAnalyzer
from finagent.agents.tool_selector import ToolSelector

analyzer = QueryAnalyzer()
selector = ToolSelector()

# During query processing
analysis = await analyzer.analyze(query.text)
selected_tools = await selector.select_tools(query.text, analysis)

# Send to UI callback
if self.ui_callback:
    await self.ui_callback.on_dynamic_plan_analysis(
        query_analysis=analysis.model_dump(),
        selected_tools=selected_tools
    )
```

## Visual Preview

When a query is submitted, users will see:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 動態規劃分析                                        2 個工具    │
├─────────────────────────────────────────────────────────────────┤
│ ℹ️ 查詢分析                                                       │
│                                                                 │
│ 🏷️ 意圖: [比較分析]           ⏱️ 複雜度: [medium]                │
│                                                                 │
│ 🏷️ 實體:                                                         │
│   [玉山銀行] [國泰世華銀行]                                        │
│                                                                 │
│ Features: [🏷️ 多實體]                                            │
├─────────────────────────────────────────────────────────────────┤
│ 🔧 選擇的工具                                                     │
│                                                                 │
│ 🔀 多實體搜尋                                             #1     │
│    比較查詢需要多實體搜尋                                          │
│    entities: 玉山銀行, 國泰世華銀行  top_k_per_entity: 5          │
└─────────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Transparency**: Users can see how their query is being interpreted
2. **Trust**: Understanding tool selection builds confidence in results
3. **Debugging**: Developers can verify correct tool selection
4. **Education**: Users learn how the system works

## Future Enhancements

1. **Tool Execution Feedback**: Show which tools succeeded/failed
2. **Alternative Suggestions**: If tool selection seems wrong, suggest query refinements
3. **Manual Override**: Allow users to manually select tools (advanced mode)
4. **Performance Metrics**: Show execution time per tool
5. **Cost Tracking**: Display API call costs per query
