/**
 * FinAgent v2.0 - Type Definitions
 * Chat-based interface with Deep Agent integration
 */

// ============================================
// Message Types
// ============================================

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'sending' | 'thinking' | 'complete' | 'error';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  timestamp: Date;
  thinking?: ThinkingState;
  citations?: Citation[];
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  processingTime?: number;
  totalTokens?: number;
  llmCostUsd?: number;
  model?: string;
  workflow?: 'plan-execute' | 'deep-agent' | 'legacy';
}

// ============================================
// Thinking/Planning Types
// ============================================

export type ThinkingStepStatus = 'pending' | 'active' | 'complete' | 'error';

export interface ThinkingStep {
  id: string;
  description: string;
  status: ThinkingStepStatus;
  result?: string;
  startedAt?: Date;
  completedAt?: Date;
  substeps?: ThinkingSubstep[];
}

export interface ThinkingSubstep {
  id: string;
  description: string;
  status: ThinkingStepStatus;
}

export interface ThinkingState {
  isThinking: boolean;
  currentStep?: string;
  steps: ThinkingStep[];
  logs: ThinkingLog[];
  // Graph/Agent State for debugging
  graphState?: GraphState;
  // Full step history with all transitions
  stepHistory?: StepHistoryEntry[];
}

// Graph State for visualizing agent execution
export interface GraphState {
  input?: string;
  plan?: {
    goal?: string;
    tasks?: Array<{
      id?: number;
      description: string;
      tool?: string;
      args?: Record<string, any>;
      status?: string;
      result?: string;
    }>;
  };
  past_steps?: Array<[Record<string, any>, string]>;
  response?: string;
  current_node?: string;
}

export interface ThinkingLog {
  timestamp: Date;
  level: 'info' | 'debug' | 'warn' | 'error';
  message: string;
  agent?: string;
}

// ============================================
// Citation Types
// ============================================

export interface Citation {
  id: string;
  number: number;
  source: string;
  content: string;
  relevance?: number;
  metadata?: CitationMetadata;
}

export interface CitationMetadata {
  docId?: string;
  filename?: string;
  date?: string;
  institution?: string;
  pageNumber?: number;
}

// ============================================
// Research Session Types
// ============================================

export type SessionStatus = 'idle' | 'pending' | 'in_progress' | 'completed' | 'failed';

export interface ResearchSession {
  id: string;
  query: string;
  status: SessionStatus;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  metadata?: SessionMetadata;
}

export interface SessionMetadata {
  celeryTaskId?: string;
  totalTokens?: number;
  totalCostUsd?: number;
  processingTime?: number;
  workflowType?: string;
}

// ============================================
// API Request/Response Types
// ============================================

export interface AsyncQueryRequest {
  query_text: string;
  use_deep_agent?: boolean;
}

export interface AsyncQueryResponse {
  session_id: string;
  celery_task_id: string;
  status: string;
  message: string;
}

export interface StepHistoryEntry {
  step: string;
  status: string;
  timestamp: string;
  sequence: number;
  data?: {
    description?: string;
    [key: string]: any;
  };
}

export interface SessionStatusResponse {
  session_id: string;
  query_text: string;
  status: SessionStatus;
  current_agent?: string;
  agent_steps?: AgentStep[];
  step_history?: StepHistoryEntry[];
  todos?: TodoItem[];
  activity_log?: ActivityLogItem[];
  research_plan?: ResearchPlan;
  dynamic_plan?: DynamicPlan;
  tool_executions?: Record<string, any>;
  result?: SessionResult;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  processing_time_seconds?: number;
}

export interface AgentStep {
  // Backend sends 'step' field (e.g., 'query_analyzer', 'planner')
  step?: string;
  // Legacy field - may be undefined
  agent?: string;
  status: string;
  timestamp?: string;
  started_at?: string;
  completed_at?: string;
  // Additional data from backend
  data?: {
    description?: string;
    [key: string]: any;
  };
}

export interface TodoItem {
  id: number;
  description: string;
  status: 'pending' | 'in_progress' | 'complete';
}

export interface ActivityLogItem {
  timestamp: string;
  message: string;
  level: string;
}

export interface ResearchPlan {
  tasks: PlanTask[];
  goal?: string;
}

export interface PlanTask {
  task_number: number;
  description: string;
  status: 'pending' | 'in_progress' | 'complete' | 'error';
  result?: string;
}

export interface DynamicPlan {
  current_task?: number;
  total_tasks?: number;
  completed_tasks?: number;
}

export interface SessionResult {
  // Legacy field (may or may not be present)
  response?: string;
  // New fields from research_workflow.py
  executive_summary?: string;
  key_findings?: string[];
  detailed_analysis?: string;
  confidence?: {
    level: 'HIGH' | 'MEDIUM' | 'LOW';
    justification?: string;
  };
  citations?: Array<{
    source: string;
    page?: number;
    excerpt?: string;
    content?: string;
    relevance?: number;
    authority_level?: string;
    citation_type?: string;
  }>;
  processing_time_ms?: number;
  tokens_used?: number;
  cost_usd?: number;
  metadata?: {
    total_tokens?: number;
    llm_cost_usd?: number;
  };
}

// ============================================
// History Types
// ============================================

export interface HistorySession {
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
  sessions: HistorySession[];
  total: number;
}

// ============================================
// UI State Types
// ============================================

export interface UIState {
  isSidebarOpen: boolean;
  isThinkingExpanded: boolean;
  activeCitation?: string;
  theme: 'dark' | 'light';
}

// ============================================
// WebSocket Message Types
// ============================================

export type WebSocketEventType =
  | 'connected'
  | 'session_update'
  | 'agent_step'
  | 'thinking_update'
  | 'result'
  | 'error'
  | 'heartbeat';

export interface WebSocketMessage {
  type: WebSocketEventType;
  data?: any;
  timestamp?: string;
}
