/**
 * Document Management Types
 * TypeScript interfaces for document API
 */

export interface DocumentResponse {
  id: string
  name: string
  file_path: string
  size_bytes: number
  status: 'pending' | 'indexed' | 'error'
  chunk_count: number
  version: number
  created_at: string
  updated_at: string
  description: string | null
  document_type: string | null
}

export interface DocumentVersion {
  version: number
  file_path: string
  size_bytes: number
  created_at: string
}

export interface IndexStatus {
  total_documents: number
  indexed_documents: number
  pending_documents: number
  error_documents: number
  total_chunks: number
  last_indexed_at: string | null
}

export interface ReindexProgress {
  status: string
  total: number
  processed: number
  failed: number
  message: string
}

export interface DocumentContent {
  id: string
  content: string
  size_chars: number
  file_path: string
}
