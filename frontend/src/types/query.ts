// Query WebSocket message types

export type StepStatus = 'pending' | 'active' | 'done' | 'error'

export interface StepUpdate {
  step: 'planning' | 'action' | 'validation' | 'answer'
  status: StepStatus
  description: string
  elapsed_ms: number
}

export interface TodoItem {
  id: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  priority?: number
  progress?: number
  message?: string
  error?: string
}

export interface TodoUpdate {
  todos: TodoItem[]
  total_count: number
  completed_count: number
  progress_percentage: number
}

export interface ActivityLogEntry {
  id: string
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
}

export interface Citation {
  id: number
  source: string
  authority: string
  citation_type: string
  date?: string
  relevance?: number
}

export interface QueryResult {
  summary: string
  key_findings: string[]
  detailed_analysis: string
  confidence: string
  processing_time_ms: number
  citations: Citation[]
}

// Research Plan types
export interface QueryAnalysis {
  keywords: string[]
  must_have_keywords: string[]
  entity_type: string
  jurisdiction: string | null
  time_period: string | null
  query_type: string
  complexity: 'simple' | 'medium' | 'complex'
}

export interface PlanTask {
  id: number
  task: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  search_method: 'vector_search' | 'hard_search' | 'hybrid'
  estimated_time: number | null
}

export interface ResearchPlan {
  analysis: QueryAnalysis
  tasks: PlanTask[]
  max_results: number
  use_hard_search: boolean
  estimated_total_time: number
}

export type WSMessageType =
  | 'query_started'
  | 'step_update'
  | 'plan_created'
  | 'todo_update'
  | 'todo_item_update'
  | 'activity_log'
  | 'citations_update'
  | 'query_complete'
  | 'query_failed'
  | 'error'
  | 'pong'

export interface WSMessage {
  type: WSMessageType
  timestamp: string
  payload: unknown
}

// Query state
export interface QueryState {
  isQuerying: boolean
  currentStep: StepUpdate | null
  steps: Map<string, StepUpdate>
  todos: TodoItem[]
  activityLog: ActivityLogEntry[]
  result: QueryResult | null
  error: string | null
}
