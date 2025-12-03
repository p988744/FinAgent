/**
 * TypeScript types for FinAgent Async Research API
 *
 * API Endpoints:
 * - POST /api/v1/research/query/async
 * - GET /api/v1/research/status/{session_id}
 * - GET /api/v1/research/history
 */

export interface AsyncQueryRequest {
  query_text: string;
}

export interface AsyncQueryResponse {
  session_id: string;
  celery_task_id: string;
  status: string;
  message: string;
}

export type SessionStatusType = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface AgentStep {
  agent: string;
  status: string;
  started_at?: string;
  completed_at?: string;
}

export interface TodoItem {
  id: number;
  description: string;
  status: string;
}

export interface ActivityLogItem {
  timestamp: string;
  message: string;
  level: string;
}

export interface Citation {
  source: string;
  content: string;
  relevance?: number;
}

export interface SessionResult {
  response: string;
  citations?: Citation[];
  metadata?: {
    total_tokens?: number;
    llm_cost_usd?: number;
  };
}

export interface SessionStatus {
  session_id: string;
  query_text: string;
  status: SessionStatusType;
  current_agent?: string;
  agent_steps?: AgentStep[];
  todos?: TodoItem[];
  activity_log?: ActivityLogItem[];
  research_plan?: any;
  dynamic_plan?: any;
  tool_executions?: any;
  result?: SessionResult;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  processing_time_seconds?: number;
}

export interface Session {
  session_id: string;
  query_text: string;
  status: string;
  celery_task_id: string;
  started_at: string;
  completed_at?: string;
  processing_time_seconds?: number;
  is_bookmarked: boolean;
  created_at: string;
}

export interface HistoryResponse {
  sessions: Session[];
  total: number;
}

export interface QueryResult {
  response: string;
  citations?: Citation[];
  processing_time: number;
  metadata?: {
    total_tokens?: number;
    llm_cost_usd?: number;
  };
}
