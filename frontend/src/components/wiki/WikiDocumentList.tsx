import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileText, ChevronLeft, ChevronRight, Loader2, AlertCircle, Calendar, Building2 } from 'lucide-react'
import type { DocumentList, DocumentSummary, CategorySummary } from '../../types/wiki'

interface WikiDocumentListProps {
  selectedCategory?: CategorySummary | null
  onDocumentSelect?: (docId: string) => void
}

export function WikiDocumentList({ selectedCategory, onDocumentSelect }: WikiDocumentListProps) {
  const [currentPage, setCurrentPage] = useState(0)
  const pageSize = 20

  // Fetch documents
  const { data, isLoading, error } = useQuery<DocumentList>({
    queryKey: ['wiki-documents', selectedCategory?.id, currentPage],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: (currentPage * pageSize).toString(),
      })

      if (selectedCategory) {
        params.append('category_id', selectedCategory.id.toString())
      }

      const response = await fetch(`/api/v1/wiki/documents?${params}`)
      if (!response.ok) {
        throw new Error('Failed to fetch documents')
      }
      return response.json()
    },
  })

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  const handlePrevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1)
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
          <span className="text-gray-600">載入文件中...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex items-center text-red-600">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>載入文件失敗：{error instanceof Error ? error.message : '未知錯誤'}</span>
        </div>
      </div>
    )
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
        <div className="text-center text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-3 text-gray-400" />
          <p className="text-sm">
            {selectedCategory ? `${selectedCategory.name} 分類下沒有文件` : '沒有找到文件'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {selectedCategory ? selectedCategory.name : '所有文件'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              共 {data.total} 份文件
            </p>
          </div>
          {selectedCategory && selectedCategory.description && (
            <div className="text-xs text-gray-500 max-w-md text-right">
              {selectedCategory.description}
            </div>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="divide-y divide-gray-200">
        {data.documents.map((doc) => (
          <DocumentListItem
            key={doc.doc_id}
            document={doc}
            onClick={() => onDocumentSelect?.(doc.doc_id)}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            顯示 {data.offset + 1} - {Math.min(data.offset + data.limit, data.total)} / 共 {data.total} 份
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrevPage}
              disabled={currentPage === 0}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              上一頁
            </button>
            <span className="text-sm text-gray-600">
              第 {currentPage + 1} / {totalPages} 頁
            </span>
            <button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages - 1}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一頁
              <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

interface DocumentListItemProps {
  document: DocumentSummary
  onClick: () => void
}

function DocumentListItem({ document, onClick }: DocumentListItemProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 hover:bg-blue-50 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Filename */}
          <h3 className="text-sm font-medium text-gray-900 mb-2">
            {document.filename}
          </h3>

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600 mb-2">
            {document.document_type && (
              <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium">
                {document.document_type}
              </span>
            )}
            {document.issuing_authority && (
              <span className="inline-flex items-center">
                <Building2 className="h-3 w-3 mr-1" />
                {document.issuing_authority}
              </span>
            )}
            {document.date && (
              <span className="inline-flex items-center">
                <Calendar className="h-3 w-3 mr-1" />
                {document.date}
              </span>
            )}
          </div>

          {/* Institutions */}
          {document.related_institutions.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {document.related_institutions.map((inst, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {inst}
                </span>
              ))}
            </div>
          )}

          {/* Violations */}
          {document.violation_types.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {document.violation_types.map((violation, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded"
                >
                  {violation}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Confidence Score */}
        {document.extraction_confidence !== undefined && document.extraction_confidence !== null && (
          <div className="ml-4 text-right flex-shrink-0">
            <div className="text-xs text-gray-500 mb-1">信心度</div>
            <div className="text-sm font-semibold text-gray-900">
              {(document.extraction_confidence * 100).toFixed(0)}%
            </div>
            <div className="mt-1 w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  document.extraction_confidence >= 0.8
                    ? 'bg-green-500'
                    : document.extraction_confidence >= 0.5
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${document.extraction_confidence * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </button>
  )
}
