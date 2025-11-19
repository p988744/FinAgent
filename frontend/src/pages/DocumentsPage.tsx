import { useState, useEffect, useCallback } from 'react'
import { RefreshCw } from 'lucide-react'
import { DocumentUpload } from '../components/documents/DocumentUpload'
import { DocumentList } from '../components/documents/DocumentList'
import { IndexStatusCard } from '../components/documents/IndexStatusCard'
import { VersionHistoryModal } from '../components/documents/VersionHistoryModal'
import { ContentViewerModal } from '../components/documents/ContentViewerModal'
import type {
  DocumentResponse,
  IndexStatus,
  DocumentVersion,
  DocumentContent,
} from '../types/documents'

const API_BASE = '/api/v1/documents'

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isReindexing, setIsReindexing] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [processingCount, setProcessingCount] = useState(0)

  // Modal states
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null)
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [content, setContent] = useState<DocumentContent | null>(null)
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  const [isUploadingVersion, setIsUploadingVersion] = useState(false)

  // Duplicate detection state
  const [duplicateMode, setDuplicateMode] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [duplicateInfo, setDuplicateInfo] = useState<any>(null)

  // Notification states
  const [notification, setNotification] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  const showSuccess = (message: string) => {
    setNotification({ type: 'success', message })
    setTimeout(() => setNotification(null), 3000)
  }

  const showError = (message: string) => {
    setNotification({ type: 'error', message })
    setTimeout(() => setNotification(null), 5000)
  }

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(API_BASE)
      if (!res.ok) throw new Error('Failed to fetch documents')
      const data = await res.json()
      setDocuments(data)
      setLastRefresh(new Date())

      // Count documents in processing states
      const processing = data.filter((doc: DocumentResponse) =>
        doc.pipeline_status === 'in_progress' ||
        doc.metadata_extraction_status === 'processing'
      ).length
      setProcessingCount(processing)
    } catch (err) {
      showError('無法載入文件列表')
      console.error(err)
    }
  }, [])

  const fetchIndexStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/status`)
      if (!res.ok) throw new Error('Failed to fetch status')
      const data = await res.json()
      setIndexStatus(data)
    } catch (err) {
      console.error('Failed to fetch index status:', err)
    }
  }, [])

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      setIsLoading(false)
    }
    loadData()
  }, [fetchDocuments, fetchIndexStatus])

  // Smart interval polling - faster when documents are processing
  useEffect(() => {
    if (!isPollingEnabled) return

    // Poll every 2s when processing, 10s when idle
    const interval = processingCount > 0 ? 2000 : 10000

    const timer = setInterval(() => {
      fetchDocuments()
      fetchIndexStatus()
    }, interval)

    return () => clearInterval(timer)
  }, [isPollingEnabled, processingCount, fetchDocuments, fetchIndexStatus])

  // Manual refresh handler
  const handleManualRefresh = useCallback(async () => {
    setIsRefreshing(true)
    setIsPollingEnabled(false) // Pause auto-polling during manual refresh
    try {
      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess('文件列表已更新')
    } catch (err) {
      showError('刷新失敗')
    } finally {
      setIsRefreshing(false)
      // Resume auto-polling after 2 seconds
      setTimeout(() => setIsPollingEnabled(true), 2000)
    }
  }, [fetchDocuments, fetchIndexStatus])

  const handleUpload = async (files: File[]) => {
    // DocumentUpload component now handles uploads internally via polling
    // and calls this callback with an empty array to trigger refresh
    if (files.length === 0) {
      // Just refresh the document list
      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      return
    }

    // Legacy batch upload support (if needed in future)
    setIsUploading(true)
    try {
      const formData = new FormData()
      files.forEach((file) => {
        formData.append('files', file)
      })

      const res = await fetch(`${API_BASE}/upload-batch?auto_index=true&extract_metadata=true`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '上傳失敗')
      }

      const result = await res.json()
      await Promise.all([fetchDocuments(), fetchIndexStatus()])

      if (result.successful > 0) {
        showSuccess(
          `成功上傳 ${result.successful} 個文件${
            result.failed > 0 ? `，${result.failed} 個失敗` : ''
          }`
        )
      } else {
        showError('所有文件上傳失敗')
      }
    } catch (err) {
      showError(err instanceof Error ? err.message : '上傳失敗')
      throw err
    } finally {
      setIsUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/${id}`, {
        method: 'DELETE',
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '刪除失敗')
      }

      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess('文件已刪除')
    } catch (err) {
      showError(err instanceof Error ? err.message : '刪除失敗')
    }
  }

  const handleReindex = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/${id}/reindex`, {
        method: 'POST',
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '重新索引失敗')
      }

      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess('文件已重新索引')
    } catch (err) {
      showError(err instanceof Error ? err.message : '重新索引失敗')
    }
  }

  const handleReindexAll = async () => {
    setIsReindexing(true)
    try {
      const res = await fetch(`${API_BASE}/reindex-all`, {
        method: 'POST',
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '批次重新索引失敗')
      }

      const result = await res.json()
      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess(result.message)
    } catch (err) {
      showError(err instanceof Error ? err.message : '批次重新索引失敗')
    } finally {
      setIsReindexing(false)
    }
  }

  const handleViewContent = async (id: string) => {
    setIsLoadingContent(true)
    setShowContentModal(true)
    setContent(null)

    try {
      const res = await fetch(`${API_BASE}/${id}/content`)
      if (!res.ok) throw new Error('Failed to fetch content')
      const data = await res.json()
      setContent(data)
    } catch (err) {
      showError('無法載入文件內容')
      console.error(err)
    } finally {
      setIsLoadingContent(false)
    }
  }

  const handleViewVersions = async (id: string) => {
    const doc = documents.find((d) => d.id === id)
    if (!doc) return

    setSelectedDocument(doc)
    setShowVersionModal(true)

    try {
      const res = await fetch(`${API_BASE}/${id}/versions`)
      if (!res.ok) throw new Error('Failed to fetch versions')
      const data = await res.json()
      setVersions(data)
    } catch (err) {
      showError('無法載入版本歷史')
      console.error(err)
    }
  }

  const handleDuplicateDetected = (file: File, dupInfo: any) => {
    // Find document by filename to show its versions
    const existingDoc = documents.find(d => d.name === file.name)

    if (existingDoc) {
      // Load versions for this document
      fetch(`${API_BASE}/${existingDoc.id}/versions`)
        .then(res => res.json())
        .then(data => {
          setVersions(data)
          setSelectedDocument(existingDoc)
        })
        .catch(err => console.error('Failed to fetch versions:', err))
    }

    // Set duplicate mode state
    setPendingFile(file)
    setDuplicateInfo(dupInfo)
    setDuplicateMode(true)
    setShowVersionModal(true)
  }

  const handleUploadNewVersion = async (file: File, action?: 'version' | 'replace') => {
    setIsUploadingVersion(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('auto_index', 'true')
      formData.append('extract_metadata', 'true')

      // Add duplicate action if provided
      if (action) {
        formData.append('duplicate_action', action)
      }

      const res = await fetch(`${API_BASE}/upload-with-progress`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '上傳失敗')
      }

      const responseData = await res.json()

      // If in duplicate mode, clear the state
      if (duplicateMode) {
        setDuplicateMode(false)
        setPendingFile(null)
        setDuplicateInfo(null)
        setShowVersionModal(false)
      }

      // Refresh document list
      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess('文件上傳成功')
    } catch (err) {
      showError(err instanceof Error ? err.message : '上傳失敗')
      throw err
    } finally {
      setIsUploadingVersion(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">文件管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            上傳、版本控制和索引法律文件
          </p>
        </div>

        {/* Refresh Controls */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center px-3 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-4 w-4 mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? '刷新中...' : '手動刷新'}
            </button>
            <span className="mt-1 text-xs text-gray-500">
              上次更新: {lastRefresh.toLocaleTimeString()}
              {processingCount > 0 && (
                <span className="ml-2 text-blue-600 font-medium">
                  • {processingCount} 處理中
                </span>
              )}
            </span>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={isPollingEnabled}
              onChange={(e) => setIsPollingEnabled(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span>
              自動刷新 ({processingCount > 0 ? '2秒' : '10秒'})
            </span>
          </label>
        </div>
      </div>

      {notification && (
        <div
          className={`p-4 rounded-md ${
            notification.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-700'
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}
        >
          {notification.message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="space-y-6">
            <DocumentUpload
              onUpload={handleUpload}
              isUploading={isUploading}
              onDuplicateDetected={handleDuplicateDetected}
            />
            <IndexStatusCard
              status={indexStatus}
              onReindexAll={handleReindexAll}
              isReindexing={isReindexing}
            />
          </div>
        </div>

        <div className="lg:col-span-2">
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            onReindex={handleReindex}
            onViewContent={handleViewContent}
            onViewVersions={handleViewVersions}
            isLoading={isLoading}
          />
        </div>
      </div>

      {showVersionModal && selectedDocument && (
        <VersionHistoryModal
          documentId={selectedDocument.id}
          documentName={selectedDocument.name}
          versions={versions}
          onClose={() => {
            setShowVersionModal(false)
            setDuplicateMode(false)
            setPendingFile(null)
            setDuplicateInfo(null)
          }}
          onUploadNewVersion={handleUploadNewVersion}
          isUploading={isUploadingVersion}
          duplicateMode={duplicateMode}
          duplicateInfo={duplicateInfo}
          pendingFile={pendingFile}
        />
      )}

      {showContentModal && (
        <ContentViewerModal
          content={content}
          onClose={() => setShowContentModal(false)}
          isLoading={isLoadingContent}
        />
      )}
    </div>
  )
}
