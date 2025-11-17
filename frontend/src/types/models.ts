/**
 * TypeScript types for Model Management API
 */

export interface LLMModel {
  id: string
  name: string
  description: string
  cost_per_1k_input: number
  cost_per_1k_output: number
  max_tokens: number
  recommended: boolean
  is_active: boolean
}

export interface EmbeddingModel {
  id: string
  name: string
  description: string
  dimensions: number
  cost_per_1k_tokens: number
  recommended: boolean
  is_active: boolean
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  latency_ms: number | null
  model: string | null
}

export interface UsageStats {
  total_tokens: number
  total_cost: number
  queries_count: number
  session_start: string
  current_llm_model: string
  current_embedding_model: string
}

export interface CostEstimate {
  input_tokens: number
  output_tokens: number
  input_cost: number
  output_cost: number
  total_cost: number
  model: string
}

export interface LocalLLMPreset {
  name: string
  base_url: string
  model: string
  api_key: string
  description: string
  recommended: boolean
}
