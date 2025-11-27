# Frontend UI Design for Async API

**Date:** 2025-11-21
**API:** Celery + HTTP Async Research API
**Status:** Design Complete - Ready for Implementation

---

## Overview

Design a modern, professional frontend UI that leverages the existing **Celery async research API** with real-time status polling.

**Key Features:**
- Submit queries to async endpoint
- Real-time status polling with progress indicators
- Session history and management
- Clean, minimal design
- Responsive layout

---

## Architecture

### Current (WebSocket-based)
```
Frontend → WebSocket → Backend → LangGraph → Results
           (Real-time streaming)
```

### New (HTTP Async with Polling)
```
Frontend → HTTP POST → Celery Task → Background Processing
              ↓
       GET Status (polling every 3s)
              ↓
         Update UI with progress
              ↓
       Final Results
```

---

## API Integration

### Endpoints to Use

**1. Submit Query**
```typescript
POST /api/v1/research/query/async
Body: { query_text: string }
Response: {
  session_id: string
  celery_task_id: string
  status: "submitted"
  message: string
}
```

**2. Poll Status**
```typescript
GET /api/v1/research/status/{session_id}
Response: {
  session_id: string
  query_text: string
  status: "pending" | "in_progress" | "completed" | "failed"
  current_agent?: string
  agent_steps?: Array<{...}>
  result?: {...}
  error_message?: string
  started_at?: string
  completed_at?: string
  processing_time_seconds?: number
}
```

**3. Get History**
```typescript
GET /api/v1/research/history?limit=10
Response: {
  sessions: Array<{
    session_id: string
    query_text: string
    status: string
    started_at: string
    completed_at?: string
    processing_time_seconds?: number
  }>
  total: number
}
```

---

## UI Components

### 1. QuerySubmitCard
**Purpose:** Input field and submit button

**Features:**
- Large textarea for query input
- Submit button (disabled when querying)
- Character count
- Example queries dropdown

**State:**
- `isSubmitting: boolean`
- `queryText: string`

**Actions:**
- `onSubmit(queryText)` → Calls API and gets session_id

---

### 2. StatusCard
**Purpose:** Show current query status with progress

**Features:**
- Session ID display
- Status badge (pending/in_progress/completed/failed)
- Progress indicator (animated spinner or progress bar)
- Current agent/step display
- Elapsed time counter
- Cancel button (if supported)

**States:**
- **Pending:** "Queued..." (spinner)
- **In Progress:** "Processing... Current: {agent}" (progress)
- **Completed:** "✅ Completed in {time}s" (success)
- **Failed:** "❌ Error: {message}" (error)

**Props:**
```typescript
interface StatusCardProps {
  sessionId: string
  status: SessionStatus
  currentAgent?: string
  processingTime?: number
  error?: string
}
```

---

### 3. ResultsCard
**Purpose:** Display final results

**Features:**
- Query text recap
- Answer/response (formatted markdown)
- References/citations
- Metadata (processing time, tokens, cost)
- Bookmark button
- Copy to clipboard button

**Props:**
```typescript
interface ResultsCardProps {
  sessionId: string
  queryText: string
  result: {
    answer: string
    references?: Reference[]
    processing_time: number
  }
}
```

---

### 4. HistoryPanel (Sidebar)
**Purpose:** Show recent queries

**Features:**
- List of recent sessions (last 10)
- Session status indicators
- Click to load session results
- Time ago display ("2 minutes ago")
- Filter by status

**Props:**
```typescript
interface HistoryPanelProps {
  sessions: Session[]
  onSelectSession: (sessionId: string) => void
  selectedSessionId?: string
}
```

---

## Layout Design

### Desktop Layout
```
┌─────────────────────────────────────────────────────────┐
│  FinAgent Research                            [History] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  QuerySubmitCard                                   │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │ Enter your research question...              │ │ │
│  │  │                                              │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  [Submit]                                          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  StatusCard (if querying)                          │ │
│  │  Status: In Progress                               │ │
│  │  Current: Executor                                 │ │
│  │  [████████░░] 80%                                  │ │
│  │  Time: 45s                                         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ResultsCard (when complete)                       │ │
│  │  ✅ Completed in 48.3s                             │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │ Based on the regulatory documents...         │ │ │
│  │  │                                              │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  References: [1] [2] [3]                           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### History Sidebar (Collapsible)
```
┌─────────────────┐
│ Recent Queries  │
├─────────────────┤
│ ✅ 玉山銀行...  │
│    2 mins ago   │
├─────────────────┤
│ ⏳ 中信銀行...  │
│    5 mins ago   │
├─────────────────┤
│ ✅ 國泰世華...  │
│    1 hour ago   │
└─────────────────┘
```

---

## Custom Hook: useAsyncResearch

**Purpose:** Manage async research API calls and polling

```typescript
interface UseAsyncResearchReturn {
  // State
  isSubmitting: boolean
  isPolling: boolean
  sessionId: string | null
  status: SessionStatus | null
  currentAgent: string | null
  result: QueryResult | null
  error: string | null
  processingTime: number | null

  // Actions
  submitQuery: (queryText: string) => Promise<void>
  stopPolling: () => void
  clearSession: () => void

  // History
  history: Session[]
  loadSession: (sessionId: string) => Promise<void>
  refreshHistory: () => Promise<void>
}

function useAsyncResearch(): UseAsyncResearchReturn {
  // 1. Submit query → Get session_id
  // 2. Start polling status endpoint (every 3s)
  // 3. Update UI with status
  // 4. Stop polling when completed/failed
  // 5. Load history on mount
}
```

**Implementation:**
- Uses `fetch` for HTTP requests
- `setInterval` for polling (every 3 seconds)
- Cleanup on unmount
- Error handling

---

## Types

**File:** `frontend/src/types/async-api.ts`

```typescript
export interface AsyncQueryRequest {
  query_text: string
}

export interface AsyncQueryResponse {
  session_id: string
  celery_task_id: string
  status: string
  message: string
}

export interface SessionStatus {
  session_id: string
  query_text: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  current_agent?: string
  agent_steps?: AgentStep[]
  todos?: TodoItem[]
  activity_log?: ActivityLogItem[]
  research_plan?: any
  dynamic_plan?: any
  tool_executions?: any
  result?: SessionResult
  error_message?: string
  started_at?: string
  completed_at?: string
  processing_time_seconds?: number
}

export interface SessionResult {
  response: string
  citations?: Citation[]
  metadata?: {
    total_tokens?: number
    llm_cost_usd?: number
  }
}

export interface Session {
  session_id: string
  query_text: string
  status: string
  celery_task_id: string
  started_at: string
  completed_at?: string
  processing_time_seconds?: number
  is_bookmarked: boolean
  created_at: string
}

export interface HistoryResponse {
  sessions: Session[]
  total: number
}

export interface AgentStep {
  agent: string
  status: string
  started_at?: string
  completed_at?: string
}

export interface TodoItem {
  id: number
  description: string
  status: string
}

export interface ActivityLogItem {
  timestamp: string
  message: string
  level: string
}

export interface Citation {
  source: string
  content: string
  relevance?: number
}
```

---

## Implementation Plan

### Step 1: Create Types (30 min)
- Create `frontend/src/types/async-api.ts`
- Define all interfaces

### Step 2: Create useAsyncResearch Hook (1-2 hours)
- Create `frontend/src/hooks/useAsyncResearch.ts`
- Implement submit, poll, history logic
- Add error handling

### Step 3: Create UI Components (2-3 hours)
- `frontend/src/components/async/QuerySubmitCard.tsx`
- `frontend/src/components/async/StatusCard.tsx`
- `frontend/src/components/async/ResultsCard.tsx`
- `frontend/src/components/async/HistoryPanel.tsx`

### Step 4: Create AsyncResearchPage (1 hour)
- `frontend/src/pages/AsyncResearchPage.tsx`
- Integrate all components
- Layout with Tailwind CSS

### Step 5: Update App.tsx (15 min)
- Add route for async research page
- Or replace existing ResearchPage

### Step 6: Test (30 min)
- Submit test queries
- Verify polling works
- Test error handling
- Test history loading

**Total Time:** 5-7 hours

---

## Styling Guide

### Colors
- **Primary:** Blue-600 (#2563eb)
- **Success:** Green-600 (#16a34a)
- **Warning:** Yellow-500 (#eab308)
- **Error:** Red-600 (#dc2626)
- **Background:** Gray-50 (#f9fafb)
- **Cards:** White with shadow

### Typography
- **Headings:** font-bold text-gray-900
- **Body:** text-gray-700
- **Labels:** text-sm text-gray-500
- **Code:** font-mono bg-gray-100

### Components
- **Cards:** `bg-white rounded-lg shadow-md p-6`
- **Buttons:** `bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700`
- **Input:** `border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500`
- **Badge:** `px-2 py-1 rounded text-xs font-medium`

---

## User Flow

### Submit Query Flow
1. User enters query text
2. Click "Submit" button
3. API call to POST /api/v1/research/query/async
4. Receive session_id
5. Show StatusCard with "Queued..." status
6. Start polling GET /api/v1/research/status/{session_id}
7. Update StatusCard every 3 seconds
8. When status = "completed", show ResultsCard
9. Add to history sidebar

### View History Flow
1. Sidebar shows recent queries
2. User clicks on a past query
3. Load session status from API
4. Display results in ResultsCard
5. If still in progress, resume polling

---

## Error Handling

### Network Errors
- Show error toast/banner
- Retry button
- Fallback to offline mode (show cached history)

### API Errors
- 404: Session not found → Show error message
- 500: Server error → Show error with retry
- Timeout: Query too long → Show progress, keep polling

### User Errors
- Empty query → Validation message
- Query too short → Minimum length warning

---

## Progressive Enhancement

### Phase 1: Basic Async (MVP)
- Submit query
- Poll status
- Show results
- Basic history

### Phase 2: Enhanced UX
- Progress percentage
- Current agent display
- Estimated time remaining
- Cancel/pause query

### Phase 3: Advanced Features
- Bookmark queries
- Export results (PDF, Markdown)
- Share session link
- Query templates

---

## Advantages Over WebSocket

### Pros:
- ✅ Simpler implementation (no WebSocket management)
- ✅ Works with HTTP-only clients
- ✅ Better for intermittent connections
- ✅ Easier to debug (standard HTTP)
- ✅ Can resume from any page refresh

### Cons:
- ❌ Not real-time (3s polling delay)
- ❌ More server requests (polling overhead)
- ❌ No push notifications

**Conclusion:** Good for v1.1, can add WebSocket in v1.2

---

## Testing Checklist

### Functionality
- [ ] Submit query successfully
- [ ] Status polling updates UI
- [ ] Results display correctly
- [ ] History loads and displays
- [ ] Error handling works

### UX
- [ ] Loading states clear
- [ ] Status indicators intuitive
- [ ] Responsive design
- [ ] Smooth transitions
- [ ] Clear error messages

### Performance
- [ ] Polling doesn't block UI
- [ ] History loads quickly
- [ ] No memory leaks
- [ ] Efficient re-renders

---

## Files to Create

```
frontend/src/
├── types/
│   └── async-api.ts (new)
├── hooks/
│   └── useAsyncResearch.ts (new)
├── components/
│   └── async/
│       ├── QuerySubmitCard.tsx (new)
│       ├── StatusCard.tsx (new)
│       ├── ResultsCard.tsx (new)
│       └── HistoryPanel.tsx (new)
└── pages/
    └── AsyncResearchPage.tsx (new)
```

---

## Summary

**Design Status:** ✅ Complete

**Implementation Time:** 5-7 hours

**Key Features:**
- Async query submission
- Real-time status polling
- Session history
- Clean, modern UI
- Responsive layout

**API Integration:**
- POST /api/v1/research/query/async
- GET /api/v1/research/status/{id}
- GET /api/v1/research/history

**Next Step:** Start implementation with types and hook

---

**Last Updated:** 2025-11-21
**Ready for Implementation:** ✅ Yes
