import { useState, useEffect, useCallback } from 'react'
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

  // Modal states
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentResponse | null>(null)
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [content, setContent] = useState<DocumentContent | null>(null)
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  const [isUploadingVersion, setIsUploadingVersion] = useState(false)

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

  const handleUpload = async (file: File) => {
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '上傳失敗')
      }

      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess(`文件 "${file.name}" 上傳成功`)
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

  const handleUploadNewVersion = async (file: File) => {
    if (!selectedDocument) return

    setIsUploadingVersion(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API_BASE}/${selectedDocument.id}/versions`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || '上傳新版本失敗')
      }

      // Refresh versions
      const versionsRes = await fetch(
        `${API_BASE}/${selectedDocument.id}/versions`
      )
      if (versionsRes.ok) {
        const data = await versionsRes.json()
        setVersions(data)
      }

      await Promise.all([fetchDocuments(), fetchIndexStatus()])
      showSuccess('新版本上傳成功')
    } catch (err) {
      showError(err instanceof Error ? err.message : '上傳新版本失敗')
      throw err
    } finally {
      setIsUploadingVersion(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">文件管理</h1>
        <p className="mt-1 text-sm text-gray-500">
          上傳、版本控制和索引法律文件
        </p>
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
            <DocumentUpload onUpload={handleUpload} isUploading={isUploading} />
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
          onClose={() => setShowVersionModal(false)}
          onUploadNewVersion={handleUploadNewVersion}
          isUploading={isUploadingVersion}
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
