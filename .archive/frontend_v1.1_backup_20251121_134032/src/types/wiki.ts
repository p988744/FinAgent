/**
 * Wiki API Type Definitions
 *
 * Matches the Pydantic schemas from src/finagent/api/schemas/wiki.py
 */

// ============================================================================
// Category Types
// ============================================================================

export interface CategorySummary {
  id: number
  name: string
  type: 'authority' | 'institution' | 'violation' | 'doc_type'
  document_count: number
  description?: string
  keywords: string[]
}

export interface CategoryDetail extends CategorySummary {
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface CategoryTree {
  type: 'authority' | 'institution' | 'violation' | 'doc_type'
  total_count: number
  categories: CategorySummary[]
}

// ============================================================================
// Document Types
// ============================================================================

export interface DocumentSummary {
  doc_id: string
  filename: string
  document_type?: string
  issuing_authority?: string
  date?: string
  related_institutions: string[]
  violation_types: string[]
  extraction_confidence?: number
}

export interface RelatedDocument {
  doc_id: string
  filename: string
  relationship_type: 'related' | 'temporal' | 'citation'
  strength: number // 0.0-1.0
  reason?: string
}

export interface DocumentDetail {
  doc_id: string
  filename: string
  file_path: string
  document_type?: string
  issuing_authority?: string
  date?: string
  case_number?: string
  related_institutions: string[]
  violation_types: string[]
  penalty_amount?: string
  keywords: string[]
  extraction_confidence?: number
  full_content?: string
  chunk_count: number
  indexed: boolean
  file_size?: number
  created_at: string
  updated_at: string
  related_documents: RelatedDocument[]
}

export interface DocumentList {
  total: number
  offset: number
  limit: number
  documents: DocumentSummary[]
}

// ============================================================================
// Statistics Types
// ============================================================================

export interface DocumentStats {
  total_documents: number
  with_metadata: number
  without_metadata: number
  by_type: Record<string, number>
  by_authority: Record<string, number>
  avg_confidence?: number
}

export interface TimelineDataPoint {
  period: string // e.g., "2020", "2020-01", "2020-01-15"
  count: number
  label?: string
}

export interface TimelineStats {
  granularity: 'year' | 'month' | 'day'
  data: TimelineDataPoint[]
  total_count: number
  date_range: {
    earliest?: string
    latest?: string
  }
}

export interface TopEntity {
  name: string
  count: number
  percentage: number
}

export interface TopEntitiesStats {
  institutions: TopEntity[]
  violations: TopEntity[]
  authorities: TopEntity[]
}

// ============================================================================
// Wiki Overview
// ============================================================================

export interface WikiOverview {
  total_documents: number
  total_categories: number
  categories_by_type: Record<string, number>
  document_stats: DocumentStats
  recent_documents: DocumentSummary[]
  top_entities: TopEntitiesStats
  generated_at?: string
}

// ============================================================================
// Search Types
// ============================================================================

export interface SearchFilters {
  document_type?: string
  authority?: string
  institution?: string
  violation?: string
  date_from?: string
  date_to?: string
  min_confidence?: number
}

export interface SearchResult {
  doc_id: string
  filename: string
  document_type?: string
  relevance_score: number
  snippet?: string
  highlights: string[]
}

export interface SearchResponse {
  query: string
  total_results: number
  offset: number
  limit: number
  results: SearchResult[]
  filters_applied?: SearchFilters
}

// ============================================================================
// Operation Response Types
// ============================================================================

export interface WikiRebuildResponse {
  success: boolean
  rebuild_time_ms: number
  categories_created: number
  documents_categorized: number
  relationships_detected: number
  statistics_updated: boolean
  message: string
}

export interface StatsRefreshResponse {
  success: boolean
  statistics_updated: boolean
  cached_at: string
  message: string
}

export interface ErrorResponse {
  detail: string
  error_type?: string
  error_code?: string
}
