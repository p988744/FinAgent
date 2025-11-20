import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Loader2, AlertCircle, Grid, Search as SearchIcon } from 'lucide-react'
import { CategoryTree } from '../components/wiki/CategoryTree'
import { WikiDocumentList } from '../components/wiki/WikiDocumentList'
import { WikiSearch } from '../components/wiki/WikiSearch'
import type { WikiOverview as WikiOverviewType, CategorySummary } from '../types/wiki'

type ViewMode = 'overview' | 'browse' | 'search'

export function WikiPage() {
  const navigate = useNavigate()
  const [selectedView, setSelectedView] = useState<ViewMode>('overview')
  const [selectedCategory, setSelectedCategory] = useState<CategorySummary | null>(null)

  // Fetch wiki overview data
  const { data: overview, isLoading, error } = useQuery<WikiOverviewType>({
    queryKey: ['wiki-overview'],
    queryFn: async () => {
      const response = await fetch('/api/v1/wiki/overview')
      if (!response.ok) {
        throw new Error('Failed to fetch wiki overview')
      }
      return response.json()
    },
  })

  const handleCategorySelect = (category: CategorySummary) => {
    setSelectedCategory(category)
    setSelectedView('browse')
  }

  const handleDocumentSelect = (docId: string) => {
    navigate(`/wiki/document/${docId}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">載入 Wiki 資料中...</p>
        </div>
      </div>
    )
  }

  if (error) {
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
      {/* Header */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BookOpen className="h-6 w-6 text-blue-600 mr-2" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">文件百科</h1>
              <p className="mt-1 text-xs text-gray-600">
                瀏覽和搜尋所有法律文件、裁罰案例和判決書
              </p>
            </div>
          </div>
          {overview && (
            <div className="text-right">
              <p className="text-2xl font-bold text-blue-600">
                {overview.total_documents}
              </p>
              <p className="text-xs text-gray-500">總文件數</p>
            </div>
          )}
        </div>
      </div>

      {/* View Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setSelectedView('overview')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                selectedView === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <Grid className="h-4 w-4 mr-2" />
                總覽
              </div>
            </button>
            <button
              onClick={() => setSelectedView('browse')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                selectedView === 'browse'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <BookOpen className="h-4 w-4 mr-2" />
                分類瀏覽
              </div>
            </button>
            <button
              onClick={() => setSelectedView('search')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                selectedView === 'search'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center">
                <SearchIcon className="h-4 w-4 mr-2" />
                搜尋
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Overview View */}
      {selectedView === 'overview' && overview && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    文件總數
                  </p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">
                    {overview.total_documents}
                  </p>
                </div>
                <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <BookOpen className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    分類總數
                  </p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">
                    {overview.total_categories}
                  </p>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    已建立元數據
                  </p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">
                    {overview.document_stats.with_metadata}
                  </p>
                </div>
                <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    平均信心度
                  </p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">
                    {overview.document_stats.avg_confidence
                      ? `${(overview.document_stats.avg_confidence * 100).toFixed(0)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div className="h-12 w-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Top Entities */}
          {overview.top_entities && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Top Institutions */}
              <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  熱門金融機構
                </h3>
                <div className="space-y-2">
                  {overview.top_entities.institutions.slice(0, 5).map((entity, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 truncate flex-1 mr-2">{entity.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-900 font-medium">{entity.count}</span>
                        <span className="text-xs text-gray-500">({entity.percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Violations */}
              <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  常見違規類型
                </h3>
                <div className="space-y-2">
                  {overview.top_entities.violations.slice(0, 5).map((entity, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 truncate flex-1 mr-2">{entity.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-900 font-medium">{entity.count}</span>
                        <span className="text-xs text-gray-500">({entity.percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Authorities */}
              <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  主管機關
                </h3>
                <div className="space-y-2">
                  {overview.top_entities.authorities.slice(0, 5).map((entity, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 truncate flex-1 mr-2">{entity.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-900 font-medium">{entity.count}</span>
                        <span className="text-xs text-gray-500">({entity.percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recent Documents */}
          {overview.recent_documents && overview.recent_documents.length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">最近文件</h2>
              <div className="space-y-2">
                {overview.recent_documents.map((doc) => (
                  <button
                    key={doc.doc_id}
                    onClick={() => handleDocumentSelect(doc.doc_id)}
                    className="w-full border border-gray-200 rounded-md p-3 hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
                  >
                    <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                    <div className="mt-1 flex items-center space-x-3 text-xs text-gray-500">
                      {doc.document_type && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                          {doc.document_type}
                        </span>
                      )}
                      {doc.issuing_authority && <span>{doc.issuing_authority}</span>}
                      {doc.date && <span>{doc.date}</span>}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Browse View */}
      {selectedView === 'browse' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-1">
            <CategoryTree
              onCategorySelect={handleCategorySelect}
              selectedCategoryId={selectedCategory?.id}
            />
          </div>
          <div className="lg:col-span-3">
            <WikiDocumentList
              selectedCategory={selectedCategory}
              onDocumentSelect={handleDocumentSelect}
            />
          </div>
        </div>
      )}

      {/* Search View */}
      {selectedView === 'search' && (
        <WikiSearch onDocumentSelect={handleDocumentSelect} />
      )}
    </div>
  )
}
