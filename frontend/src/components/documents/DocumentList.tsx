import { useState } from 'react'
import { File, Trash2, RefreshCw, Clock, CheckCircle, AlertCircle, Activity } from 'lucide-react'
import type { DocumentResponse } from '../../types/documents'
import PipelineModal from './PipelineModal'

interface DocumentListProps {
  documents: DocumentResponse[]
  onDelete: (id: string) => Promise<void>
  onReindex: (id: string) => Promise<void>
  onViewContent: (id: string) => void
  onViewVersions: (id: string) => void
  isLoading: boolean
}

export function DocumentList({
  documents,
  onDelete,
  onReindex,
  onViewContent,
  onViewVersions,
  isLoading,
}: DocumentListProps) {
  const [pipelineModalOpen, setPipelineModalOpen] = useState(false)
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [selectedDocName, setSelectedDocName] = useState<string>('')
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-TW')
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'indexed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            已索引
          </span>
        )
      case 'pending':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="h-3 w-3 mr-1" />
            待索引
          </span>
        )
      case 'error':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
            <AlertCircle className="h-3 w-3 mr-1" />
            錯誤
          </span>
        )
      default:
        return null
    }
  }

  const getPipelineStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      'uploaded': '文件已上傳',
      'parsing': '文件解析中',
      'parsed': '文件解析完成',
      'indexing': '文件索引中',
      'indexed': '文件索引完成',
      'extracting_metadata': '生成元數據中',
      'metadata_extracted': '元數據生成完成',
      'updating_wiki': '更新Wiki中',
      'complete': '處理完成',
      'failed': '處理失敗',
    }
    return labels[stage] || stage
  }

  const getPipelineProgress = (doc: DocumentResponse): { progress: number; label: string; isProcessing: boolean } => {
    const stage = doc.pipeline_stage || 'unknown'
    const status = doc.pipeline_status || 'unknown'

    // Calculate progress based on stage
    const stageProgress: Record<string, number> = {
      'uploaded': 20,
      'parsing': 30,
      'parsed': 40,
      'indexing': 50,
      'indexed': 70,
      'extracting_metadata': 80,
      'metadata_extracted': 90,
      'updating_wiki': 95,
      'complete': 100,
    }

    const progress = stageProgress[stage] || 0
    const label = getPipelineStageLabel(stage)
    const isProcessing = status === 'in_progress' || ['parsing', 'indexing', 'extracting_metadata', 'updating_wiki'].includes(stage)

    return { progress, label, isProcessing }
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-8 text-center text-gray-500">
        載入文件列表中...
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-8 text-center text-gray-500">
        尚無文件。請上傳文件開始使用。
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <File className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">最近上傳</h3>
          </div>
          <span className="text-sm text-gray-500">{documents.length} 個文件</span>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {documents.map((doc) => {
          const pipeline = getPipelineProgress(doc)

          return (
            <div key={doc.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0 mr-4">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {doc.name}
                    </h4>
                    {getStatusBadge(doc.status)}
                    <span className="text-xs text-gray-500">v{doc.version}</span>
                  </div>

                  <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                    <span>{formatSize(doc.size_bytes)}</span>
                    <span>{doc.chunk_count} 個區塊</span>
                    <span>更新於 {formatDate(doc.updated_at)}</span>
                  </div>

                  {doc.description && (
                    <p className="mt-1 text-xs text-gray-600">{doc.description}</p>
                  )}

                  {/* Pipeline Progress Bar */}
                  {doc.pipeline_stage && doc.pipeline_stage !== 'complete' && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-medium ${pipeline.isProcessing ? 'text-blue-600' : 'text-gray-600'}`}>
                          {pipeline.label}
                        </span>
                        <span className="text-xs text-gray-500">{pipeline.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-300 ${
                            pipeline.isProcessing ? 'bg-blue-600 animate-pulse' : 'bg-green-600'
                          }`}
                          style={{ width: `${pipeline.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setSelectedDocId(doc.id)
                      setSelectedDocName(doc.name)
                      setPipelineModalOpen(true)
                    }}
                    className="text-gray-400 hover:text-purple-600"
                    title="查看處理流程詳情"
                  >
                    <Activity className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => onViewContent(doc.id)}
                    className="text-gray-400 hover:text-blue-600"
                    title="查看內容"
                  >
                    <File className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => onViewVersions(doc.id)}
                    className="text-gray-400 hover:text-blue-600"
                    title="版本歷史"
                  >
                    <Clock className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => onReindex(doc.id)}
                    className="text-gray-400 hover:text-green-600"
                    title="重新索引"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => {
                      if (confirm(`確定要刪除文件 "${doc.name}"?`)) {
                        onDelete(doc.id)
                      }
                    }}
                    className="text-gray-400 hover:text-red-600"
                    title="刪除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Pipeline Modal */}
      <PipelineModal
        docId={selectedDocId}
        filename={selectedDocName}
        isOpen={pipelineModalOpen}
        onClose={() => {
          setPipelineModalOpen(false)
          setSelectedDocId(null)
          setSelectedDocName('')
        }}
      />
    </div>
  )
}
