/**
 * TypeScript types for Configuration Management API
 */

export interface SettingResponse {
  key: string
  value: string
  category: string
  description: string | null
}

export interface SettingUpdate {
  value: string
  description?: string
}

export interface PresetResponse {
  id: number
  name: string
  config_type: 'llm' | 'embedding'
  model: string
  api_key: string // Masked for security
  base_url: string
  temperature: number | null
  is_active: boolean
  created_at: string
}

export interface PresetCreate {
  name: string
  config_type: 'llm' | 'embedding'
  api_key?: string
  base_url?: string
  model: string
  temperature?: number
  set_active?: boolean
}

export interface ModelChoices {
  openai_chat_models: ModelInfo[]
  openai_embedding_models: ModelInfo[]
  local_llm_presets: LocalLLMPreset[]
  temperature_presets: TemperaturePreset[]
}

export interface ModelInfo {
  name: string
  description: string
  max_tokens?: number
  cost_per_1m_input?: number
  cost_per_1m_output?: number
}

export interface LocalLLMPreset {
  name: string
  base_url: string
  model: string
  description: string
}

export interface TemperaturePreset {
  name: string
  value: number
  description: string
}

export type SettingCategory = 'llm' | 'embedding' | 'vector_db' | 'general'
