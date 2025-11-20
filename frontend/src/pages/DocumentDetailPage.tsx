import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  FileText,
  Calendar,
  Building2,
  AlertTriangle,
  DollarSign,
  Hash,
  Tag,
  Link2,
  Loader2,
  AlertCircle,
  Eye,
  EyeOff,
} from 'lucide-react'
import { useState } from 'react'
import type { DocumentDetail } from '../types/wiki'

export function DocumentDetailPage() {
  const { docId } = useParams<{ docId: string }>()
  const navigate = useNavigate()
  const [showContent, setShowContent] = useState(false)

  // Fetch document detail
  const { data: document, isLoading, error } = useQuery<DocumentDetail>({
    queryKey: ['wiki-document', docId, showContent],
    queryFn: async () => {
      if (!docId) throw new Error('Document ID is required')
      const response = await fetch(
        `/api/v1/wiki/document/${docId}?include_content=${showContent}`
      )
      if (!response.ok) {
        throw new Error('Failed to fetch document')
      }
      return response.json()
    },
    enabled: !!docId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">載入文件詳情中...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-red-800">載入失敗</h3>
            <p className="text-sm text-red-700 mt-1">
              {error instanceof Error ? error.message : '未知錯誤'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Back Button */}
      <button
        onClick={() => navigate('/wiki')}
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        返回百科
      </button>

      {/* Header */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <FileText className="h-6 w-6 text-blue-600" />
              {document.document_type && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {document.document_type}
                </span>
              )}
              {document.indexed && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  已索引
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {document.filename}
            </h1>
            <p className="text-sm text-gray-600">
              文件 ID: <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{document.doc_id}</code>
            </p>
          </div>

          {document.extraction_confidence !== undefined && document.extraction_confidence !== null && (
            <div className="text-right">
              <div className="text-sm text-gray-500 mb-1">元數據信心度</div>
              <div className="text-3xl font-bold text-gray-900">
                {(document.extraction_confidence * 100).toFixed(0)}%
              </div>
              <div className="mt-2 w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
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
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Basic Metadata */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">基本資訊</h2>
          <dl className="space-y-3 text-sm">
            {document.issuing_authority && (
              <div className="flex items-start">
                <dt className="flex items-center text-gray-500 w-24 flex-shrink-0">
                  <Building2 className="h-4 w-4 mr-2" />
                  主管機關
                </dt>
                <dd className="text-gray-900 font-medium">{document.issuing_authority}</dd>
              </div>
            )}
            {document.date && (
              <div className="flex items-start">
                <dt className="flex items-center text-gray-500 w-24 flex-shrink-0">
                  <Calendar className="h-4 w-4 mr-2" />
                  日期
                </dt>
                <dd className="text-gray-900 font-medium">{document.date}</dd>
              </div>
            )}
            {document.case_number && (
              <div className="flex items-start">
                <dt className="flex items-center text-gray-500 w-24 flex-shrink-0">
                  <Hash className="h-4 w-4 mr-2" />
                  案號
                </dt>
                <dd className="text-gray-900 font-medium font-mono text-xs">
                  {document.case_number}
                </dd>
              </div>
            )}
            {document.penalty_amount && (
              <div className="flex items-start">
                <dt className="flex items-center text-gray-500 w-24 flex-shrink-0">
                  <DollarSign className="h-4 w-4 mr-2" />
                  裁罰金額
                </dt>
                <dd className="text-gray-900 font-medium">{document.penalty_amount}</dd>
              </div>
            )}
            <div className="flex items-start">
              <dt className="text-gray-500 w-24 flex-shrink-0">索引狀態</dt>
              <dd className="text-gray-900">
                {document.indexed ? (
                  <span className="text-green-600">已索引 ({document.chunk_count} 個片段)</span>
                ) : (
                  <span className="text-gray-500">未索引</span>
                )}
              </dd>
            </div>
            {document.file_size && (
              <div className="flex items-start">
                <dt className="text-gray-500 w-24 flex-shrink-0">檔案大小</dt>
                <dd className="text-gray-900">{(document.file_size / 1024).toFixed(2)} KB</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Related Entities */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">相關實體</h2>
          <div className="space-y-4">
            {/* Institutions */}
            {document.related_institutions.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  金融機構
                </h3>
                <div className="flex flex-wrap gap-2">
                  {document.related_institutions.map((inst, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-md text-sm bg-gray-100 text-gray-800"
                    >
                      {inst}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Violations */}
            {document.violation_types.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 flex items-center">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  違規類型
                </h3>
                <div className="flex flex-wrap gap-2">
                  {document.violation_types.map((violation, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-3 py-1 rounded-md text-sm bg-red-100 text-red-800"
                    >
                      {violation}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Keywords */}
            {document.keywords.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 flex items-center">
                  <Tag className="h-3 w-3 mr-1" />
                  關鍵字
                </h3>
                <div className="flex flex-wrap gap-2">
                  {document.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-50 text-blue-700 border border-blue-200"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Full Content */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">文件內容</h2>
          <button
            onClick={() => setShowContent(!showContent)}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {showContent ? (
              <>
                <EyeOff className="h-4 w-4 mr-2" />
                隱藏內容
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" />
                顯示內容
              </>
            )}
          </button>
        </div>
        <div className="p-4">
          {showContent && document.full_content ? (
            <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono bg-gray-50 p-4 rounded-md overflow-x-auto">
              {document.full_content}
            </pre>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              {showContent ? '載入中...' : '點擊「顯示內容」查看完整文件'}
            </p>
          )}
        </div>
      </div>

      {/* Related Documents */}
      {document.related_documents.length > 0 && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Link2 className="h-5 w-5 mr-2 text-blue-600" />
            相關文件 ({document.related_documents.length})
          </h2>
          <div className="space-y-2">
            {document.related_documents.map((related, idx) => (
              <button
                key={idx}
                onClick={() => navigate(`/wiki/document/${related.doc_id}`)}
                className="w-full text-left p-3 border border-gray-200 rounded-md hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {related.filename}
                    </p>
                    {related.reason && (
                      <p className="text-xs text-gray-600 mt-1">{related.reason}</p>
                    )}
                  </div>
                  <div className="ml-4 text-right flex-shrink-0">
                    <span className="inline-block px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700">
                      {related.relationship_type}
                    </span>
                    <div className="mt-1 text-xs text-gray-500">
                      相似度: {(related.strength * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
          <div>
            <span className="font-medium">建立時間:</span>{' '}
            {new Date(document.created_at).toLocaleString('zh-TW')}
          </div>
          <div>
            <span className="font-medium">更新時間:</span>{' '}
            {new Date(document.updated_at).toLocaleString('zh-TW')}
          </div>
        </div>
      </div>
    </div>
  )
}
