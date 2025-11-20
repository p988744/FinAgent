/**
 * Pipeline monitoring types
 * Matches backend models in src/finagent/models/pipeline.py
 */

export type PipelineStage =
  | 'uploading'
  | 'uploaded'
  | 'parsing'
  | 'parsed'
  | 'indexing'
  | 'indexed'
  | 'extracting_metadata'
  | 'metadata_extracted'
  | 'updating_wiki'
  | 'wiki_updated'
  | 'complete'
  | 'failed';

export type PipelineStatus = 'pending' | 'in_progress' | 'success' | 'failed' | 'skipped';

export interface PipelineStageInfo {
  stage: PipelineStage;
  status: PipelineStatus;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  details?: Record<string, any>;
  error_message?: string;
}

export interface PipelineStatusResponse {
  doc_id: string;
  filename: string;
  current_stage: PipelineStage;
  overall_status: PipelineStatus;
  progress_percentage: number;
  total_duration_seconds?: number;
  stages: PipelineStageInfo[];
  started_at?: string;
  completed_at?: string;
}

export interface PipelineStatsResponse {
  total_documents: number;
  by_status: Record<string, number>;
  by_stage: Record<string, number>;
  avg_duration_seconds?: number;
  failed_documents: Array<{
    doc_id: string;
    filename: string;
    failed_stage: string;
    error?: string;
  }>;
}

// Stage display configuration
export const STAGE_CONFIG: Record<
  PipelineStage,
  {
    label: string;
    icon: string;
    description: string;
  }
> = {
  uploading: {
    label: '上傳中',
    icon: '📤',
    description: '正在上傳文件...',
  },
  uploaded: {
    label: '已上傳',
    icon: '✅',
    description: '文件已成功上傳',
  },
  parsing: {
    label: '解析中',
    icon: '📝',
    description: '正在解析文件內容...',
  },
  parsed: {
    label: '已解析',
    icon: '✅',
    description: '文件內容已成功解析',
  },
  indexing: {
    label: '索引中',
    icon: '🔍',
    description: '正在建立向量索引...',
  },
  indexed: {
    label: '已索引',
    icon: '✅',
    description: '向量索引已建立',
  },
  extracting_metadata: {
    label: '提取中',
    icon: '🧠',
    description: '正在提取文件元數據...',
  },
  metadata_extracted: {
    label: '已提取',
    icon: '✅',
    description: '元數據已提取',
  },
  updating_wiki: {
    label: '更新中',
    icon: '📚',
    description: '正在更新知識庫...',
  },
  wiki_updated: {
    label: '已更新',
    icon: '✅',
    description: '知識庫已更新',
  },
  complete: {
    label: '完成',
    icon: '🎉',
    description: '所有處理已完成',
  },
  failed: {
    label: '失敗',
    icon: '❌',
    description: '處理失敗',
  },
};

// Status display configuration
export const STATUS_CONFIG: Record<
  PipelineStatus,
  {
    label: string;
    color: string;
    bgColor: string;
  }
> = {
  pending: {
    label: '待處理',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
  in_progress: {
    label: '處理中',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  success: {
    label: '成功',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  failed: {
    label: '失敗',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  skipped: {
    label: '跳過',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
  },
};
